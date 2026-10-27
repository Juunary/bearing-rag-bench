"""Shared pieces of the framework comparison: data loading, scoring with the repository's metrics, result files.

[EN]
- Every system (LlamaIndex, Haystack, AutoRAG, ours) is scored here with the SAME functions: the gold of each
  question is a {chunk_id: grade} dict (comparison/data/qa.jsonl), the ranked list is the chunk ids the system
  returned, and Recall@5 / MRR@10 / nDCG@10 come from ragbench.metrics. The frameworks' own metrics are not used.
- A result file has the layout of the repository's retrieval results (per_query with qid, group, ranked, gold,
  metrics) so the generation step can read it as `retrieval_result` and the analysis can mix it with our runs.

[KO]
- 모든 시스템(LlamaIndex, Haystack, AutoRAG, 우리 것)을 여기서 같은 함수로 채점한다: 질문마다 gold는
  {청크 ID: 등급} 딕셔너리(comparison/data/qa.jsonl), 순위 목록은 시스템이 돌려준 청크 ID, Recall@5 / MRR@10 /
  nDCG@10은 ragbench.metrics에서 온다. 프레임워크 자체 지표는 쓰지 않는다.
- 결과 파일은 저장소의 검색 결과와 같은 구조(질문별 qid, group, ranked, gold, metrics)라서 생성 단계가
  `retrieval_result`로 읽고 분석이 우리 실행과 섞어 쓸 수 있다.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))

from ragbench.metrics import aggregate, evaluate_query  # noqa: E402

DATA = HERE / "data"
RESULTS = REPO / "experiments" / "results"


def environment() -> dict:
    """Run provenance: comparison-env python and framework versions, git commit (generation reads environment.git_commit)."""
    import platform
    import subprocess
    from datetime import datetime, timezone
    from importlib.metadata import PackageNotFoundError, version

    def ver(pkg: str):
        try:
            return version(pkg)
        except PackageNotFoundError:
            return None

    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--", "src", "eval"], capture_output=True, text=True).stdout.strip()
    return {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "git_commit": head + ("-dirty" if dirty else ""),
            "packages": {p: ver(p) for p in ("autorag", "llama-index-core", "llama-index-retrievers-bm25", "haystack-ai", "sentence-transformers",
                                             "FlagEmbedding", "torch", "transformers", "kiwipiepy")}}


def load_corpus() -> list[dict]:
    return [json.loads(l) for l in open(DATA / "corpus.jsonl", encoding="utf-8") if l.strip()]


def load_qa() -> list[dict]:
    return [json.loads(l) for l in open(DATA / "qa.jsonl", encoding="utf-8") if l.strip()]


def evaluate_system(name: str, framework: str, description: str, search, qa: list[dict], k: int = 10, extra: dict | None = None,
                    latency_ms: float | None = None) -> dict:
    """Run `search(question, k) -> list[(chunk_id, score)]` over the questions, score it and save cmp_<name>.json."""
    per_query, lat = [], []
    for q in qa:
        t0 = time.perf_counter()
        hits = search(q["question"], k)
        lat.append(time.perf_counter() - t0)
        ranked = [h[0] for h in hits]
        per_query.append({"qid": q["qid"], "group": q["group"], "q_lang": q["q_lang"], "type": q["type"], "gold": q["gold"], "ranked": ranked,
                          "scores": [round(float(h[1]), 4) for h in hits], "metrics": evaluate_query(ranked, q["gold"])})
    agg = aggregate(per_query, "group")
    result = {"environment": environment(), "config": {"exp_id": f"cmp_{name}", "stage": "cmp", "framework": framework, "description": description, "eval_path": "eval/queries_v2.jsonl"},
              "metrics": {"overall": agg.pop("overall"), "by_group": agg}, "per_query": per_query,
              # latency_ms: 결과를 파일에서 읽어 채점하는 시스템(AutoRAG)은 자체 보고한 질문당 시간을 넘긴다
              "timing": {"query_latency_ms": {"p50": statistics.median(lat) * 1000, "p95": sorted(lat)[int(0.95 * (len(lat) - 1))] * 1000,
                                              "mean": statistics.fmean(lat) * 1000} if latency_ms is None else {"p50": latency_ms, "p95": latency_ms, "mean": latency_ms}},
              "extra": extra or {}}
    (RESULTS / f"cmp_{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    o = result["metrics"]["overall"]
    print(f"[{name}] R@5 {o['recall@5']:.3f}  MRR@10 {o['mrr@10']:.3f}  nDCG@10 {o['ndcg@10']:.3f}  p50 {result['timing']['query_latency_ms']['p50']:.1f} ms", flush=True)
    return result
