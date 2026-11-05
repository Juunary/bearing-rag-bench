"""Direct corpus interaction (DCI): an agent greps the corpus and reads chunks before answering -> eval/dci/.

[EN]
- Role: the questions the serving pipeline refused (cite_refuse_v1 on the best PDF-corpus retrieval) are given to a
  small agent loop with the same generator (Qwen3-4B-Instruct, greedy). Instead of one top-k retrieval step the model
  searches the corpus itself, as in "direct corpus interaction" (arXiv 2605.05242) and the OKF folder mode:
    grep(pattern)   v1: case-insensitive regex over the original text AND the English translation of every chunk
                    (903 chunks, wiki + PDF with table headers); v2: whitespace-separated terms, a passage matches when
                    every term occurs anywhere in it (each term a regex), and a miss reports which terms never occur;
                    up to 10 hits with chunk id, document title, matching line
    read(chunk_id)  the chunk's original text (what RAG gives the generator), plus its English translation when it
                    is not English
    answer(text)    the final answer citing [chunk_id] of chunks it has read, or NO_ANSWER
  One JSON object per step; at most MAX_CALLS tool calls; one correction prompt on malformed output; after the budget
  the model is asked to answer. The answer goes through the same output validation as the pipeline, with the read
  chunks as the allowed citations.
- Questions: eval/human_round2 (5 refused), eval/kb (12 refused, 4 of them outside the bundle topics) and the 3 refused
  PDF questions (gold chunks known, so cites_gold / gold_read are computed automatically).
- Records per question: trajectory (every call and tool result), answer, blocked, reason, calls, chunks read,
  prompt tokens summed over steps, seconds. Writes a blind grading sheet for the answered D/K questions.
- Variants: v1 (regex grep, terse prompt) failed on 17 of 20 questions because the 4B model searched with sentence-long
  patterns ("oil seal.*lip wear.*shaft") that never match; v2 adds the all-terms grep and a prompt that asks for one or
  two key terms per search. Results go to eval/dci/results_<variant>.json; the sheet lists the answered D/K questions.
- Usage: uv run python experiments/run_dci.py --variant v2 [--max-calls 8]

[KO]
- 역할: 서비스 파이프라인(PDF 코퍼스 최고 검색 + cite_refuse_v1)이 거절한 질문을 같은 생성 모델(Qwen3-4B-Instruct, greedy)의
  작은 에이전트 루프에 준다. 상위 k 검색 한 번 대신 모델이 코퍼스를 직접 뒤진다("direct corpus interaction", arXiv 2605.05242;
  OKF 폴더 모드와 같은 계열): grep(정규식, 원문 + 영어 번역문, 일치 청크 10개까지) / read(청크 원문 + 영어 번역) / answer(읽은
  청크를 인용한 답 또는 NO_ANSWER). 단계마다 JSON 하나, 도구 호출 MAX_CALLS회 상한, 형식 오류는 1회 교정, 상한 뒤에는 답변 요구.
  답은 파이프라인과 같은 출력 검증을 거친다(인용 허용 범위 = 읽은 청크).
- 질문: eval/human_round2 거절 5개, eval/kb 거절 12개(주제 밖 4개 포함), PDF 거절 3개(정답 청크가 있어 자동 채점).
- 기록: 궤적(호출·도구 결과 전부), 답변, 차단 여부, 호출 수, 읽은 청크, 단계 합산 프롬프트 토큰, 시간. 답한 D/K 질문의
  블라인드 채점표를 쓴다.
- 변형: v1(정규식 grep, 짧은 지시문)은 4B 모델이 "oil seal.*lip wear.*shaft"처럼 문장 길이 패턴으로 검색해 20개 중 17개에서 아무것도
  읽지 못하고 거절했다. v2는 단어 전부 포함(순서 무관) grep과 "검색어는 핵심 단어 1~2개" 지시를 더한다. 결과는 eval/dci/results_<variant>.json.
- 사용: uv run python experiments/run_dci.py --variant v2 [--max-calls 8]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig, set_seed  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks  # noqa: E402
from ragbench.generation import CITE_RE, NO_ANSWER, Generator  # noqa: E402
from ragbench.ingest import REPO, load_corpus  # noqa: E402
from ragbench.validation import SAFE_MESSAGES, guess_lang, validate_answer  # noqa: E402

OUT = REPO / "eval" / "dci"
MODEL, SEED = "Qwen/Qwen3-4B-Instruct-2507", 20261105
EN_CHUNKS = REPO / "data" / "processed" / "chunks_en_fixed_tok384_ov48_pdf_th.jsonl"
MAX_HITS, SNIPPET, STEP_TOKENS = 10, 160, 320

GREP_HELP = {
    "v1": '  {"tool": "grep", "pattern": "<regex, case-insensitive>"}   -> up to 10 matching passages: id, document, matching line',
    "v2": ('  {"tool": "grep", "pattern": "<one or two key terms>"}      -> up to 10 passages that contain EVERY term (any order, '
           'case-insensitive): id, document, matching line. Use single words or short phrases such as "shaft seal" or "Wellendichtring", '
           'never a whole sentence; combine at most two terms; if nothing matches, the result names the terms that never occur, so try a synonym.'),
}
SYSTEM_TMPL = (
    "You are a technical assistant for bearings and automotive parts. You answer by searching a document collection "
    "yourself. The collection has 903 passages from Wikipedia (Korean, English, German) and from NASA bearing reports and "
    "German theses; every passage also has an English translation that grep searches.\n"
    "Tools (reply with exactly ONE JSON object per turn, nothing else):\n"
    "{grep_help}\n"
    '  {"tool": "read", "chunk_id": "<id>"}                        -> the full passage\n'
    '  {"tool": "answer", "text": "<final answer>"}               -> finish\n'
    "Strategy: the question may use different words than the documents. Grep English technical terms (and German or "
    "Korean synonyms) one at a time; try alternative terms if a search finds nothing; read the most promising passages; "
    "then answer in the language of the question, in at most four sentences, citing after every sentence the id of a "
    "passage you have READ in square brackets, for example [en_grease#2]. If after searching the passages do not contain "
    f"the information, answer with exactly {NO_ANSWER}."
)
EXAMPLE = {"v1": "", "v2": ('\nExample for "Why does a hydraulic pump cavitate?": first {"tool": "grep", "pattern": "cavitation"}, '
                           'then read the best passage, then answer.')}


def system_prompt(variant: str) -> str:
    return SYSTEM_TMPL.replace("{grep_help}", GREP_HELP[variant]) + EXAMPLE[variant]     # 템플릿에 JSON 중괄호가 있어 format은 못 쓴다


def parse_call(text: str) -> dict | None:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) and obj.get("tool") in ("grep", "read", "answer") else None


class Corpus:
    def __init__(self):
        chunks = load_chunks(ChunkingConfig(corpus="wiki_pdf", table_header=True))
        en = {r["chunk_id"]: r for r in map(json.loads, filter(str.strip, EN_CHUNKS.read_text(encoding="utf-8").splitlines()))}
        titles = {d["doc_id"]: d["title"] for d in load_corpus("wiki_pdf")}
        self.rows = [(c["chunk_id"], titles[c["doc_id"]], c["lang"], c["text"], en[c["chunk_id"]]["text"] if en[c["chunk_id"]]["translated"] else None)
                     for c in chunks]
        self.by_id = {r[0]: r for r in self.rows}

    def grep(self, pattern: str, variant: str = "v1") -> str:
        if variant == "v2":
            return self.grep_terms(pattern)
        try:
            rx = re.compile(pattern, re.I)
        except re.error as e:
            return f"invalid regex: {e}"
        hits = []
        for cid, title, lang, text, en in self.rows:
            for body in (text, en or ""):
                m = rx.search(body)
                if m:
                    line = body[max(0, m.start() - SNIPPET // 2): m.end() + SNIPPET // 2].replace("\n", " ")
                    hits.append(f"{cid} | {title} [{lang}] | ...{line}...")
                    break
        if not hits:
            return "no match"
        shown = hits[:MAX_HITS]
        return f"{len(hits)} matching passages" + (f" (showing {MAX_HITS})" if len(hits) > MAX_HITS else "") + ":\n" + "\n".join(shown)

    def grep_terms(self, pattern: str) -> str:
        """v2: every whitespace-separated term must occur somewhere in the passage (original or English), any order."""
        terms = [t for t in re.split(r"\s+", pattern.strip().strip('"')) if t]
        if not terms:
            return "empty pattern"
        try:
            rxs = [re.compile(t, re.I) for t in terms]
        except re.error as e:
            return f"invalid regex: {e}"
        hits, seen = [], [0] * len(terms)
        for cid, title, lang, text, en in self.rows:
            body = text + "\n" + (en or "")
            ms = [rx.search(body) for rx in rxs]
            for i, m in enumerate(ms):
                seen[i] += bool(m)
            if all(ms):
                m = ms[0]
                src = text if m.start() < len(text) else body
                line = src[max(0, m.start() - SNIPPET // 2): m.end() + SNIPPET // 2].replace("\n", " ")
                hits.append(f"{cid} | {title} [{lang}] | ...{line}...")
        if not hits:
            never = [t for t, n in zip(terms, seen) if n == 0]
            return "no passage contains all terms" + (f"; these terms occur nowhere: {', '.join(never)}" if never else "; each term occurs, but not together")
        shown = hits[:MAX_HITS]
        return f"{len(hits)} matching passages" + (f" (showing {MAX_HITS})" if len(hits) > MAX_HITS else "") + ":\n" + "\n".join(shown)

    def read(self, cid: str) -> str | None:
        r = self.by_id.get(cid)
        if r is None:
            return None
        cid, title, lang, text, en = r
        return f"[{cid}] {title} [{lang}]\n{text}" + (f"\n--- English translation ---\n{en}" if en else "")


def run_agent(gen: Generator, corpus: Corpus, question: str, max_calls: int, variant: str = "v1") -> dict:
    messages = [{"role": "system", "content": system_prompt(variant)}, {"role": "user", "content": f"Question: {question}"}]
    traj, read_ids, calls, bad, tokens, t0 = [], [], 0, 0, 0, time.perf_counter()
    final = None
    while True:
        out = gen.generate(messages, max_new_tokens=STEP_TOKENS)
        tokens += out["prompt_tokens"] + out["completion_tokens"]
        call = parse_call(out["text"])
        traj.append({"model": out["text"]})
        if call is None:
            bad += 1
            if bad > 1 or calls >= max_calls:
                final = out["text"]
                break
            messages += [{"role": "assistant", "content": out["text"]},
                         {"role": "user", "content": "Reply with exactly one JSON object: a grep, a read, or an answer."}]
            continue
        if call["tool"] == "answer":
            final = str(call.get("text", ""))
            break
        calls += 1
        if call["tool"] == "grep":
            result = corpus.grep(str(call.get("pattern", "")), variant)
        else:
            cid = str(call.get("chunk_id", "")).strip("[] ")
            result = corpus.read(cid) or f"unknown chunk id {cid!r}; use an id returned by grep"
            if cid in corpus.by_id and cid not in read_ids:
                read_ids.append(cid)
        traj[-1]["tool_result"] = result
        messages += [{"role": "assistant", "content": json.dumps(call, ensure_ascii=False)}, {"role": "user", "content": result}]
        if calls >= max_calls:
            messages.append({"role": "user", "content": f"Tool budget used ({max_calls} calls). Now answer from the passages you read, "
                                                        f"or {NO_ANSWER}: " + '{"tool": "answer", "text": "..."}'})
            out = gen.generate(messages, max_new_tokens=STEP_TOKENS)
            tokens += out["prompt_tokens"] + out["completion_tokens"]
            call = parse_call(out["text"])
            traj.append({"model": out["text"]})
            final = str(call.get("text", "")) if call and call.get("tool") == "answer" else out["text"]
            break
    v = validate_answer(final, read_ids)
    lang = guess_lang(question)
    return {"answer": final if v.ok else SAFE_MESSAGES.get(lang, SAFE_MESSAGES["en"]), "raw": final, "blocked": not v.ok, "reason": v.reason,
            "calls": calls, "read": read_ids, "cited": sorted(set(CITE_RE.findall(final))), "malformed": bad, "tokens": tokens,
            "seconds": time.perf_counter() - t0, "trajectory": traj}


def questions() -> list[dict]:
    qs = []
    for r in json.loads((REPO / "eval" / "human_round2" / "user_questions_answers.json").read_text(encoding="utf-8"))["rows"]:
        if r["blocked"]:
            qs.append({"set": "D", "qid": r["qid"], "question": r["question"], "scope": "in"})
    kb = json.loads((REPO / "eval" / "kb" / "results.json").read_text(encoding="utf-8"))["rows"]
    scope = {json.loads(l)["qid"]: json.loads(l)["scope"] for l in (REPO / "eval" / "kb" / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    for r in kb:
        if r["modes"]["rag"]["blocked"]:
            qs.append({"set": "K", "qid": r["qid"], "question": r["question"], "scope": scope[r["qid"]]})
    pdf = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_pdf.jsonl")}
    gen = json.loads((REPO / "experiments" / "results" / "pdfg_th_x13_rrf_en_dense_en_rerank_en_text_refuse.json").read_text(encoding="utf-8"))
    for q in gen["per_query"]:
        if q["metrics"]["refused"]:
            qs.append({"set": "PDF", "qid": q["qid"], "question": pdf[q["qid"]]["question"], "scope": "in", "gold": q["gold"]})
    return qs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-calls", type=int, default=8)
    ap.add_argument("--variant", default="v1", choices=["v1", "v2"])
    args = ap.parse_args()
    set_seed(42)
    corpus = Corpus()
    gen = Generator(MODEL, device="cuda:1")
    rows = []
    for q in questions():
        r = run_agent(gen, corpus, q["question"], args.max_calls, args.variant)
        if "gold" in q:
            r["gold_read"] = any(g in r["read"] for g in q["gold"])
            r["cites_gold"] = any(g in r["cited"] for g in q["gold"])
        rows.append({**q, **r})
        print(q["set"], q["qid"], "blocked" if r["blocked"] else "answered", f"calls {r['calls']} read {len(r['read'])} tokens {r['tokens']} {r['seconds']:.0f}s",
              r["reason"] or "", r["answer"][:80].replace("\n", " "))
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for s in ("D", "K", "PDF"):
        rs = [r for r in rows if r["set"] == s]
        summary[s] = {"n": len(rs), "answered": sum(not r["blocked"] for r in rs), "calls_mean": sum(r["calls"] for r in rs) / len(rs),
                      "tokens_mean": sum(r["tokens"] for r in rs) / len(rs), "seconds_mean": sum(r["seconds"] for r in rs) / len(rs),
                      "malformed": sum(r["malformed"] for r in rs),
                      **({"cites_gold": sum(r["cites_gold"] for r in rs), "gold_read": sum(r["gold_read"] for r in rs)} if s == "PDF" else {})}
    (OUT / f"results_{args.variant}.json").write_text(json.dumps({"model": MODEL, "variant": args.variant, "max_calls": args.max_calls, "summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    # 블라인드 채점표: 답한 D·K 질문만 (PDF는 정답 청크로 자동 채점)
    items = [{"qid": r["qid"], "question": r["question"], "answer": r["answer"]} for r in rows if r["set"] != "PDF" and not r["blocked"]]
    random.Random(SEED).shuffle(items)
    tag = args.variant.upper()
    for i, it in enumerate(items, start=1):
        it["item"] = f"{tag}{i:02d}"
    (OUT / f"sample_{args.variant}.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# DCI {args.variant} 채점표 (에이전트가 코퍼스를 뒤져 답한 항목)", "", f"답 형식: `{tag}01 | 정확성: 맞음 | 메모:` (맞음/부분/틀림).", ""]
    for it in items:
        lines += [f"**{it['item']}** ({it['qid']}) 질문: {it['question']}", "", "답변: " + it["answer"], ""]
    (OUT / f"sheet_{args.variant}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"items to grade: {len(items)} -> {OUT.relative_to(REPO)}/sheet_{args.variant}.md")


if __name__ == "__main__":
    main()
