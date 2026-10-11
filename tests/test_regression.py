import copy
import json
from pathlib import Path

import pytest

from ragbench.regression import compare, extract_baseline

REPO = Path(__file__).resolve().parents[1]


def retrieval_result(ranked_q1=("a", "b"), ndcg=0.5, extra_q=None):
    pq = [{"qid": "q1", "ranked": list(ranked_q1)}, {"qid": "q2", "ranked": ["c"]}]
    if extra_q:
        pq.append({"qid": extra_q, "ranked": ["z"]})
    return {"config": {"exp_id": "t"}, "per_query": pq, "metrics": {"overall": {"recall@5": 0.5, "mrr@10": 0.5, "ndcg@10": ndcg, "n": len(pq)}}}


def generation_result(answer="x [a#1]", cites=1.0, refused=0.0):
    return {"config": {"exp_id": "g"}, "per_query": [{"qid": "q1", "answer": answer}],
            "metrics": {"overall": {"refused": refused, "citations_valid": cites, "cites_gold": 0.5, "n": 1}}}


def test_identical_is_pass():
    base = extract_baseline(retrieval_result())
    assert compare(retrieval_result(), base).status == "PASS"


def test_changed_output_within_tolerance_is_warn():
    base = extract_baseline(retrieval_result())
    r = compare(retrieval_result(ranked_q1=("b", "a"), ndcg=0.49), base)
    assert r.status == "WARN" and any("1 of 2 outputs differ" in line for line in r.lines)


def test_improvement_is_warn_not_pass():
    base = extract_baseline(retrieval_result())
    assert compare(retrieval_result(ranked_q1=("b", "a"), ndcg=0.6), base).status == "WARN"


def test_drop_beyond_tolerance_fails():
    base = extract_baseline(retrieval_result())
    r = compare(retrieval_result(ranked_q1=("x",), ndcg=0.47), base)
    assert r.status == "FAIL" and "ndcg@10 fell" in r.lines[0]
    assert compare(retrieval_result(ndcg=0.48), base).status == "WARN"      # exactly at the tolerance is not a failure


def test_question_set_change_fails():
    base = extract_baseline(retrieval_result())
    assert compare(retrieval_result(extra_q="q3"), base).status == "FAIL"


def test_generation_refusal_rate_is_not_judged_but_citation_drop_is():
    base = extract_baseline(generation_result())
    assert compare(generation_result(answer="NO_ANSWER", refused=1.0), base).status == "WARN"
    assert compare(generation_result(answer="y", cites=0.9), base).status == "FAIL"


@pytest.mark.parametrize("path", sorted((REPO / "eval" / "baselines").glob("*.json")) or [None])
def test_committed_results_match_committed_baselines(path):
    """Guards against editing result files or code paths without accepting the change as a new baseline."""
    if path is None:
        pytest.skip("no baselines yet")
    base = json.loads(path.read_text(encoding="utf-8"))
    result = json.loads((REPO / "experiments" / "results" / f"{base['exp_id']}.json").read_text(encoding="utf-8"))
    assert compare(copy.deepcopy(result), base).status == "PASS"
