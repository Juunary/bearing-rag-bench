import json

import pytest

from ragbench.retrieval.bm25_en import EnglishBM25Retriever
from ragbench.translate import clean_translation, translation_messages


# 프롬프트에 원문과 종류별 규칙이 들어가고, 잘못된 kind는 예외가 나는지
def test_messages_have_task_text_and_kind_specific_rules():
    q = translation_messages("구름 베어링이란?", "query")
    p = translation_messages("Wälzlager.\nZweite Zeile.", "passage")
    assert q[-1]["content"].endswith("구름 베어링이란?") and "already English" in q[-1]["content"]
    assert p[-1]["content"].endswith("Zweite Zeile.") and "line breaks" in p[-1]["content"]
    with pytest.raises(ValueError):
        translation_messages("x", "document")


# "Translation:" 머리말·따옴표 제거, None 입력 방어
def test_clean_translation():
    assert clean_translation('  Translation: "What is a rolling bearing?"\n', "query") == "What is a rolling bearing?"
    assert clean_translation("English: line1\nline2 ", "passage") == "line1\nline2"
    assert clean_translation(None, "query") == ""


# 모델 없이 CPU로 검증하기 위한 가짜 번역기 (고정 사전 + 고정 지연 2초)
class FakeTranslator:
    def translate(self, text, kind):
        return {"text": {"베어링 수명": "bearing life"}.get(text, text), "truncated": False, "seconds": 2.0}


def _chunks():
    return [{"chunk_id": "ko_a#0", "text": "베어링 수명은 하중에 따라 달라진다."}, {"chunk_id": "en_b#0", "text": "Seals keep oil in."}]


def _write(tmp_path, rows):
    p = tmp_path / "chunks_en.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


# 핵심 동작: 한국어 질의가 번역을 거쳐 한국어 청크의 영어본에 매칭되고, 반환 ID는 원래 청크 ID
def test_english_pivot_matches_across_languages(tmp_path):
    p = _write(tmp_path, [{"chunk_id": "ko_a#0", "text": "Bearing life depends on the load.", "translated": True, "truncated": False},
                          {"chunk_id": "en_b#0", "text": "Seals keep oil in.", "translated": False, "truncated": False}])
    r = EnglishBM25Retriever(FakeTranslator(), p)
    stats = r.index(_chunks())
    assert stats["chunks_translated"] == 1 and stats["chunks_truncated"] == 0
    hits = r.search("베어링 수명", 5)
    # 한국어 질의 -> "bearing life" -> 영어 번역본 -> 원래 ID ko_a#0
    assert hits[0][0] == "ko_a#0"                      # original chunk id, found through the English text
    extra = r.run_extra()
    assert extra["query_translation_seconds_p50"] == 2.0 and extra["query_translations_truncated"] == 0


# 번역이 빠진 청크가 있으면 색인 단계에서 실패해야 한다
def test_missing_translation_raises(tmp_path):
    p = _write(tmp_path, [{"chunk_id": "en_b#0", "text": "Seals keep oil in.", "translated": False, "truncated": False}])
    with pytest.raises(ValueError, match="no English translation"):
        EnglishBM25Retriever(FakeTranslator(), p).index(_chunks())


# 일반화한 피벗: 안쪽 검색기(dense 등)는 영어 텍스트로 색인되고 영어 질의로 검색된다
def test_english_pivot_wraps_any_retriever(tmp_path):
    from ragbench.retrieval.bm25_en import EnglishPivotRetriever

    class Recorder:
        name = "dense_exact"

        def index(self, chunks):
            self.texts = [c["text"] for c in chunks]
            return {}

        def search(self, query, k):
            self.query = query
            return [("ko_a#0", 1.0)]

    p = _write(tmp_path, [{"chunk_id": "ko_a#0", "text": "Bearing life depends on the load.", "translated": True, "truncated": False},
                          {"chunk_id": "en_b#0", "text": "Seals keep oil in.", "translated": False, "truncated": False}])
    inner = Recorder()
    r = EnglishPivotRetriever(FakeTranslator(), p, inner)
    assert r.name == "dense_exact_en"
    r.index(_chunks())
    assert inner.texts == ["Bearing life depends on the load.", "Seals keep oil in."]
    assert r.search("베어링 수명", 5) == [("ko_a#0", 1.0)] and inner.query == "bearing life"


# ---- docfirst: 번역 구간 정렬과 번호 문장 파싱 ----
from types import SimpleNamespace as NS

from ragbench.docfirst import anchor_to_english_span, group_lines, make_windows, numbered_text, parse_numbered, rebuild


def _spans(text, pieces):
    out, pos = [], 0
    for p in pieces:
        s = text.index(p, pos); pos = s + len(p)
        out.append(NS(text=p, start=s, end=pos, n_tokens=10))
    return out


def test_group_lines_and_windows():
    text = "A. B.\nC.\n\nD."
    spans = _spans(text, ["A.", "B.", "C.", "D."])
    lines = group_lines(text, spans)
    assert lines == [[0, 1], [2], [3]]                       # 같은 줄의 문장은 한 묶음
    assert make_windows(lines, spans, max_tokens=25) == [[[0, 1]], [[2], [3]]]   # 줄 단위로만 자른다


def test_parse_numbered_requires_exact_numbers():
    assert parse_numbered("[1] One.\n[2] Two.", 2) == ["One.", "Two."]
    assert parse_numbered("[1] One.\n[3] Three.", 2) is None      # 번호 건너뜀
    assert parse_numbered("[1] One.", 2) is None                  # 개수 부족
    assert parse_numbered("[1] One.\nextra comment\n[2] Two.", 2) is None   # 정렬을 못 믿는 줄
    assert numbered_text(["a  b", "c"]) == "[1] a b\n[2] c"


def test_rebuild_keeps_structure_and_alignment():
    text = "Eins. Zwei.\n\nDrei."
    spans = _spans(text, ["Eins.", "Zwei.", "Drei."])
    en, units = rebuild(text, spans, ["One.", "Two things.", "Three."])
    assert en == "One. Two things.\n\nThree."
    for u, t in zip(units, ["One.", "Two things.", "Three."]):
        assert en[u["e_start"]:u["e_end"]] == t
    # 두 번째 문장만 덮는 근거 문장 -> 영어 두 번째 문장 범위
    s, e = anchor_to_english_span(text.index("Zwei."), text.index("Zwei.") + 5, units)
    assert en[s:e] == "Two things."
    assert anchor_to_english_span(100, 110, units) is None


# 정답 연결: 번역된 문서는 정렬 단위로, 영어 문서는 기존 규칙으로 청크에 연결된다
def test_map_gold_docfirst_translated_and_english_docs():
    from ragbench.docfirst import map_gold_docfirst

    orig = "Eins. Zwei. Drei."
    spans = _spans(orig, ["Eins.", "Zwei.", "Drei."])
    en, units = rebuild(orig, spans, ["One thing.", "Two things.", "Three things."])
    docs = {"de_a": {"text": orig}, "en_b": {"text": "Seals keep oil in."}}
    chunks = [{"chunk_id": "de_a#0", "doc_id": "de_a", "char_start": 0, "char_end": en.index("Two")},          # 첫 문장만
              {"chunk_id": "de_a#1", "doc_id": "de_a", "char_start": en.index("Two"), "char_end": len(en)},   # 둘째·셋째 문장
              {"chunk_id": "en_b#0", "doc_id": "en_b", "char_start": 0, "char_end": 18}]
    gold = [{"doc_id": "de_a", "grade": 2, "anchor": "Zwei."}, {"doc_id": "en_b", "grade": 1, "anchor": "Seals keep oil in."}]
    assert map_gold_docfirst(gold, docs, {"de_a": units}, chunks) == {"de_a#1": 2, "en_b#0": 1}


# ---- 영어 질문 번역 건너뛰기 ----
class CountingTranslator(FakeTranslator):
    def __init__(self): self.calls = 0
    def translate(self, text, kind):
        self.calls += 1
        return super().translate(text, kind)


def test_skip_english_queries_only_translates_non_english(tmp_path):
    p = _write(tmp_path, [{"chunk_id": "ko_a#0", "text": "Bearing life depends on the load.", "translated": True, "truncated": False},
                          {"chunk_id": "en_b#0", "text": "Seals keep oil in.", "translated": False, "truncated": False}])
    tr = CountingTranslator()
    r = EnglishBM25Retriever(tr, p, skip_english=True)
    r.index(_chunks())
    assert r.search("What keeps oil in?", 5)[0][0] == "en_b#0" and tr.calls == 0       # 영어: 모델 호출 없음
    r.search("베어링 수명", 5)
    assert tr.calls == 1                                                                 # 한국어: 번역
    extra = r.run_extra()
    assert extra["query_translations_skipped"] == 1 and extra["query_translation_seconds_p50"] == 2.0


# ---- 용어집 힌트 ----
def test_glossary_hint_only_for_terms_in_the_text_and_most_specific_form():
    from ragbench.translate import glossary_hint, translation_messages

    entries = [{"en": "friction", "ko": ["마찰"], "de": ["Reibung"]},
               {"en": "rolling friction", "ko": ["구름 마찰"], "de": ["Rollreibung"]},
               {"en": "cage", "ko": ["케이지"], "de": ["Käfig"]},
               {"en": "grease", "ko": ["그리스"], "de": ["Schmierfett"]}]
    assert glossary_hint("구름 마찰과 케이지", entries) == "구름 마찰 = rolling friction; 케이지 = cage"   # 마찰은 구름 마찰에 포함되어 빠진다
    assert glossary_hint("Der Käfig und die Reibung", entries) == "Käfig = cage; Reibung = friction"       # 대소문자 무시
    assert glossary_hint("What is grease?", entries) == ""
    assert "Required term translations" in translation_messages("케이지?", "query", "케이지 = cage")[-1]["content"]
    assert "Required term" not in translation_messages("케이지?", "query")[-1]["content"]                  # 힌트가 없으면 예전 메시지 그대로


# 가짜 생성기: Generator와 같은 속성을 갖고 호출 횟수를 센다 (모델 로드 없음)
class FakeGenerator:
    def __init__(self, model_name, quantize_4bit=False, adapter=None):
        self.model_name, self.quantize_4bit, self.adapter = model_name, quantize_4bit, adapter
        self.device, self.revision, self.calls = "cuda:1", "rev1", 0

    def generate(self, messages, max_new_tokens=256):
        self.calls += 1
        return {"text": "What is bearing life?", "completion_tokens": 5, "seconds": 0.1}


# 번역기는 같은 모델(bf16, 어댑터 없음)인 생성기만 공유하고, 공유하면 그 생성기로 번역한다
def test_translator_shares_only_the_same_plain_model(tmp_path):
    from ragbench.translate import MODEL, Translator

    tr = Translator(tmp_path / "c.sqlite")
    assert not tr.use_generator(FakeGenerator("other/model"))
    assert not tr.use_generator(FakeGenerator(MODEL, quantize_4bit=True))
    assert not tr.use_generator(FakeGenerator(MODEL, adapter="adapters/x"))
    gen = FakeGenerator(MODEL)
    assert tr.use_generator(gen) and tr.device == "cuda:1"
    assert tr.translate("베어링 수명이란?", "query")["text"] == "What is bearing life?" and gen.calls == 1
    assert tr.translate("베어링 수명이란?", "query")["from_cache"] and gen.calls == 1


# share_translator_model은 검색기 안의 번역기(같은 객체는 한 번)를 모두 찾아 생성기를 공유시킨다
def test_share_translator_model_finds_every_translator(tmp_path):
    from ragbench.retrieval.bm25_en import EnglishPivotRetriever
    from ragbench.retrieval.factory import share_translator_model
    from ragbench.translate import MODEL, Translator

    class Fusion:
        name = "fusion"

        def __init__(self, retrievers):
            self.retrievers = retrievers

    p = _write(tmp_path, [{"chunk_id": "ko_a#0", "text": "Bearing life.", "translated": True, "truncated": False}])
    tr = Translator(tmp_path / "c.sqlite")
    tree = Fusion([EnglishBM25Retriever(tr, p), EnglishPivotRetriever(tr, p, Fusion([]))])
    gen = FakeGenerator(MODEL)
    assert share_translator_model(tree, gen) == 1 and tr._gen is gen
