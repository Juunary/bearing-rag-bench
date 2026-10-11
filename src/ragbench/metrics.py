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
- Why graded nDCG: the eval set marks core vs supporting evidence, so ordering quality matters.
- Implementation: the author writes these; tests/test_metrics.py holds
  hand-computed expectations.

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
- 등급형 nDCG를 쓰는 이유: 평가셋이 핵심/보조 근거를 구분하므로 순서 품질을 반영한다.
- 구현: 작성자가 직접 쓴다. 기대값은 tests/test_metrics.py에 손계산으로 둔다.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


def recall_at_k(ranked: list[str], gold: dict[str, int], k: int) -> float:
    raise NotImplementedError


def mrr_at_k(ranked: list[str], gold: dict[str, int], k: int = 10) -> float:
    raise NotImplementedError


def ndcg_at_k(ranked: list[str], gold: dict[str, int], k: int = 10) -> float:
    # Hint: write a small dcg(grades: list[int]) helper and call it twice.
    raise NotImplementedError


def evaluate_query(ranked: list[str], gold: dict[str, int]) -> dict[str, float]:
    """Return {"recall@5": ..., "mrr@10": ..., "ndcg@10": ...} for one query."""
    raise NotImplementedError


def aggregate(per_query: list[dict[str, Any]], group_key: str | None = None) -> dict[str, dict[str, float]]:
    """Mean of each metric over queries.

    ``per_query`` items look like {"qid": ..., "group": "ko->en", "metrics": {"recall@5": ...}}.
    With ``group_key=None`` return {"overall": {metric: mean}}; with ``group_key="group"`` return
    {"ko->en": {...}, "en->en": {...}, ...} plus "overall". Also include "n" (query count) per group.
    """
    raise NotImplementedError
