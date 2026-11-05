"""Answer a question file with a serving config (the real RAGPipeline, knowledge bundle included) -> JSON.

[EN]
- Role: run exactly what the chat server runs (experiments/serve_chat.py builds the same pipeline) on a JSONL file of
  questions and store, per question: path ("kb" | "rag"), matched pages, context ids, answer, blocked/reason, tokens,
  timings. Used for the trace page (scripts/export_site_data.py) and for checking a serving config on known questions.
- Usage: uv run python scripts/answer_questions.py --config configs/s7_pipeline_kb.json --questions eval/kb/questions.jsonl
             eval/human_round2/user_questions.jsonl --out eval/service/s7_answers.json

[KO]
- 역할: 채팅 서버가 돌리는 것과 똑같은 파이프라인(experiments/serve_chat.py와 같은 구성, 지식 번들 포함)으로 질문 파일을 답하고
  질문마다 경로("kb" | "rag"), 매칭 페이지, 컨텍스트 ID, 답변, 차단 여부, 토큰, 시간을 저장한다. 추적 페이지 데이터와 서비스 설정 점검용.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.generation import Generator  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever, share_translator_model  # noqa: E402


def build(cfg: ExperimentConfig, cache_path: Path) -> RAGPipeline:
    """Same construction as experiments/serve_chat.py (kept in one place for the trace page and the server)."""
    g = cfg.generation
    chunks = load_chunks(cfg.chunking)
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    generator = Generator(g.model, device=g.device, quantize_4bit=g.quantize_4bit, adapter=g.adapter)
    share_translator_model(retriever, generator)
    kb = None
    if g.kb_bundle:
        from ragbench.kb import KnowledgeBundle
        dense = next((r for r in getattr(retriever.base, "retrievers", []) if "dense" in r.name), None)
        embedder = getattr(getattr(dense, "inner", dense), "embedder", None)
        kb = KnowledgeBundle(REPO / g.kb_bundle, embedder=embedder, dense_min=g.kb_dense_min, context=g.kb_context)
    return RAGPipeline(retriever, chunks, generator, LLMCache(cache_path), RequestLogger(REPO / "logs" / "answer_questions.jsonl"),
                       prompt_version=g.prompt_version, context_k=g.context_k, max_new_tokens=g.max_new_tokens,
                       config_id=f"answer:{cfg.exp_id}", kb=kb)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--questions", type=Path, nargs="+", required=True, help="JSONL files with qid and question")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)
    pipe = build(cfg, REPO / "logs" / "chat_cache.sqlite")
    rows = []
    for path in args.questions:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            q = json.loads(line)
            r = pipe.answer(q["question"])
            rows.append({**{k: v for k, v in q.items() if k in ("qid", "question", "scope", "topic", "q_lang")}, "source": path.name,
                         "path": r.path, "kb_match": r.kb_match, "context_ids": list(r.context_ids), "answer": r.answer, "raw_answer": r.raw_answer,
                         "blocked": r.blocked, "reason": r.reason, "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
                         "timings_ms": {k: round(v, 1) for k, v in r.timings_ms.items()}, "cache_hit": r.cache_hit})
            print(q["qid"], r.path, "blocked" if r.blocked else "ok", f"{r.timings_ms.get('total', 0):.0f}ms", r.answer[:70].replace("\n", " "))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"config": args.config.name, "exp_id": cfg.exp_id, "n": len(rows),
                                    "paths": {p: sum(r["path"] == p for r in rows) for p in ("kb", "rag", "invalid")},
                                    "blocked": sum(r["blocked"] for r in rows), "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved -> {args.out}")


if __name__ == "__main__":
    main()
