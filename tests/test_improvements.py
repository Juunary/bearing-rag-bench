import json

import pytest

from ragbench.config import ExperimentConfig
from ragbench.retrieval.bm25_en import EnglishBM25Retriever, ExpandedQueryRetriever
from ragbench.retrieval.factory import _bm25, _index_set_id
from ragbench.retrieval.rerank import RerankRetriever
from ragbench.translate import expansion_messages


class FakeTr:
    """번역은 사전, 확장은 미리 정한 문자열을 돌려주는 가짜 번역기."""
    def __init__(self, expand_text="[1] bearing life\n[2] service life of a rolling bearing"):
        self.expand_text, self.expand_calls = expand_text, 0
    def translate(self, text, kind):
        return {"text": {"베어링 수명": "bearing life"}.get(text, text), "truncated": False, "seconds": 0.5}
    def expand(self, query, mode):
        self.expand_calls += 1
        return {"text": self.expand_text, "truncated": False, "seconds": 1.0}


CHUNKS = [{"chunk_id": "a#0", "text": "x"}, {"chunk_id": "b#0", "text": "x"}, {"chunk_id": "c#0", "text": "x"}]
EN = [{"chunk_id": "a#0", "text": "Bearing life depends on the load.", "translated": True, "truncated": False},
      {"chunk_id": "b#0", "text": "The service life of a rolling bearing is limited by fatigue.", "translated": True, "truncated": False},
      {"chunk_id": "c#0", "text": "Seals keep oil in.", "translated": False, "truncated": False}]


def en_retriever(tmp_path, tr):
    p = tmp_path / "en.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in EN), encoding="utf-8")
    r = EnglishBM25Retriever(tr, p)
    r.index(CHUNKS)
    return r


def test_expansion_prompts_name_the_mode_and_reject_unknown():
    assert "exactly two" in expansion_messages("q", "multi")[-1]["content"]
    assert "passage" in expansion_messages("q", "hyde")[-1]["content"]
    with pytest.raises(ValueError):
        expansion_messages("q", "other")


def test_multi_expansion_fuses_translation_and_variants(tmp_path):
    tr = FakeTr()
    r = ExpandedQueryRetriever(tr, en_retriever(tmp_path, tr), "multi")
    hits = r.search("베어링 수명", 3)
    ids = [h[0] for h in hits]
    assert set(ids[:2]) == {"a#0", "b#0"}                       # 번역은 a, 변형은 b에 닿아 둘 다 위로 올라온다
    extra = r.run_extra()
    assert extra["query_expansion_failed"] == 0 and extra["query_expansion_seconds_p50"] == 1.0
    assert extra["query_expansions"][0]["variants"] == ["bearing life", "service life of a rolling bearing"]


def test_multi_expansion_falls_back_to_translation_when_the_answer_is_malformed(tmp_path):
    tr = FakeTr(expand_text="Sure! Here are two versions.")
    r = ExpandedQueryRetriever(tr, en_retriever(tmp_path, tr), "multi")
    assert r.search("베어링 수명", 3)[0][0] == "a#0"
    assert r.run_extra()["query_expansion_failed"] == 1


def test_hyde_searches_translation_plus_passage(tmp_path):
    tr = FakeTr(expand_text="Rolling bearings fail by fatigue after a limited service life.")
    r = ExpandedQueryRetriever(tr, en_retriever(tmp_path, tr), "hyde")
    ids = [h[0] for h in r.search("베어링 수명", 3)]
    assert ids[0] == "b#0"                                      # 가상 문단의 어휘(fatigue, service life)가 b를 끌어올린다
    assert r.run_extra()["query_expansion_failed"] == 0


class FakeCE:
    model_name, revision = "fake-ce", "r"
    def __init__(self): self.seen = None
    def score(self, query, texts):
        self.seen = (query, texts)
        return [float(len(t)) for t in texts]                    # 긴 텍스트가 높은 점수


class FakeBase:
    name = "fake"
    def index(self, chunks): return {}
    def search(self, q, k): return [("a#0", 1.0), ("b#0", 0.9)][:k]


def test_rerank_in_english_reads_translated_chunks_and_query_and_records_the_pool(tmp_path):
    p = tmp_path / "en.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in EN), encoding="utf-8")
    ce = FakeCE()
    rr = RerankRetriever(FakeBase(), top_n=2, cross_encoder=ce, english_chunks_path=p, query_translator=FakeTr())
    rr.index(CHUNKS)
    out = rr.search("베어링 수명", 2)
    assert ce.seen[0] == "bearing life" and ce.seen[1][0].startswith("Bearing life depends")      # 영어 질의, 영어 청크
    assert [cid for cid, _ in out] == ["b#0", "a#0"] and rr.last_pool == ["a#0", "b#0"]
    assert rr.name.endswith("_en")


def test_factory_builds_the_requested_bm25_variants_and_separates_context_cache_keys():
    plain = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "bm25"}})
    assert type(_bm25(plain)).__name__ == "BM25Retriever"
    pivot = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "bm25", "bm25_english_pivot": True}})
    assert type(_bm25(pivot, FakeTr())).__name__ == "EnglishBM25Retriever"
    exp = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "bm25", "bm25_english_pivot": True, "query_expansion": "hyde"}})
    assert type(_bm25(exp, FakeTr())).__name__ == "ExpandedQueryRetriever"
    ctx = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "dense", "contextual_prefix": True}})
    assert _index_set_id(ctx) == _index_set_id(plain) + "_ctx"          # 접두사 텍스트의 임베딩 캐시는 따로
