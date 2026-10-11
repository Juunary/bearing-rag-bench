"""Retrieval metrics: Recall@k, MRR@k, nDCG@k and grouped aggregation.

Conventions (decided 2026-10-11, keep README in sync):
- ``ranked``: list of chunk ids in the order the retriever returned them (best first).
- ``gold``: dict chunk_id -> grade. grade 2 = core evidence, 1 = supporting evidence.
  Every id in ``gold`` is "relevant" for Recall/MRR regardless of grade.
- Recall@k is strict recall: |relevant ids in ranked[:k]| / |relevant ids|.
- MRR@k: 1 / (1-based rank of the first relevant id) if it occurs within the top k, else 0.
- nDCG@k uses LINEAR gain: DCG = sum_i grade(ranked[i]) / log2(i + 1), i is the 1-based rank.
  IDCG is the DCG of the gold grades sorted descending (truncated at k).
  (The alternative exponential gain (2**grade - 1) would weight core evidence 3:1 instead of 2:1;
  we keep linear so it is easy to hand-compute. trec_eval also uses linear gain.)
- Empty ``gold`` is a data error: raise ValueError rather than returning 0 silently.
- A ``ranked`` list shorter than k is fine.

TODO(user): implement the four functions below. Tests: tests/test_metrics.py
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
