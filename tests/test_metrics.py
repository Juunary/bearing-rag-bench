"""Hand-computed expectations for ragbench.metrics (linear-gain nDCG, strict recall)."""

import math

import pytest

from ragbench.metrics import aggregate, evaluate_query, mrr_at_k, ndcg_at_k, recall_at_k

RANKED_A = ["a", "b", "c", "d", "e", "f"]
GOLD_A = {"b": 2, "e": 1}          # b at rank 2, e at rank 5


# ----------------------------------------------------------------- recall@k

def test_recall_strict_fraction():
    assert recall_at_k(RANKED_A, GOLD_A, 5) == 1.0
    assert recall_at_k(RANKED_A, GOLD_A, 3) == 0.5
    assert recall_at_k(RANKED_A, GOLD_A, 1) == 0.0


def test_recall_three_relevant():
    ranked = ["y", "q", "x"]
    gold = {"x": 2, "y": 1, "z": 1}
    assert recall_at_k(ranked, gold, 2) == pytest.approx(1 / 3)
    assert recall_at_k(ranked, gold, 3) == pytest.approx(2 / 3)
    assert recall_at_k(ranked, gold, 10) == pytest.approx(2 / 3)   # z never retrieved


def test_recall_shorter_than_k():
    assert recall_at_k(["b"], GOLD_A, 5) == 0.5


# -------------------------------------------------------------------- mrr@k

def test_mrr_first_relevant_rank():
    assert mrr_at_k(RANKED_A, GOLD_A, 10) == 0.5            # first relevant is b at rank 2
    assert mrr_at_k(["e", "b"], GOLD_A, 10) == 1.0           # grade does not matter for MRR
    assert mrr_at_k(RANKED_A, GOLD_A, 1) == 0.0              # cut-off excludes rank 2


def test_mrr_nothing_relevant():
    assert mrr_at_k(["x", "y"], GOLD_A, 10) == 0.0


# ------------------------------------------------------------------- ndcg@k

def test_ndcg_linear_gain_case_a():
    # DCG  = 2/log2(3) + 1/log2(6) = 1.6487 ; IDCG = 2/log2(2) + 1/log2(3) = 2.6309
    assert ndcg_at_k(RANKED_A, GOLD_A, 10) == pytest.approx(0.626665, abs=1e-5)
    # only b (rank 2) inside the top 3
    assert ndcg_at_k(RANKED_A, GOLD_A, 3) == pytest.approx(0.479625, abs=1e-5)


def test_ndcg_rewards_grade_order():
    # e(1) at rank 1, b(2) at rank 2 -> worse than ideal order [2,1]
    assert ndcg_at_k(["e", "b"], GOLD_A, 10) == pytest.approx(0.859719, abs=1e-5)
    assert ndcg_at_k(["b", "e"], GOLD_A, 10) == pytest.approx(1.0)


def test_ndcg_three_relevant_one_missing():
    ranked = ["y", "q", "x"]
    gold = {"x": 2, "y": 1, "z": 1}
    # DCG = 1/log2(2) + 2/log2(4) = 2.0 ; IDCG = 2/1 + 1/log2(3) + 1/log2(4) = 3.1309
    assert ndcg_at_k(ranked, gold, 10) == pytest.approx(0.638788, abs=1e-5)


def test_ndcg_zero_when_nothing_relevant():
    assert ndcg_at_k(["x", "y"], GOLD_A, 10) == 0.0


def test_ndcg_idcg_truncated_at_k():
    # 3 relevant but k=1: IDCG uses only the best grade -> perfect hit at rank 1 gives 1.0
    assert ndcg_at_k(["x"], {"x": 2, "y": 1, "z": 1}, 1) == pytest.approx(1.0)


# --------------------------------------------------------------- edge cases

@pytest.mark.parametrize("fn", [recall_at_k, mrr_at_k, ndcg_at_k])
def test_empty_gold_raises(fn):
    with pytest.raises(ValueError):
        fn(RANKED_A, {}, 5)


# --------------------------------------------------------- evaluate / aggregate

def test_evaluate_query_keys_and_values():
    m = evaluate_query(RANKED_A, GOLD_A)
    assert set(m) == {"recall@5", "mrr@10", "ndcg@10"}
    assert m["recall@5"] == 1.0
    assert m["mrr@10"] == 0.5
    assert m["ndcg@10"] == pytest.approx(0.626665, abs=1e-5)


def test_aggregate_overall_and_groups():
    per_query = [
        {"qid": "q1", "group": "ko->ko", "metrics": {"recall@5": 1.0, "mrr@10": 1.0}},
        {"qid": "q2", "group": "ko->ko", "metrics": {"recall@5": 0.0, "mrr@10": 0.5}},
        {"qid": "q3", "group": "ko->en", "metrics": {"recall@5": 0.5, "mrr@10": 0.0}},
    ]
    overall = aggregate(per_query)
    assert overall["overall"]["recall@5"] == pytest.approx(0.5)
    assert overall["overall"]["mrr@10"] == pytest.approx(0.5)
    assert overall["overall"]["n"] == 3

    grouped = aggregate(per_query, group_key="group")
    assert grouped["ko->ko"]["recall@5"] == pytest.approx(0.5)
    assert grouped["ko->ko"]["mrr@10"] == pytest.approx(0.75)
    assert grouped["ko->ko"]["n"] == 2
    assert grouped["ko->en"]["recall@5"] == pytest.approx(0.5)
    assert grouped["ko->en"]["n"] == 1
    assert grouped["overall"]["n"] == 3
