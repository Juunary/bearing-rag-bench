import json

import numpy as np
import pytest

from ragbench.concepts import ConceptMatcher, alias_in_text, load_concepts
from ragbench.config import ExperimentConfig
from ragbench.retrieval.concept import ConceptCandidateRetriever
from ragbench.retrieval.dense import DenseRetriever
from ragbench.retrieval.factory import _rerank, build_retriever, translators_of
from ragbench.retrieval.rerank import RerankRetriever

PAGES = {
    "radial_shaft_seal": """---
id: radial_shaft_seal
type: concept
title: radial shaft seal
names:
  en: [oil seal, RWDR]
  ko: [오일 씰]
  de: [Wellendichtring]
related: [shaft_counterface]
docs: [en_radial_shaft_seal]
---
A radial shaft seal closes the gap between a rotating shaft and a housing with an elastomer lip.
""",
    "shaft_counterface": """---
id: shaft_counterface
type: concept
title: shaft counterface
names:
  en: [running surface]
  ko: []
  de: [Gegenlauffläche]
---
The shaft surface on which the sealing lip runs.
""",
    "shaft": """---
id: shaft
type: concept
title: shaft
names: {en: [], ko: [샤프트], de: [Welle]}
---
A rotating machine element.
""",
}


def bundle(tmp_path, pages=PAGES):
    d = tmp_path / "concepts"
    d.mkdir(parents=True)
    for k, v in pages.items():
        (d / f"{k}.md").write_text(v, encoding="utf-8")
    return d


# ---------------------------------------------------------------- loader

def test_loader_parses_pages_and_rejects_bad_bundles(tmp_path):
    cs = load_concepts(bundle(tmp_path))
    by = {c.id: c for c in cs}
    assert by["radial_shaft_seal"].title == "radial shaft seal" and by["radial_shaft_seal"].related == ["shaft_counterface"]
    assert ("en", "radial shaft seal") in by["radial_shaft_seal"].aliases() and ("de", "Wellendichtring") in by["radial_shaft_seal"].aliases()
    assert by["radial_shaft_seal"].description.startswith("A radial shaft seal")
    assert "oil seal" in by["radial_shaft_seal"].page_text()
    empty = tmp_path / "empty"
    empty.mkdir()
    assert load_concepts(empty) == []
    with pytest.raises(ValueError, match="related"):
        load_concepts(bundle(tmp_path / "a", {"x": "---\nid: x\ntype: concept\ntitle: x\nrelated: [nope]\n---\n"}))
    with pytest.raises(ValueError, match="file stem"):
        load_concepts(bundle(tmp_path / "b", {"y": "---\nid: z\ntype: concept\ntitle: z\n---\n"}))
    with pytest.raises(ValueError, match="type"):
        load_concepts(bundle(tmp_path / "c", {"y": "---\nid: y\ntype: note\ntitle: y\n---\n"}))
    with pytest.raises(ValueError, match="title or at least one alias"):
        load_concepts(bundle(tmp_path / "d", {"y": "---\nid: y\ntype: concept\n---\n"}))


# ---------------------------------------------------------------- alias matching

def test_alias_rules_by_language():
    assert alias_in_text("seal", "en", "Seals keep oil in.") and not alias_in_text("seal", "en", "the sealing lip")
    assert alias_in_text("RWDR", "en", "Der RWDR dichtet") and not alias_in_text("RWDR", "en", "rwdr")      # 약어는 대소문자 구분
    assert alias_in_text("오일 씰", "ko", "오일씰에서 누유가") and alias_in_text("오일 씰", "ko", "오일 씰(Oil seal)에서")
    assert alias_in_text("Wellendichtring", "de", "Radial-Wellendichtringe sind") and alias_in_text("Welle", "de", "Wellen")   # 독일어는 복합어라 부분 문자열


def test_matcher_prefers_longer_forms_and_uses_both_queries(tmp_path):
    m = ConceptMatcher(load_concepts(bundle(tmp_path)))
    # 한국어 질문에 괄호 영어가 있으면 그것도 잡힌다. "샤프트"는 "오일 씰"에 포함되지 않으므로 둘 다 매칭된다
    got = m.match("오일 씰(Oil seal)에서 샤프트 측 결함은?", "shaft-side defects of an oil seal")
    assert set(got.ids) == {"radial_shaft_seal", "shaft"} and got.related == ["shaft_counterface"]
    assert got.canonical_names == ["radial shaft seal", "shaft"]
    # "shaft seal"처럼 더 긴 매칭 형태에 포함된 "shaft"는 버린다 (영어 질의에서 radial shaft seal이 잡힘)
    got = m.match("Was ist ein Radial-Wellendichtring?", "What is a radial shaft seal?")
    assert got.ids == ["radial_shaft_seal"]
    assert m.match("볼 베어링의 수명은?", "ball bearing life").ids == []


class StubEmb:
    """키워드로 정해지는 단위 벡터: seal -> e0, bearing -> e1, 그 외 e2 (+ 작은 성분으로 순위 구분)."""
    model_name, revision, dim = "stub", "r", 3

    def encode(self, texts):
        out = np.zeros((len(texts), 3), dtype=np.float32)
        for i, t in enumerate(texts):
            t = t.lower()
            out[i] = [1.0, 0.0, 0.0] if "seal" in t else [0.0, 1.0, 0.0] if "bearing" in t else [0.0, 0.0, 1.0]
            if "lip" in t:
                out[i] = [0.9, 0.0, np.sqrt(1 - 0.81)]
        return out

    def encode_chunks_cached(self, chunks, chunk_set_id):
        return self.encode([c["text"] for c in chunks]), {"cached": False}


def test_dense_matching_is_a_fallback_with_threshold(tmp_path):
    cs = load_concepts(bundle(tmp_path))
    m = ConceptMatcher(cs, embedder=StubEmb(), dense_top=1, dense_min=0.85)
    m.index()
    q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    got = m.match("leakage of the lip", "leakage of the lip", q).dense                 # 별칭 없음 -> dense (페이지에 lip이 있어 0.9)
    assert len(got) == 1 and got[0][0] == "radial_shaft_seal" and got[0][1] > 0.85
    assert m.match("오일 씰 누유", "oil seal leakage", q).dense == []                 # 별칭 있음 -> dense 생략
    assert m.match("x", "x", np.array([0.0, 1.0, 0.0], dtype=np.float32)).ids == []    # 임계값 미달 (어느 페이지도 bearing 쪽이 아님)


# ---------------------------------------------------------------- candidate retriever

CHUNKS = [{"chunk_id": "a#0", "text": "Radial-Wellendichtringe laufen auf der Welle."},
          {"chunk_id": "b#0", "text": "볼 베어링의 수명은 하중에 달려 있다."},
          {"chunk_id": "c#0", "text": "Die Gegenlauffläche muss drallfrei sein."},
          {"chunk_id": "d#0", "text": "Grease thickener."}]
EN = [{"chunk_id": "a#0", "text": "Radial shaft seals run on the shaft.", "translated": True, "truncated": False},
      {"chunk_id": "b#0", "text": "Ball bearing life depends on the load.", "translated": True, "truncated": False},
      {"chunk_id": "c#0", "text": "The running surface must be lead-free; the sealing lip rides on it.", "translated": True, "truncated": False},
      {"chunk_id": "d#0", "text": "Grease thickener.", "translated": False, "truncated": False}]


class FakeTr:
    def __init__(self):
        self.calls = 0

    def translate(self, text, kind):
        self.calls += 1
        return {"text": {"오일 씰 누유": "oil seal leakage", "그리스": "grease"}.get(text, text), "truncated": False, "seconds": 0.1}


def concept_retriever(tmp_path, top_n=10):
    p = tmp_path / "en.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r) for r in EN), encoding="utf-8")
    dense = DenseRetriever(embedder=StubEmb(), exact=True)
    dense.index([{**c, "text": e["text"]} for c, e in zip(CHUNKS, EN)])
    # dense_top=0: 별칭 매칭만 (dense 대체 매칭은 위 matcher 테스트에서 따로 본다)
    r = ConceptCandidateRetriever(load_concepts(bundle(tmp_path)), dense, FakeTr(), p, top_n=top_n, dense_top=0, bundle="t")
    stats = r.index(CHUNKS)
    return r, stats


def test_candidates_come_only_from_matched_concepts_primary_first(tmp_path):
    r, stats = concept_retriever(tmp_path)
    # 원문(독일어 Wellendichtring)과 영어(radial shaft seal) 양쪽에서 청크가 개념에 붙는다
    assert r.chunk_sets["radial_shaft_seal"] == {"a#0"} and r.chunk_sets["shaft_counterface"] == {"c#0"}
    assert stats["chunks_per_concept"]["shaft"] >= 1 and stats["n_concepts"] == 3
    hits = r.search("오일 씰 누유", 10)
    ids = [h[0] for h in hits]
    assert ids[0] == "a#0" and "c#0" in ids and "b#0" not in ids          # 주 개념 청크가 먼저, 관련 개념 청크가 뒤
    assert r.augment_terms() == ["radial shaft seal"]
    assert r.search("그리스", 10) == [] and r.augment_terms() == []          # 매칭 없음
    extra = r.run_extra()
    assert extra["concept_queries"] == 2 and extra["concept_queries_matched"] == 1 and extra["concept_queries_alias"] == 1
    r2, _ = concept_retriever(tmp_path / "n", top_n=1)
    assert len(r2.search("오일 씰 누유", 10)) == 1


# ---------------------------------------------------------------- reranker extension

class FakeCE:
    model_name, revision = "fake-ce", "r"

    def __init__(self):
        self.seen = None

    def score(self, query, texts):
        self.seen = (query, texts)
        return [float(len(t)) for t in texts]


class FakeBase:
    name = "fake"

    def index(self, chunks):
        return {}

    def search(self, q, k):
        return [("b#0", 1.0), ("d#0", 0.9)][:k]


def test_reranker_pool_extension_and_query_augmentation(tmp_path):
    concept, _ = concept_retriever(tmp_path)
    ce = FakeCE()
    rr = RerankRetriever(FakeBase(), top_n=2, cross_encoder=ce, query_translator=FakeTr(), pool_extra=concept, pool_extra_n=10, query_augment=concept)
    rr.index(CHUNKS)
    rr.search("오일 씰 누유", 4)
    assert rr.last_pool[:2] == ["b#0", "d#0"] and set(rr.last_pool_added) == {"a#0", "c#0"}
    assert ce.seen[0] == "oil seal leakage (radial shaft seal)" and rr.last_concept["ids"] == ["radial_shaft_seal"]
    assert rr.name.endswith("_cpool10_cq")
    # 매칭이 없으면 후보·질의가 원래 리랭커와 같다
    plain = RerankRetriever(FakeBase(), top_n=2, cross_encoder=FakeCE(), query_translator=FakeTr())
    plain.index(CHUNKS)
    assert rr.search("그리스", 4) == plain.search("그리스", 4) and rr.last_pool == plain.last_pool and rr.last_ce_query == "grease"
    assert rr.last_concept["pool_added"] == [] and RerankRetriever(FakeBase(), top_n=2, cross_encoder=FakeCE()).last_concept is None


# ---------------------------------------------------------------- factory / config

def test_factory_sets_pool_and_augment_by_mode_and_validates(tmp_path, monkeypatch):
    monkeypatch.setattr("ragbench.retrieval.rerank.CrossEncoder", lambda model_name: FakeCE())   # 실제 리랭커 모델을 올리지 않는다
    concept, _ = concept_retriever(tmp_path)
    base = {"method": "hybrid_rerank", "rerank_model": "BAAI/bge-reranker-v2-m3", "rerank_text": "english", "concept_bundle": "data/concepts"}
    for mode, pool, aug in (("pool", True, False), ("pool_query", True, True), ("rrf_query", False, True)):
        cfg = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {**base, "concept_mode": mode}})
        rr = _rerank(cfg, FakeBase(), FakeTr(), concept)
        assert (rr.pool_extra is not None) == pool and (rr.query_augment is not None) == aug
    with pytest.raises(ValueError, match="concept_bundle"):
        build_retriever(ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "hybrid_rerank", "concept_mode": "pool"}}))
    rr = _rerank(ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {**base, "concept_mode": "pool"}}), FakeBase(), FakeTr(), concept)
    assert [type(t).__name__ for t in translators_of(rr)] == ["FakeTr", "FakeTr"]      # 리랭커 번역기 + pool_extra 번역기


def test_config_roundtrip_keeps_concept_fields(tmp_path):
    cfg = ExperimentConfig(exp_id="t")
    cfg.retrieval.concept_bundle, cfg.retrieval.concept_mode, cfg.retrieval.concept_pool_n = "data/concepts", "pool_query", 7
    p = tmp_path / "c.json"
    p.write_text(json.dumps(cfg.to_dict()), encoding="utf-8")
    assert ExperimentConfig.load(p) == cfg


def test_run_extra_reaches_pool_extra():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("run_retrieval", Path(__file__).resolve().parents[1] / "experiments" / "run_retrieval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class R:
        def __init__(self, name, extra, **kids):
            self.name, self._extra = name, extra
            for k, v in kids.items():
                setattr(self, k, v)

        def run_extra(self):
            return self._extra

    top = R("rr", {"a": 1}, base=R("rrf", {"b": 2}, retrievers=[R("x", {"c": 3})]), pool_extra=R("concept", {"concept_n": 4}))
    assert mod._run_extra(top) == {"a": 1, "b": 2, "c": 3, "concept_n": 4}
