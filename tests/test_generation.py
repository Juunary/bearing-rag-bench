import pytest

from ragbench.generation import NO_ANSWER, PROMPTS, build_messages, format_context, parse_answer

CH = [{"chunk_id": "en_grease#2", "text": "Grease is semisolid."}, {"chunk_id": "de_schmierfett#1", "text": "Fett besteht aus Öl."}]


def test_format_context_prefixes_ids_in_order():
    assert format_context(CH) == "[en_grease#2] Grease is semisolid.\n\n[de_schmierfett#1] Fett besteht aus Öl."


def test_build_messages_versions_differ_only_by_refusal_rule():
    a = build_messages("cite_v1", "What is grease?", CH)
    b = build_messages("cite_refuse_v1", "What is grease?", CH)
    assert a[1] == b[1]
    assert NO_ANSWER not in a[0]["content"] and NO_ANSWER in b[0]["content"]
    assert a[1]["content"].endswith("Question: What is grease?")


def test_unknown_prompt_version_raises():
    with pytest.raises(ValueError):
        build_messages("nope", "q", CH)
    assert set(PROMPTS) == {"cite_v1", "cite_refuse_v1"}


def test_parse_valid_citations_and_gold():
    r = parse_answer("Grease is semisolid [en_grease#2]. It contains oil [de_schmierfett#1].", ["en_grease#2", "de_schmierfett#1"], {"en_grease#2"})
    assert r["citations_valid"] and r["cites_gold"] and not r["refused"]
    assert r["cited"] == ["en_grease#2", "de_schmierfett#1"]
    assert r["sentence_coverage"] == 1.0


def test_parse_invalid_citation_and_partial_coverage():
    r = parse_answer("A claim [en_grease#9]. Another claim without a source.", ["en_grease#2"], {"en_grease#2"})
    assert r["has_citation"] and not r["citations_valid"] and not r["cites_gold"]
    assert r["sentence_coverage"] == 0.5


def test_parse_refusal_sentinel_only_when_exact():
    assert parse_answer(" NO_ANSWER \n", ["a#1"])["refused"]
    assert not parse_answer("NO_ANSWER because the context is silent.", ["a#1"])["refused"]
    assert parse_answer(NO_ANSWER, ["a#1"])["sentence_coverage"] == 0.0


def test_parse_no_citation():
    r = parse_answer("Plain answer.", ["a#1"])
    assert not r["has_citation"] and not r["citations_valid"] and r["sentence_coverage"] == 0.0
