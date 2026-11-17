import numpy as np

from ragbench.gaps import gap_table, leader_clusters


def unit(*v):
    v = np.array(v, dtype=float)
    return v / np.linalg.norm(v)


def test_leader_clusters_are_deterministic():
    vecs = np.stack([unit(1, 0), unit(0.95, 0.05), unit(0, 1), unit(0.05, 0.95), unit(1, 0.02)])
    assert leader_clusters(vecs, 0.9) == [[0, 1, 4], [2, 3]]


def test_gap_table_marks_existing_pages():
    items = [{"question": q, "source": "s", "reason": None} for q in ("a1", "a2", "b1")]
    qv = np.stack([unit(1, 0, 0), unit(0.98, 0.02, 0), unit(0, 0, 1)])
    pv = np.stack([unit(1, 0.1, 0), unit(0, 1, 0)])
    rows = gap_table(items, qv, ["page_a", "page_b"], pv, threshold=0.9, dense_min=0.55)
    assert [(r["size"], r["kind"]) for r in rows] == [(2, "page exists"), (1, "new page")]
    assert rows[0]["nearest_page"] == "page_a" and rows[0]["leader"] == "a1"
