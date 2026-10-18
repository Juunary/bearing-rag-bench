"""Retrieval metrics: Recall@k, MRR@k, nDCG@k, grouped aggregation.

[EN]
- Role: hand-written metric functions (no library) so the formulas are visible and testable.
- Conventions (decided 2026-10-11; keep README in sync):
  - ranked: chunk ids in retriever order (best first). gold: {chunk_id: grade}, grade 2 = core
    evidence, 1 = supporting. Every gold id counts as relevant for Recall / MRR.
  - Recall@k = |relevant in ranked[:k]| / |relevant|  (strict recall, not hit-rate).
  - MRR@k = 1 / rank of first relevant id within top k, else 0.
  - nDCG@k with LINEAR gain: DCG = sum grade(ranked[i]) / log2(i+1), i = 1-based rank.
    IDCG = DCG of gold grades sorted descending, truncated at k. Linear (as in trec_eval) keeps
    hand computation easy; exponential gain (2**g - 1) would weight core:support = 3:1.
  - Empty gold -> ValueError (data error must not silently become 0).
  - ranked shorter than k is fine.
  - Duplicate ids in ranked (added 2026-10-19): only the FIRST occurrence can score; a repeated id
    occupies its slot but adds nothing (no gain, no hit), and the ranks of the other ids do not
    move. Without this, recall and nDCG could exceed 1. The current retrievers never repeat an id
    (RRF fuses by id); the rule keeps the metrics valid if a future retriever does.
- Why graded nDCG: the eval set marks core vs supporting evidence, so ordering quality matters.


[KO]
- 역할: 라이브러리 없이 직접 쓴 지표 함수. 수식이 코드에 드러나고 테스트로 검증한다.
- 규약(2026-10-11 결정, README와 동기화):
  - ranked: 검색기가 돌려준 순서의 청크 ID. gold: {청크ID: 등급}, 2=핵심 근거, 1=보조 근거.
    Recall/MRR에서는 gold에 있는 모든 ID가 "관련"이다.
  - Recall@k = 상위 k 안의 관련 ID 수 / 전체 관련 ID 수 (엄밀한 recall, hit-rate 아님).
  - MRR@k = 상위 k 안 첫 관련 ID 순위의 역수, 없으면 0.
  - nDCG@k는 선형 gain: DCG = Σ grade/log2(i+1), i는 1부터. IDCG는 gold 등급 내림차순을 k에서
    자른 DCG. 선형(trec_eval 방식)은 손계산이 쉽다. 지수 gain(2**g-1)은 핵심:보조 = 3:1이 된다.
  - gold가 비면 ValueError (데이터 오류가 조용히 0이 되면 안 된다).
  - ranked가 k보다 짧아도 된다.
  - ranked에 같은 ID가 반복되면(2026-10-19 추가): 첫 등장만 점수를 낸다. 반복된 ID는 자리만 차지하고
    이득도 적중도 없으며 다른 ID의 순위는 밀리지 않는다. 이 규칙이 없으면 recall과 nDCG가 1을 넘을 수
    있다. 현재 검색기는 ID를 반복하지 않지만(RRF는 ID로 융합) 이후 검색기가 반복해도 지표가 유효하다.
- 등급형 nDCG를 쓰는 이유: 평가셋이 핵심/보조 근거를 구분하므로 순서 품질을 반영한다.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


def _first_occurrences(ranked: list[str], k: int) -> list[str | None]:
    """Top-k slots where a repeated id is replaced by None (the slot stays, so other ranks do not move)."""
    seen: set[str] = set()
    out: list[str | None] = []
    for chunk_id in ranked[:k]:
        out.append(None if chunk_id in seen else chunk_id)
        seen.add(chunk_id)
    return out


def recall_at_k(ranked: list[str], gold: dict[str, int], k: int) -> float:
    if not gold:
        raise ValueError("gold must not be empty")
    relevant = set(gold)
    hit = sum(1 for chunk_id in _first_occurrences(ranked, k) if chunk_id in relevant)
    return hit / len(relevant)

def mrr_at_k(ranked: list[str], gold: dict[str, int], k: int = 10) -> float:
    if not gold:
        raise ValueError("gold must not be empty")
    for rank, chunk_id in enumerate(_first_occurrences(ranked, k), start=1):
        if chunk_id in gold:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked: list[str], gold: dict[str, int], k: int = 10) -> float:
    if not gold:
        raise ValueError("gold must not be empty")
    # DCG
    dcg = 0.0
    for rank, chunk_id in enumerate(_first_occurrences(ranked, k), start=1):
        grade = gold.get(chunk_id, 0) if chunk_id is not None else 0     # 반복된 ID(None)는 이득 0
        dcg += grade / math.log2(rank + 1)
    # IDCG
    ideal_grades = sorted(gold.values(), reverse=True)[:k]
    idcg = sum(grade / math.log2(rank + 1) for rank, grade in enumerate(ideal_grades, start=1))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_query(ranked: list[str], gold: dict[str, int]) -> dict[str, float]:
    """Return {"recall@5": ..., "mrr@10": ..., "ndcg@10": ...} for one query."""
    return {
        "recall@5": recall_at_k(ranked, gold, k=5),
        "mrr@10": mrr_at_k(ranked, gold, k=10),
        "ndcg@10": ndcg_at_k(ranked, gold, k=10)
    }


def aggregate(per_query: list[dict[str, Any]], group_key: str | None = None) -> dict[str, dict[str, float]]:
    """Mean of each metric over queries.

    ``per_query`` items look like {"qid": ..., "group": "ko->en", "metrics": {"recall@5": ...}}.
    With ``group_key=None`` return {"overall": {metric: mean}}; with ``group_key="group"`` return
    {"ko->en": {...}, "en->en": {...}, ...} plus "overall". Also include "n" (query count) per group.
    """
    groups: dict[str, list[dict[str, float]]] = defaultdict(list)
    for q in per_query:
        metrics = q["metrics"]
        groups["overall"].append(metrics)
        if group_key:
            groups[q[group_key]].append(metrics)

    result: dict[str, dict[str, float]] = {}
    for name, items in groups.items():
        metric_names = list(items[0].keys())
        averaged = {metric_name: sum(m[metric_name] for m in items) / len(items) for metric_name in metric_names}
        averaged["n"] = len(items)
        result[name] = averaged
    return result