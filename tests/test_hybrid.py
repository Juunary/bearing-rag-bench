from ragbench.retrieval.hybrid import RRFRetriever


class Fake:
    def __init__(self, name, ranking):
        self.name, self.ranking = name, ranking
    def index(self, chunks):
        return {}
    def search(self, q, k):
        return [(c, 1.0 / (i + 1)) for i, c in enumerate(self.ranking[:k])]


def test_rrf_scores_and_order():
    a = Fake("a", ["x", "y", "z"])
    b = Fake("b", ["y", "w"])
    r = RRFRetriever([a, b], rrf_k=60, candidates=10)
    hits = dict(r.search("q", 10))
    # y: rank 2 in a, rank 1 in b
    assert abs(hits["y"] - (1 / 62 + 1 / 61)) < 1e-12
    assert abs(hits["x"] - 1 / 61) < 1e-12
    assert abs(hits["w"] - 1 / 62) < 1e-12
    order = [c for c, _ in r.search("q", 10)]
    assert order[0] == "y" and order[1] == "x"
    assert r.last_provenance["y"] == {"a": 2, "b": 1}


def test_rrf_truncates_to_k():
    r = RRFRetriever([Fake("a", list("abcdef"))], rrf_k=60, candidates=10)
    assert len(r.search("q", 2)) == 2
