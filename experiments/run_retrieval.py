"""Run one retrieval experiment from a config file -> experiments/results/<exp_id>.json.

[EN]
- Role: config -> seed -> docs/chunks -> retriever (by method) -> index -> for each eval query:
  map gold anchors to chunks, search, per-query metrics -> aggregate overall and per group ->
  save result with environment snapshot and latency (p50/p95).
- Group key = "{q_lang}->{doc_lang of gold[0]}" (primary evidence, always a top-grade gold), so
  cross-language quality is reported per language pair.
- --dry-run: build the index and print top-3 for three sample queries; needs no eval set.
  Used to sanity-check a retriever before the eval set exists.
- Metrics are imported from ragbench.metrics (author-implemented).
- Usage:
    uv run python experiments/run_retrieval.py configs/s1_bm25_kiwi.json [--dry-run]

[KO]
- 역할: 설정 -> 시드 -> 문서/청크 -> 방식별 검색기 -> 인덱스 -> 평가 질의마다 gold anchor를 청크로
  매핑, 검색, 질의별 지표 -> 전체·그룹별 집계 -> 환경 스냅샷과 지연(p50/p95)을 포함해 저장.
- 그룹 키 = "{질문 언어}->{gold[0]의 문서 언어}" (주 근거, 항상 최고 등급). 교차 언어 품질을
  언어쌍별로 보고한다.
- --dry-run: 인덱스를 만들고 샘플 질의 3개의 상위 3개를 출력. 평가셋 없이 검색기 동작을 확인할 때 쓴다.
- 지표는 ragbench.metrics(작성자 구현)에서 가져온다.
- 사용: uv run python experiments/run_retrieval.py configs/s1_bm25_kiwi.json [--dry-run]
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
from ragbench.evalset import load_queries, map_gold_to_chunks, primary_group  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.retrieval.factory import build_retriever  # noqa: E402

SAMPLE_QUERIES = [
    ("ko", "테이퍼 롤러 베어링은 어떤 하중을 받을 수 있는가?"),
    ("en", "What causes brinelling in a bearing raceway?"),
    ("de", "Welche Aufgabe hat der Käfig in einem Wälzlager?"),
]


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
            "qid": q["qid"], "group": primary_group(q), "q_lang": q["q_lang"], "type": q.get("type"),
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
