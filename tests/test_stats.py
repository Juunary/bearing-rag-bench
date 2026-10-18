import numpy as np

from ragbench.stats import bootstrap_ci, compare, sign_test_p


def test_iid_matches_the_original_analysis_convention():
    d = np.array([0.1, -0.2, 0.3, 0.0, 0.4, 0.2])
    rng = np.random.default_rng(42)
    ref = d[rng.integers(0, len(d), size=(10000, len(d)))].mean(axis=1)
    assert bootstrap_ci(d) == (float(np.percentile(ref, 2.5)), float(np.percentile(ref, 97.5)))


def test_cluster_ci_is_wider_when_questions_of_a_document_move_together():
    # 문서 4개, 문서 안 질문은 같은 부호로 움직인다 -> 군집 CI가 iid CI보다 넓어야 한다
    d = np.array([0.5, 0.5, 0.5, 0.5, -0.4, -0.4, -0.4, -0.4, 0.3, 0.3, 0.3, 0.3, -0.1, -0.1, -0.1, -0.1])
    docs = [f"d{i // 4}" for i in range(16)]
    lo_i, hi_i = bootstrap_ci(d)
    lo_c, hi_c = bootstrap_ci(d, docs)
    assert (hi_c - lo_c) > (hi_i - lo_i)


def test_cluster_ci_with_one_question_per_document_is_close_to_iid():
    d = np.linspace(-0.3, 0.5, 40)
    lo_i, hi_i = bootstrap_ci(d)
    lo_c, hi_c = bootstrap_ci(d, [f"q{i}" for i in range(40)])
    assert abs(lo_i - lo_c) < 0.03 and abs(hi_i - hi_c) < 0.03


def test_sign_test():
    assert sign_test_p(np.zeros(5)) == 1.0
    assert abs(sign_test_p(np.array([1.0] * 17 + [-1.0] * 6 + [0.0] * 22)) - 0.0347) < 0.001    # 앞서 손계산한 17/6 -> 0.035


def test_compare_reports_counts_and_both_cis():
    d = np.array([0.2, 0.0, -0.1, 0.3])
    out = compare(d, ["a", "a", "b", "b"])
    assert (out["better"], out["worse"], out["tie"]) == (2, 1, 1) and out["n_clusters"] == 2 and "ci_cluster" in out
