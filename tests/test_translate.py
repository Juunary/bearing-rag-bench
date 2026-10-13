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
