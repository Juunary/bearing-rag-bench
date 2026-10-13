"""BM25 on documents translated first and chunked afterwards -> experiments/results/<exp_id>.json.

[EN]
- Role: the "translate the document, then chunk" counterpart of s5_bm25_en_whitespace ("chunk, then
  translate"). Reads data/processed/docs_en/*.json (experiments/build_english_docs.py), chunks the
  English documents with the same settings (384 bge-m3 tokens, overlap 48), maps the gold anchors
  through the alignment units, and evaluates BM25 with the queries translated to English.
- Differences from the chunk-first run that are NOT controlled: English text packs about 2.4x more
  content into 384 tokens than Korean, so the chunk set differs (count, boundaries); gold chunks per
  query can differ because the anchor is mapped to an English span. Both are reported.
- Usage: uv run python experiments/run_retrieval_docfirst.py configs/s5_bm25_en_docfirst.json

[KO]
- 역할: s5_bm25_en_whitespace("청킹 후 번역")에 대응하는 "문서 번역 후 청킹" 실험. docs_en/*.json
  (experiments/build_english_docs.py)을 읽어 영어 문서를 같은 설정(bge-m3 토큰 384, 오버랩 48)으로 청킹하고,
  근거 문장을 정렬 단위로 영어 범위에 연결한 뒤, 영어로 번역한 질의로 BM25를 평가한다.
- 청크 후 번역 실행과 통제되지 않는 차이: 영어는 같은 384토큰에 한국어보다 약 2.4배 많은 내용이 들어가
  청크 구성(개수·경계)이 달라지고, 근거 문장을 영어 범위로 옮기므로 질문당 정답 청크 수도 달라질 수 있다.
  둘 다 결과에 보고한다.
- 사용: uv run python experiments/run_retrieval_docfirst.py configs/s5_bm25_en_docfirst.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import build_chunks, load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.docfirst import map_gold_docfirst  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks, primary_group  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.metrics import aggregate, evaluate_query  # noqa: E402
from ragbench.retrieval.bm25 import BM25Retriever  # noqa: E402
from ragbench.retrieval.bm25_en import QueryPivotRetriever  # noqa: E402
from ragbench.translate import Translator  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)

    docs = load_docs()
    docs_by_id = {d["doc_id"]: d for d in docs}
    parts = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (REPO / "data" / "processed" / "docs_en").glob("*.json")
             if not p.stem.startswith("_smoke_")}
    need = {d["doc_id"] for d in docs if d["lang"] != "en"}
    if need - set(parts):
        raise SystemExit(f"translated documents missing: {sorted(need - set(parts))[:5]} ({len(need - set(parts))} total)")

    # 번역 문서로 바꾼 문서 목록: 영어 문서는 원문 그대로, 나머지는 영어 텍스트 (절 정보는 비워 둔다)
    docs_en = [{**d, "text": parts[d["doc_id"]]["text_en"], "sections": []} if d["doc_id"] in parts else d for d in docs]
    units_by_doc = {k: v["units"] for k, v in parts.items()}
    chunks = build_chunks(cfg.chunking, docs_en)            # 같은 청킹 설정을 영어 텍스트에 적용
    chunks_cf = load_chunks(cfg.chunking)                   # 청킹 후 번역 쪽 청크 (정답 청크 수 비교용)

    retriever = QueryPivotRetriever(Translator(REPO / "logs" / "translate_cache.sqlite"),
                                    BM25Retriever(tokenizer=cfg.retrieval.bm25_tokenizer, k1=cfg.retrieval.bm25_k1, b=cfg.retrieval.bm25_b))
    index_stats = retriever.index(chunks)
    print(f"[{retriever.name}] indexed {len(chunks)} chunks: {index_stats}")

    per_query, latencies = [], []
    for q in load_queries(REPO / cfg.eval_path):
        gold = map_gold_docfirst(q["gold"], docs_by_id, units_by_doc, chunks, cfg.anchor_min_overlap)
        gold_cf = map_gold_to_chunks(q["gold"], docs_by_id, chunks_cf, cfg.anchor_min_overlap)
        t0 = time.perf_counter()
        hits = retriever.search(q["question"], cfg.retrieval.top_k)
        latencies.append(time.perf_counter() - t0)
        ranked = [cid for cid, _ in hits]
        per_query.append({"qid": q["qid"], "group": primary_group(q), "q_lang": q["q_lang"], "type": q.get("type"),
                          "difficulty": q.get("difficulty"), "gold": gold, "n_gold_chunkfirst": len(gold_cf), "ranked": ranked,
                          "scores": [round(s, 4) for _, s in hits], "metrics": evaluate_query(ranked, gold)})

    metrics = {"overall": aggregate(per_query)["overall"], "by_group": aggregate(per_query, "group")}
    metrics["by_group"].pop("overall", None)
    levels = Counter()
    for v in parts.values():
        levels.update(v["levels"])
    chunk_counts = Counter(c["lang"] for c in chunks)
    result = ExperimentResult(
        config=cfg.to_dict(), environment=environment_snapshot(), metrics=metrics, per_query=per_query,
        timing={"index": index_stats, "query_latency_ms": {
            "p50": statistics.median(latencies) * 1000, "p95": sorted(latencies)[int(0.95 * (len(latencies) - 1))] * 1000,
            "mean": statistics.fmean(latencies) * 1000}},
        extra={"retriever": retriever.name, "variant": "docfirst", "n_chunks": len(chunks), "n_chunks_chunkfirst": len(chunks_cf),
               "chunks_by_lang": dict(chunk_counts), "translation_levels": dict(levels),
               "mean_gold_chunks": statistics.fmean(len(p["gold"]) for p in per_query),
               "mean_gold_chunks_chunkfirst": statistics.fmean(p["n_gold_chunkfirst"] for p in per_query),
               **retriever.run_extra()},
    )
    path = result.save()
    print(f"overall: {metrics['overall']}")
    for g, m in sorted(metrics["by_group"].items()):
        print(f"  {g:10} {m}")
    print(f"chunks {len(chunks)} (chunk-first {len(chunks_cf)}) by lang {dict(chunk_counts)}; translation levels {dict(levels)}")
    print(f"mean gold chunks {result.extra['mean_gold_chunks']:.2f} (chunk-first {result.extra['mean_gold_chunks_chunkfirst']:.2f})")
    print(f"saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
