"""Answer practical questions three ways: RAG, the whole knowledge bundle in the prompt, and RAG-then-bundle (hybrid).

[EN]
- Role: compare, on questions written by a person independently of the pages, (1) `rag`: the serving pipeline
  (best PDF-corpus retrieval, cite_refuse_v1, top 5 chunks), (2) `bundle`: no retrieval, every page of data/kb
  (12 practical guide pages, about 10k tokens) is the context, (3) `hybrid`: `rag` first and, only when its answer
  is blocked (refusal, missing or invalid citation), `bundle`. Same generator (Qwen3-4B, greedy), same prompt, same
  output validation; passages of the bundle are cited as kb_<page id>#0.
- Records per question and mode: answer, blocked, reason, context ids, prompt and completion tokens, generation
  seconds (from the LLM cache when repeated), and for hybrid which path produced the answer.
- Also writes a blind grading sheet: identical answers to the same question are merged into one item, items are
  shuffled with a fixed seed, and the sheet never shows the mode.
- Usage: uv run python experiments/run_kb.py --questions eval/kb/questions.jsonl [--modes rag,bundle,hybrid]
  Outputs: eval/kb/results.json, eval/kb/sheet.md, eval/kb/sample.json (item -> question/modes map).

[KO]
- 역할: 페이지와 독립적으로 사람이 쓴 질문에 대해 (1) `rag`: 서비스 파이프라인(PDF 코퍼스 최고 검색, cite_refuse_v1, 상위 5),
  (2) `bundle`: 검색 없이 data/kb의 페이지 전부(실무 안내 12쪽, 약 1만 토큰)를 컨텍스트로, (3) `hybrid`: `rag`를 먼저 하고 답이
  차단될 때(거절, 인용 없음·잘못된 인용)만 `bundle`로 답한다. 생성 모델·프롬프트·출력 검증은 같고, 번들 문단은 kb_<페이지 id>#0으로 인용한다.
- 질문·방식마다 답변, 차단 여부와 사유, 컨텍스트 ID, 프롬프트·생성 토큰, 생성 시간(반복 실행은 캐시), hybrid는 어느 경로로 답했는지 기록.
- 블라인드 채점표: 같은 질문의 같은 답변은 한 항목으로 묶고, 고정 시드로 섞으며, 방식은 표시하지 않는다.
- 사용: uv run python experiments/run_kb.py --questions eval/kb/questions.jsonl [--modes rag,bundle,hybrid]
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
from ragbench.concepts import load_concepts  # noqa: E402
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
    ap.add_argument("--modes", default="rag,bundle,hybrid")
    ap.add_argument("--kb", type=Path, default=REPO / "data" / "kb")
    args = ap.parse_args()
    modes = args.modes.split(",")
    questions = [json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip()]
    kb = load_concepts(args.kb)
    passages = bundle_passages(kb)
    cfg = ExperimentConfig.load(CONFIG)
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    generator = Generator(MODEL, device="cuda:1")
    share_translator_model(retriever, generator)
    cache = LLMCache(REPO / "logs" / "kb_cache.sqlite")
    pipe = RAGPipeline(retriever, chunks, generator, cache, RequestLogger(REPO / "logs" / "kb_requests.jsonl"),
                       prompt_version=PROMPT, context_k=5, max_new_tokens=MAX_NEW, config_id=f"kb:{cfg.exp_id}")

    def run_rag(q: dict) -> dict:
        r = pipe.answer(q["question"])
        return {"mode": "rag", "answer": r.answer, "blocked": r.blocked, "reason": r.reason, "context_ids": list(r.context_ids),
                "prompt_tokens": getattr(r, "prompt_tokens", None), "completion_tokens": getattr(r, "completion_tokens", None),
                "seconds": (getattr(r, "timings_ms", {}) or {}).get("generate", 0.0) / 1000}

    def run_bundle(q: dict) -> dict:
        messages = build_messages(PROMPT, q["question"], passages)
        t0 = time.perf_counter()
        out = generate_cached(generator, cache, messages)
        ids = [p["chunk_id"] for p in passages]
        v = validate_answer(out["text"], ids)
        lang = guess_lang(q["question"])
        return {"mode": "bundle", "answer": out["text"] if v.ok else SAFE_MESSAGES.get(lang, SAFE_MESSAGES["en"]), "raw": out["text"],
                "blocked": not v.ok, "reason": v.reason, "context_ids": ids, "prompt_tokens": out["prompt_tokens"],
                "completion_tokens": out["completion_tokens"], "seconds": out.get("seconds", time.perf_counter() - t0)}

    rows = []
    for q in questions:
        rec = {"qid": q["qid"], "question": q["question"], "topic": q.get("topic"), "modes": {}}
        if "rag" in modes or "hybrid" in modes:
            rag = run_rag(q)
        if "rag" in modes:
            rec["modes"]["rag"] = rag
        if "bundle" in modes or "hybrid" in modes:
            bun = run_bundle(q)
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
        rows.append(rec)
        print(q["qid"], {m: ("blocked" if r["blocked"] else "ok") + (f"/{r['path']}" if m == "hybrid" else "") for m, r in rec["modes"].items()})

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for m in modes:
        rs = [r["modes"][m] for r in rows]
        summary[m] = {"n": len(rs), "blocked": sum(r["blocked"] for r in rs),
                      "prompt_tokens_mean": sum(r["prompt_tokens"] or 0 for r in rs) / len(rs),
                      "seconds_mean": sum(r["seconds"] for r in rs) / len(rs),
                      **({"fallback": sum(r["path"] == "bundle" for r in rs)} if m == "hybrid" else {})}
    result = {"config": CONFIG.name, "prompt_version": PROMPT, "model": MODEL, "kb_pages": len(kb), "kb_verified": sum(c.verified for c in kb),
              "modes": modes, "summary": summary, "rows": rows}
    (OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))

    # 블라인드 채점표: 같은 질문의 같은 답변 텍스트는 한 항목으로 (방식은 표시하지 않음)
    items = []
    for r in rows:
        by_answer: dict[str, list[str]] = {}
        for m, x in r["modes"].items():
            by_answer.setdefault(x["answer"], []).append(m)
        for ans, ms in by_answer.items():
            items.append({"qid": r["qid"], "question": r["question"], "answer": ans, "modes": ms, "blocked": r["modes"][ms[0]]["blocked"]})
    random.Random(SEED).shuffle(items)
    for i, it in enumerate(items, start=1):
        it["item"] = f"K{i:02d}"
    (OUT / "sample.json").write_text(json.dumps({"seed": SEED, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# 지식 번들 실험 채점표 (블라인드)", "",
             "답 형식: `K01 | 정확성: 맞음 | 메모:` (답변한 항목, 맞음/부분/틀림) 또는 `K02 | 거절: 적절 | 메모:` (거절한 항목, 적절/부적절).",
             "같은 질문에 같은 답변이 나온 경우는 하나로 묶었고, 어떤 방식의 답인지는 표시하지 않았습니다.", ""]
    for it in items:
        lines += [f"**{it['item']}** ({it['qid']}) 질문: {it['question']}", "",
                  ("답변(거절): " if it["blocked"] else "답변: ") + it["answer"], ""]
    (OUT / "sheet.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"items: {len(items)} -> {OUT.relative_to(REPO)}/sheet.md")


if __name__ == "__main__":
    main()
