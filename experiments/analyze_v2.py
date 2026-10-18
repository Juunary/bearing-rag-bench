"""Analyse the retrieval experiments of the improvement round (90-question set) -> experiments/results/v2_analysis.md.

[EN]
- Reads experiments/results/v2_*.json (retrieval runs). Sections: (1) all configs with Recall@5, MRR@10,
  nDCG@10, mono / cross nDCG and the added per-query cost of translation or expansion; (2) the paired
  comparisons that were fixed BEFORE the runs (PAIRS below) with the mean nDCG@10 difference, the
  95 % interval by question (iid) and by primary-evidence document (cluster), win/loss/tie counts and the
  exact sign test; (3) reranker pool diagnosis (is the gold chunk inside the candidate list, and does the
  reranker keep it in the top 5); (4) nDCG@10 per language pair for the main configs.
- Multiplicity: the number of paired comparisons is printed; no correction is applied to the intervals, so
  read them as exploratory unless the cluster interval and the sign test agree.
- Usage: uv run python experiments/analyze_v2.py

[KO]
- experiments/results/v2_*.json(검색 실행)을 읽는다. 구성: (1) 모든 설정의 Recall@5, MRR@10, nDCG@10,
  단일/교차 nDCG, 번역·확장이 질문당 더하는 비용; (2) 실행 전에 정한 쌍체 비교(아래 PAIRS)의 nDCG@10 평균 차이,
  질문 단위(iid)와 주 근거 문서 단위(군집) 95% 구간, 개선/악화/동일 수, 정확한 부호 검정; (3) 리랭커 후보 풀
  진단(정답 청크가 후보 목록 안에 있는가, 리랭커가 상위 5 안에 유지하는가); (4) 주요 설정의 언어쌍별 nDCG@10.
- 다중 비교: 쌍체 비교 개수를 출력하며 구간에 보정은 하지 않는다. 군집 구간과 부호 검정이 함께 일치할 때만
  확정으로, 아니면 탐색적으로 읽는다.
- 사용: uv run python experiments/analyze_v2.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.stats import compare  # noqa: E402

RES = REPO / "experiments" / "results"
# (A, B): A - B. 실행 전에 정한 가설들. b_는 기준선이다.
PAIRS = [
    ("b_bm25_en", "b_bm25_kiwi"), ("b_rrf_en_rerank", "b_rrf_rerank"), ("b_bm25_en", "b_dense"), ("b_rrf_en", "b_rrf"),
    ("x1_rrf3", "b_rrf_en"), ("x1_rrf3_rerank", "b_rrf_en_rerank"), ("x1_rrf3_rerank", "b_rrf_rerank"),
    ("x2_rerank_n50", "b_rrf_en_rerank"), ("x2_rerank_n100", "b_rrf_en_rerank"), ("x2_rerank_en_text", "b_rrf_en_rerank"),
    ("x2_orig_rerank_n100", "b_rrf_rerank"),
    ("x3_bm25_en_gl", "b_bm25_en"), ("x3_rrf_en_rerank_gl", "b_rrf_en_rerank"),
    ("x4_bm25_en_stem", "b_bm25_en"), ("x4_bm25_en_stem_stop", "b_bm25_en"),
    ("x5_bm25_en_multi", "b_bm25_en"), ("x5_bm25_en_hyde", "b_bm25_en"),
    ("x6_dense_c256", "b_dense"), ("x6_dense_c512", "b_dense"), ("x6_bm25_kiwi_c256", "b_bm25_kiwi"), ("x6_bm25_kiwi_c512", "b_bm25_kiwi"),
    ("x6_rrf_rerank_c256", "b_rrf_rerank"), ("x6_rrf_rerank_c512", "b_rrf_rerank"),
    ("x6_dense_ctx", "b_dense"), ("x6_bm25_kiwi_ctx", "b_bm25_kiwi"), ("x6_rrf_rerank_ctx", "b_rrf_rerank"),
    ("x11_bm25_en_skip", "b_bm25_en"),
]


def load(name: str) -> dict | None:
    p = RES / f"v2_{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ndcg(d: dict) -> np.ndarray:
    return np.array([q["metrics"]["ndcg@10"] for q in d["per_query"]])


def main() -> None:
    names = sorted(p.stem.removeprefix("v2_") for p in RES.glob("v2_*.json")
                   if p.stem.removeprefix("v2_").split("_")[0] in {"b", *(f"x{i}" for i in range(1, 12))})
    R = {n: load(n) for n in names}
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    first = next(iter(R.values()))
    qids = [q["qid"] for q in first["per_query"]]
    types = np.array([queries[i]["type"] for i in qids])
    clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
    out = ["# v2 analysis (90 questions)", "", f"configs: {len(R)}; clusters (primary-evidence documents): {len(set(clusters))}", "",
           "## 1. All configs", "", "| config | R@5 | MRR@10 | nDCG@10 | mono | cross | +s/query (translate/expand) | p50 ms |", "|---|---|---|---|---|---|---|---|"]
    for n, d in R.items():
        o, x, ex = d["metrics"]["overall"], ndcg(d), d["extra"]
        extra_s = (ex.get("query_translation_seconds_p50") or 0) + (ex.get("query_expansion_seconds_p50") or 0)
        out.append(f"| {n} | {o['recall@5']:.3f} | {o['mrr@10']:.3f} | {o['ndcg@10']:.3f} | {x[types == 'mono'].mean():.3f} | {x[types == 'cross'].mean():.3f} | "
                   f"{extra_s:.2f} | {d['timing']['query_latency_ms']['p50']:.1f} |")

    done = [(a, b) for a, b in PAIRS if a in R and b in R]
    out += ["", f"## 2. Paired comparisons fixed before the runs (nDCG@10, A - B; {len(done)} comparisons, no multiplicity correction)", "",
            "| A | B | mean diff | 95% CI (question) | 95% CI (document cluster) | better/worse/tie | sign-test p |", "|---|---|---|---|---|---|---|"]
    for a, b in done:
        c = compare(ndcg(R[a]) - ndcg(R[b]), clusters)
        out.append(f"| {a} | {b} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | "
                   f"{c['better']}/{c['worse']}/{c['tie']} | {c['sign_p']:.3f} |")

    out += ["", "## 3. Reranker pool diagnosis", "",
            "gold in pool = at least one gold chunk is among the candidates given to the reranker; kept = a gold chunk is in the reranked top 5.", "",
            "| config | pool size | gold in pool | gold in top 5 | lost by reranker (in pool, not in top 5) | not in pool |", "|---|---|---|---|---|---|"]
    for n, d in R.items():
        if "rerank_pool" not in d["per_query"][0]:
            continue
        inpool = kept = 0
        for q in d["per_query"]:
            gold = set(q["gold"])
            p = gold & set(q["rerank_pool"])
            inpool += bool(p)
            kept += bool(gold & set(q["ranked"][:5]))
        N = len(d["per_query"])
        out.append(f"| {n} | {len(d['per_query'][0]['rerank_pool'])} | {inpool}/{N} | {kept}/{N} | {inpool - kept} | {N - inpool} |")

    pairs_of = {}
    for i, qid in enumerate(qids):
        pairs_of.setdefault(f"{queries[qid]['q_lang']}->{queries[qid]['gold'][0]['doc_lang']}", []).append(i)
    keys = sorted(pairs_of)
    main_cfgs = [n for n in ("b_bm25_kiwi", "b_dense", "b_rrf_rerank", "b_bm25_en", "b_rrf_en_rerank", "x1_rrf3_rerank", "x5_bm25_en_multi") if n in R]
    out += ["", "## 4. nDCG@10 per language pair (10 questions each)", "", "| config | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for n in main_cfgs:
        x = ndcg(R[n])
        out.append(f"| {n} | " + " | ".join(f"{x[pairs_of[k]].mean():.2f}" for k in keys) + " |")
    text = "\n".join(out) + "\n"
    (RES / "v2_analysis.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
