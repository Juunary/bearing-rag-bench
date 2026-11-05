"""Answer practical questions with RAG, the whole knowledge bundle, and three ways of combining them.

[EN]
- Role: compare, on questions written by a person independently of the pages, (1) `rag`: the serving pipeline
  (best PDF-corpus retrieval, cite_refuse_v1, top 5 chunks), (2) `bundle`: no retrieval, every page of data/kb
  (12 practical guide pages, about 10k tokens) is the context, (3) `hybrid`: `rag` first and, only when its answer
  is blocked (refusal, missing or invalid citation), `bundle`, (4) `kb_first`: `bundle` when the question matches a
  bundle page (alias match on the question or its English translation, otherwise the best dense match with cosine
  `--kb-dense-min` or more, fixed before the run; the same ConceptMatcher as the concept pages), else `rag`,
  (5) `both`: the 12 pages and the 5 RAG chunks in one context. Same generator (Qwen3-4B, greedy), same prompt,
  same output validation; passages of the bundle are cited as kb_<page id>#0.
- Records per question and mode: answer, blocked, reason, context ids, prompt and completion tokens, generation
  seconds (from the LLM cache when repeated), and for hybrid / kb_first which path produced the answer.
- Blind grading sheet: identical answers to the same question are merged into one item, items are shuffled with a
  fixed seed, and the sheet never shows the mode. Items already in eval/kb/sample.json keep their id; only new answers
  go to sheet_new.md, so a later run with more modes adds items without regrading the old ones.
- Usage: uv run python experiments/run_kb.py [--modes rag,bundle,hybrid,kb_first,both] [--kb-dense-min 0.55]
         [--questions eval/kb/questions2.jsonl --out eval/kb2 --item-prefix M]   (second question set, 24-page bundle)
  Outputs: eval/kb/results.json, eval/kb/sample.json, eval/kb/sheet.md (all items), eval/kb/sheet_new.md (new items).

[KO]
- 역할: 페이지와 독립적으로 사람이 쓴 질문에 대해 (1) `rag`: 서비스 파이프라인(PDF 코퍼스 최고 검색, cite_refuse_v1, 상위 5),
  (2) `bundle`: 검색 없이 data/kb의 페이지 전부(실무 안내 12쪽, 약 1만 토큰)를 컨텍스트로, (3) `hybrid`: `rag`를 먼저 하고 답이
  차단될 때(거절, 인용 없음·잘못된 인용)만 `bundle`, (4) `kb_first`: 질문이 번들 페이지에 매칭되면(질문 또는 영어 번역의 별칭 일치,
  없으면 dense 코사인 `--kb-dense-min` 이상 상위 1, 실행 전에 고정; 개념 페이지와 같은 ConceptMatcher) `bundle`, 아니면 `rag`,
  (5) `both`: 페이지 12쪽과 RAG 청크 5개를 한 컨텍스트에. 생성 모델·프롬프트·출력 검증은 같고, 번들 문단은 kb_<페이지 id>#0으로 인용한다.
- 질문·방식마다 답변, 차단 여부와 사유, 컨텍스트 ID, 프롬프트·생성 토큰, 생성 시간(반복 실행은 캐시), hybrid·kb_first는 어느 경로로
  답했는지 기록한다.
- 블라인드 채점표: 같은 질문의 같은 답변은 한 항목으로 묶고, 고정 시드로 섞으며, 방식은 표시하지 않는다. 이미 sample.json에 있는 항목은
  번호를 유지하고 새 답변만 sheet_new.md에 쓴다(방식을 더해 다시 실행해도 옛 항목을 다시 채점하지 않는다).
- 사용: uv run python experiments/run_kb.py [--modes rag,bundle,hybrid,kb_first,both] [--kb-dense-min 0.55]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache, make_key  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.concepts import ConceptMatcher, load_concepts  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.generation import Generator, build_messages  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever, share_translator_model  # noqa: E402
from ragbench.validation import SAFE_MESSAGES, guess_lang, validate_answer  # noqa: E402

OUT = REPO / "eval" / "kb"
CONFIG = REPO / "configs" / "pdf" / "pdfth_x13_rrf_en_dense_en_rerank_en_text.json"
PROMPT, MODEL, MAX_NEW, SEED = "cite_refuse_v1", "Qwen/Qwen3-4B-Instruct-2507", 256, 20261104
ALL_MODES = ["rag", "bundle", "hybrid", "kb_first", "both"]


def bundle_passages(kb) -> list[dict]:
    # 페이지 하나가 문단 하나: 제목 + 본문. 인용 ID는 kb_<id>#0 (기존 인용 정규식과 호환)
    return [{"chunk_id": f"kb_{c.id}#0", "text": f"{c.title}\n{c.description}"} for c in kb]


def generate_cached(generator, cache, messages) -> dict:
    key = make_key(generator.model_name, generator.revision, messages, MAX_NEW)
    out = cache.get(key)
    if out is None:
        out = generator.generate(messages, max_new_tokens=MAX_NEW)
        cache.put(key, out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", type=Path, default=OUT / "questions.jsonl")
    ap.add_argument("--modes", default=",".join(ALL_MODES))
    ap.add_argument("--kb", type=Path, default=REPO / "data" / "kb")
    ap.add_argument("--kb-dense-min", type=float, default=0.55, help="kb_first: cosine threshold of the dense fallback (fixed before the run)")
    ap.add_argument("--out", type=Path, default=OUT, help="output directory (results.json, sample.json, sheet.md)")
    ap.add_argument("--item-prefix", default="K", help="prefix of the blind sheet item ids")
    args = ap.parse_args()
    out = args.out
    modes = args.modes.split(",")
    questions = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    kb = load_concepts(args.kb)
    passages = bundle_passages(kb)
    cfg = ExperimentConfig.load(CONFIG)
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)
    by_id = {c["chunk_id"]: c for c in chunks}
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    generator = Generator(MODEL, device="cuda:1")
    share_translator_model(retriever, generator)
    cache = LLMCache(REPO / "logs" / "kb_cache.sqlite")
    pipe = RAGPipeline(retriever, chunks, generator, cache, RequestLogger(REPO / "logs" / "kb_requests.jsonl"),
                       prompt_version=PROMPT, context_k=5, max_new_tokens=MAX_NEW, config_id=f"kb:{cfg.exp_id}")
    # kb_first의 매칭기: 페이지 별칭(ko/en/de) + 영어 dense 다리의 임베더(bge-m3)를 그대로 쓴다
    dense_leg = next(r for r in retriever.base.retrievers if "dense" in r.name)
    embedder = dense_leg.inner.embedder
    matcher = ConceptMatcher(kb, embedder=embedder, dense_top=1, dense_min=args.kb_dense_min)
    matcher.index()

    def generate_with(mode: str, q: dict, ctx: list[dict]) -> dict:
        messages = build_messages(PROMPT, q["question"], ctx)
        t0 = time.perf_counter()
        out = generate_cached(generator, cache, messages)
        ids = [p["chunk_id"] for p in ctx]
        v = validate_answer(out["text"], ids)
        lang = guess_lang(q["question"])
        return {"mode": mode, "answer": out["text"] if v.ok else SAFE_MESSAGES.get(lang, SAFE_MESSAGES["en"]), "raw": out["text"],
                "blocked": not v.ok, "reason": v.reason, "context_ids": ids, "prompt_tokens": out["prompt_tokens"],
                "completion_tokens": out["completion_tokens"], "seconds": out.get("seconds", time.perf_counter() - t0)}

    def run_rag(q: dict) -> dict:
        r = pipe.answer(q["question"])
        return {"mode": "rag", "answer": r.answer, "blocked": r.blocked, "reason": r.reason, "context_ids": list(r.context_ids),
                "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens, "seconds": r.timings_ms.get("generate", 0.0) / 1000}

    def match_kb(q: dict) -> dict:
        en = retriever.query_translator.translate(q["question"], "query")["text"] if retriever.query_translator else q["question"]
        qvec = embedder.encode([q["question"]])[0]        # 페이지가 한국어라 질문도 원문으로 임베딩한다
        m = matcher.match(q["question"], en, qvec)
        sims = matcher.page_emb @ qvec
        best = int(sims.argmax())
        return {**m.to_dict(), "dense_best": [kb[best].id, round(float(sims[best]), 4)]}

    rows = []
    for q in questions:
        rec = {"qid": q["qid"], "question": q["question"], "topic": q.get("topic"), "modes": {}}
        rag = run_rag(q) if modes != ["bundle"] else None
        bun = generate_with("bundle", q, passages) if any(m in modes for m in ("bundle", "hybrid", "kb_first")) else None
        if "rag" in modes:
            rec["modes"]["rag"] = rag
        if "bundle" in modes:
            rec["modes"]["bundle"] = bun
        if "hybrid" in modes:
            # RAG가 차단되면 번들로 넘긴다. 토큰은 두 단계를 합산한다 (넘기지 않으면 RAG만)
            if rag["blocked"]:
                rec["modes"]["hybrid"] = {**bun, "mode": "hybrid", "path": "bundle",
                                          "prompt_tokens": (rag["prompt_tokens"] or 0) + (bun["prompt_tokens"] or 0),
                                          "completion_tokens": (rag["completion_tokens"] or 0) + (bun["completion_tokens"] or 0),
                                          "seconds": rag["seconds"] + bun["seconds"]}
            else:
                rec["modes"]["hybrid"] = {**rag, "mode": "hybrid", "path": "rag"}
        if "kb_first" in modes:
            # 번들 페이지에 매칭되면 번들 답, 아니면 RAG 답 (RAG의 거절 여부와 무관). 매칭 비용은 임베딩 1회라 토큰에 넣지 않는다
            mt = match_kb(q)
            src = bun if mt["ids"] else rag
            rec["modes"]["kb_first"] = {**src, "mode": "kb_first", "path": "bundle" if mt["ids"] else "rag", "match": mt}
        if "both" in modes:
            rec["modes"]["both"] = generate_with("both", q, passages + [by_id[i] for i in rag["context_ids"]])
        rows.append(rec)
        print(q["qid"], {m: ("blocked" if r["blocked"] else "ok") + (f"/{r['path']}" if "path" in r else "") for m, r in rec["modes"].items()})

    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for m in modes:
        rs = [r["modes"][m] for r in rows]
        summary[m] = {"n": len(rs), "blocked": sum(r["blocked"] for r in rs),
                      "prompt_tokens_mean": sum(r["prompt_tokens"] or 0 for r in rs) / len(rs),
                      "seconds_mean": sum(r["seconds"] for r in rs) / len(rs),
                      **({"fallback": sum(r["path"] == "bundle" for r in rs)} if m in ("hybrid", "kb_first") else {})}
    result = {"questions": str(args.questions.relative_to(REPO)), "config": CONFIG.name, "prompt_version": PROMPT, "model": MODEL, "kb_pages": len(kb), "kb_verified": sum(c.verified for c in kb),
              "modes": modes, "kb_dense_min": args.kb_dense_min, "summary": summary, "rows": rows}
    (out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))

    # 블라인드 채점표: 같은 질문의 같은 답변 텍스트는 한 항목으로 (방식은 표시하지 않음).
    # 이미 있는 항목(sample.json)은 번호를 유지하고, 새 답변만 뒤 번호로 붙여 sheet_new.md에 쓴다
    old = json.loads((out / "sample.json").read_text(encoding="utf-8"))["items"] if (out / "sample.json").exists() else []
    known = {(it["qid"], it["answer"]): it for it in old}
    new_items = []
    for r in rows:
        by_answer: dict[str, list[str]] = {}
        for m, x in r["modes"].items():
            by_answer.setdefault(x["answer"], []).append(m)
        for ans, ms in by_answer.items():
            if (r["qid"], ans) in known:
                known[(r["qid"], ans)]["modes"] = ms
            else:
                new_items.append({"qid": r["qid"], "question": r["question"], "answer": ans, "modes": ms, "blocked": r["modes"][ms[0]]["blocked"]})
    random.Random(SEED + len(old)).shuffle(new_items)
    for i, it in enumerate(new_items, start=len(old) + 1):
        it["item"] = f"{args.item_prefix}{i:02d}"
    items = old + new_items
    (out / "sample.json").write_text(json.dumps({"seed": SEED, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")

    def sheet(path: Path, its: list[dict], title: str) -> None:
        lines = [f"# {title}", "",
                 "답 형식: `K01 | 정확성: 맞음 | 메모:` (답변한 항목, 맞음/부분/틀림) 또는 `K02 | 거절: 적절 | 메모:` (거절한 항목, 적절/부적절).",
                 "같은 질문에 같은 답변이 나온 경우는 하나로 묶었고, 어떤 방식의 답인지는 표시하지 않았습니다.", ""]
        for it in its:
            lines += [f"**{it['item']}** ({it['qid']}) 질문: {it['question']}", "",
                      ("답변(거절): " if it["blocked"] else "답변: ") + it["answer"], ""]
        path.write_text("\n".join(lines), encoding="utf-8")

    sheet(out / "sheet.md", items, "지식 번들 실험 채점표 (블라인드)")
    sheet(out / "sheet_new.md", new_items, "지식 번들 실험 추가 채점표 (블라인드, 새 답변만)")
    print(f"items: {len(items)} (new {len(new_items)}) -> {out.relative_to(REPO)}/sheet.md, sheet_new.md")


if __name__ == "__main__":
    main()
