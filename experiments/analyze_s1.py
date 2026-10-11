"""Stage 1 summary: mono/cross split, bootstrap CI, latency, failures, hybrid-vs-dense losses.

[EN]
- Role: derive every number quoted in the README from experiments/results/*.json so the README
  can be regenerated and checked. Prints markdown tables to stdout.
- Sections: (1) overall + mono + cross per config with 95% bootstrap CI of overall nDCG@10
  (resampling queries, 10000 draws, seed 42), (2) query latency and index build time,
  (3) queries a config fails completely (Recall@5 = 0), (4) queries where dense beat the RRF hybrid.
- Usage: uv run python experiments/analyze_s1.py

[KO]
- 역할: README에 인용하는 모든 숫자를 결과 JSON에서 계산해 README를 다시 만들고 검증할 수 있게 한다.
  마크다운 표를 표준 출력으로 낸다.
- 구성: (1) 설정별 전체·단일·교차 언어 지표와 nDCG@10의 95% 부트스트랩 신뢰구간(질문 재표집 10000회,
  시드 42), (2) 질의 지연과 인덱스 빌드 시간, (3) 한 설정이 완전히 실패한 질문(Recall@5=0),
  (4) dense가 RRF 하이브리드보다 나았던 질문.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "experiments" / "results"
ORDER = ["s1_bm25_whitespace", "s1_bm25_kiwi", "s1_bm25_subword", "s1_dense_bge_m3_exact",
         "s1_dense_bge_m3", "s1_hybrid_rrf", "s1_hybrid_rrf_rerank"]
M = ["recall@5", "mrr@10", "ndcg@10"]


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def mean(per: list[dict], m: str) -> float:
    return float(np.mean([p["metrics"][m] for p in per])) if per else float("nan")


def is_cross(p: dict) -> bool:
    a, b = p["group"].split("->")
    return a != b


def boot_ci(vals: np.ndarray, n: int = 10000, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), size=(n, len(vals)))
    means = vals[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> None:
    R = {n: load(n) for n in ORDER}
    print("### 1. overall / mono / cross (n=45 / 21 / 24)\n")
    print("| config | Recall@5 | MRR@10 | nDCG@10 | nDCG@10 95% CI | nDCG mono | nDCG cross |")
    print("|---|---|---|---|---|---|---|")
    for n in ORDER:
        per = R[n]["per_query"]
        mono = [p for p in per if not is_cross(p)]
        cross = [p for p in per if is_cross(p)]
        lo, hi = boot_ci(np.array([p["metrics"]["ndcg@10"] for p in per]))
        print(f"| {n[3:]} | {mean(per,'recall@5'):.3f} | {mean(per,'mrr@10'):.3f} | {mean(per,'ndcg@10'):.3f} "
              f"| {lo:.3f} - {hi:.3f} | {mean(mono,'ndcg@10'):.3f} | {mean(cross,'ndcg@10'):.3f} |")

    print("\n### 2. latency (ms per query) and index build\n")
    print("| config | p50 | p95 | index build (s) |")
    print("|---|---|---|---|")
    for n in ORDER:
        t = R[n]["timing"]
        b = t["index"].get("build_seconds")
        print(f"| {n[3:]} | {t['query_latency_ms']['p50']:.2f} | {t['query_latency_ms']['p95']:.2f} | {b:.2f} |")

    print("\n### 3. complete failures of the best config (Recall@5 = 0)\n")
    best = R["s1_hybrid_rrf_rerank"]["per_query"]
    fails = [p for p in best if p["metrics"]["recall@5"] == 0]
    print(f"{len(fails)} of {len(best)} queries\n")
    qtext = {json.loads(l)["qid"]: json.loads(l)["question"] for l in open(REPO / "eval" / "queries.jsonl", encoding="utf-8")}
    for p in fails:
        top = p["ranked"][0] if p["ranked"] else "-"
        print(f"- {p['qid']} ({p['group']}): gold {sorted(p['gold'])} | top-1 {top} | {qtext[p['qid']][:70]}")

    print("\n### 4. dense better than RRF hybrid (gold chunks in top 5)\n")
    d = {p["qid"]: p for p in R["s1_dense_bge_m3"]["per_query"]}
    h = {p["qid"]: p for p in R["s1_hybrid_rrf"]["per_query"]}
    lost = []
    won = 0
    for q in d:
        dg = len(set(d[q]["ranked"][:5]) & set(d[q]["gold"]))
        hg = len(set(h[q]["ranked"][:5]) & set(h[q]["gold"]))
        if dg > hg:
            lost.append((q, d[q]["group"]))
        elif hg > dg:
            won += 1
    print(f"dense > hybrid: {len(lost)} queries; hybrid > dense: {won} queries")
    print("dense > hybrid groups:", sorted({g for _, g in lost}), "| cross:", sum(1 for _, g in lost if g.split('->')[0] != g.split('->')[1]), "of", len(lost))

    print("\n### 5. paired bootstrap of nDCG@10 differences (same queries, 10000 draws, seed 42)\n")
    pairs = [("dense_bge_m3", "bm25_kiwi"), ("hybrid_rrf", "dense_bge_m3"), ("hybrid_rrf_rerank", "dense_bge_m3"),
             ("hybrid_rrf_rerank", "hybrid_rrf"), ("bm25_kiwi", "bm25_whitespace"), ("bm25_subword", "bm25_whitespace")]
    print("| A - B | mean diff | 95% CI | A better in n queries |")
    print("|---|---|---|---|")
    for a_, b_ in pairs:
        pa = {p["qid"]: p["metrics"]["ndcg@10"] for p in R["s1_" + a_]["per_query"]}
        pb = {p["qid"]: p["metrics"]["ndcg@10"] for p in R["s1_" + b_]["per_query"]}
        diff = np.array([pa[q] - pb[q] for q in pa])
        lo, hi = boot_ci(diff)
        print(f"| {a_} - {b_} | {diff.mean():+.3f} | {lo:+.3f} .. {hi:+.3f} | {int((diff > 0).sum())} / {int((diff < 0).sum())} (worse) |")

    print("\n### 6. language of the top-1 chunk in complete failures of the best config\n")
    tops = [(p["qid"], p["group"], p["ranked"][0].split("_")[0]) for p in fails]
    same = sum(1 for _, g, t in tops if t == g.split("->")[0])
    print(f"top-1 chunk is in the question language in {same} of {len(tops)} failures:", [(q, g, t) for q, g, t in tops])

    print("\n### 7. HNSW vs exact: identical rankings?\n")
    e = R["s1_dense_bge_m3_exact"]["per_query"]
    a = R["s1_dense_bge_m3"]["per_query"]
    same = sum(1 for x, y in zip(e, a) if x["ranked"] == y["ranked"])
    print(f"{same} of {len(e)} queries have identical top-10 lists")


if __name__ == "__main__":
    main()
