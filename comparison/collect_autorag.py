"""Score every AutoRAG module result with the repository's metrics -> experiments/results/cmp_ar_*.json.

[EN]
- AutoRAG writes one parquet per module under <trial>/0/<node_line>/<node_type>/ (retrieved_ids and scores per
  question) and a summary.csv with the module parameters, its execution time and its own metrics. This script
  reads every module result, takes the first 10 ranked ids and scores them with cmp_common.evaluate_system, so
  AutoRAG's variants are measured exactly like the other systems. AutoRAG's own choice (is_best) is recorded.
- Latency: AutoRAG reports the execution time of a module over all questions; the per-question figure is that
  time divided by the number of questions (it includes the module's own setup, so it is an upper bound).
- Usage: uv run python collect_autorag.py [trial_name]

[KO]
- AutoRAG는 <trial>/0/<node_line>/<node_type>/ 아래에 모듈마다 parquet 하나(질문별 retrieved_ids와 점수)와,
  모듈 파라미터, 실행 시간, 자체 지표가 담긴 summary.csv를 쓴다. 이 스크립트는 모든 모듈 결과를 읽어 상위 10개
  ID를 cmp_common.evaluate_system으로 채점하므로 AutoRAG 변형도 다른 시스템과 똑같이 측정된다. AutoRAG 자체의
  선택(is_best)은 기록해 둔다.
- 지연: AutoRAG는 모듈이 전체 질문에 쓴 실행 시간을 보고한다. 질문당 값은 그 시간을 질문 수로 나눈 것이며
  모듈 자체 준비 시간을 포함하므로 상한이다.
- 사용: uv run python collect_autorag.py [trial_name]
"""

import ast
import re
import sys
from pathlib import Path

import pandas as pd

from cmp_common import evaluate_system, load_qa

HERE = Path(__file__).resolve().parent
trial = sys.argv[1] if len(sys.argv) > 1 else "autorag_retrieval"
root = HERE / "autorag_trial" / trial / "0"
qa = load_qa()
n = len(qa)
qa_queries = pd.read_parquet(HERE / "data" / "autorag" / "qa.parquet")["query"].tolist()
assert len(qa_queries) == n and len(set(qa_queries)) == n, "qa.parquet queries must be unique and match the QA set"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def short_name(node_type: str, module: str, params: str) -> str:
    """Readable result name: ar_bm25_space, ar_vector, ar_hybrid_rrf, ar_hybrid_cc_mm, ar_rerank_flag ..."""
    if node_type == "lexical_retrieval":
        return "ar_bm25_" + re.search(r"'bm25_tokenizer': '(\w+)'", params).group(1)
    if node_type == "semantic_retrieval":
        return "ar_vector"
    if node_type == "hybrid_retrieval":
        return "ar_hybrid_rrf" if module == "HybridRRF" else "ar_hybrid_cc_" + re.search(r"'normalize_method': '(\w+)'", params).group(1)
    return {"PassReranker": "ar_rerank_pass", "FlagEmbeddingReranker": "ar_rerank_flag", "SentenceTransformerReranker": "ar_rerank_st"}[module]


for summary_path in sorted(root.glob("*/*/summary.csv")):
    node_dir = summary_path.parent
    node_type = node_dir.name
    summary = pd.read_csv(summary_path)
    for _, row in summary.iterrows():
        idx = int(row["filename"].split(".")[0])
        res = pd.read_parquet(node_dir / f"{idx}.parquet")
        # 모듈 결과에는 query 열이 없고 qa.parquet와 같은 행 순서다
        by_query = {q: (list(r["retrieved_ids"]), list(r["retrieve_scores"])) for q, (_, r) in zip(qa_queries, res.iterrows())}
        params = row.get("module_params", "{}")
        name = short_name(node_type, row["module_name"], str(params))
        seconds = float(row["execution_time"])
        evaluate_system(name, "AutoRAG", f"AutoRAG {node_type} / {row['module_name']} {params}",
                        lambda q, k, d=by_query: list(zip(d[q][0][:k], d[q][1][:k])), qa,
                        extra={"autorag_node": node_type, "module": row["module_name"], "module_params": str(params), "autorag_is_best": bool(row.get("is_best", False)),
                               "autorag_execution_seconds": seconds}, latency_ms=1000 * seconds / n)
