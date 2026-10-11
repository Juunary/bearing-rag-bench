"""Run one retrieval experiment from a config file and write experiments/results/<exp_id>.json.

    uv run python experiments/run_retrieval.py configs/s1_bm25_kiwi.json
    uv run python experiments/run_retrieval.py configs/s1_bm25_kiwi.json --dry-run   # index + 3 sample queries, no eval set needed

Per query the group key is "{q_lang}->{doc_lang of the highest-grade gold}" ("mixed" if the
top-grade golds span several languages), so cross-language results are aggregated per pair.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402

SAMPLE_QUERIES = [
    ("ko", "테이퍼 롤러 베어링은 어떤 하중을 받을 수 있는가?"),
    ("en", "What causes brinelling in a bearing raceway?"),
    ("de", "Welche Aufgabe hat der Käfig in einem Wälzlager?"),
]


def build_retriever(cfg: ExperimentConfig):
    r = cfg.retrieval
    if r.method == "bm25":
        from ragbench.retrieval.bm25 import BM25Retriever
        return BM25Retriever(tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b)
    if r.method == "dense":
        from ragbench.retrieval.dense import DenseRetriever
        return DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search)
    if r.method in ("hybrid", "hybrid_rerank"):
        from ragbench.retrieval.bm25 import BM25Retriever
        from ragbench.retrieval.dense import DenseRetriever
        from ragbench.retrieval.hybrid import RRFRetriever
        base = RRFRetriever(
            [BM25Retriever(tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b),
             DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search)],
            rrf_k=r.rrf_k, candidates=r.fusion_candidates)
        if r.method == "hybrid":
            return base
        from ragbench.retrieval.rerank import RerankRetriever
        return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n)
    raise ValueError(f"unknown retrieval method {r.method!r}")


def group_of(q: dict) -> str:
    top = max(g["grade"] for g in q["gold"])
    langs = {g["doc_lang"] for g in q["gold"] if g["grade"] == top}
    return f"{q['q_lang']}->{langs.pop() if len(langs) == 1 else 'mixed'}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)
    docs = load_docs()
    docs_by_id = {d["doc_id"]: d for d in docs}
    chunks = load_chunks(cfg.chunking)
    chunk_text = {c["chunk_id"]: c for c in chunks}

    retriever = build_retriever(cfg)
    index_stats = retriever.index(chunks)
    print(f"[{retriever.name}] indexed {len(chunks)} chunks: {index_stats}")

    if args.dry_run:
        for lang, q in SAMPLE_QUERIES:
            hits = retriever.search(q, cfg.retrieval.top_k)
            print(f"\n[{lang}] {q}")
            for cid, score in hits[:3]:
                c = chunk_text[cid]
                print(f"   {score:7.3f} {cid:36} {' > '.join(c['section_path']) or '(lead)'} | {c['text'][:90]!r}")
        return

    from ragbench.metrics import aggregate, evaluate_query   # user-implemented

    queries = load_queries(REPO / cfg.eval_path)
    per_query = []
    latencies = []
    for q in queries:
        gold = map_gold_to_chunks(q["gold"], docs_by_id, chunks, cfg.anchor_min_overlap)
        t0 = time.perf_counter()
        hits = retriever.search(q["question"], cfg.retrieval.top_k)
        latencies.append(time.perf_counter() - t0)
        ranked = [cid for cid, _ in hits]
        per_query.append({
            "qid": q["qid"], "group": group_of(q), "q_lang": q["q_lang"], "type": q.get("type"),
            "difficulty": q.get("difficulty"), "gold": gold, "ranked": ranked,
            "scores": [round(s, 4) for _, s in hits], "metrics": evaluate_query(ranked, gold),
        })

    metrics = {"overall": aggregate(per_query)["overall"], "by_group": aggregate(per_query, "group")}
    metrics["by_group"].pop("overall", None)
    result = ExperimentResult(
        config=cfg.to_dict(), environment=environment_snapshot(), metrics=metrics, per_query=per_query,
        timing={"index": index_stats, "query_latency_ms": {
            "p50": statistics.median(latencies) * 1000,
            "p95": sorted(latencies)[int(0.95 * (len(latencies) - 1))] * 1000,
            "mean": statistics.fmean(latencies) * 1000}},
        extra={"retriever": retriever.name, "n_chunks": len(chunks)},
    )
    path = result.save()
    print(f"overall: {metrics['overall']}")
    for g, m in sorted(metrics["by_group"].items()):
        print(f"  {g:10} {m}")
    print(f"saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
