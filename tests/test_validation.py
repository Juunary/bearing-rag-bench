import pytest

from ragbench.validation import guess_lang, validate_answer, validate_question

IDS = ["en_grease#2", "de_schmierfett#1"]


def test_question_checks():
    assert validate_question("  What is grease? ")[0].ok
    assert validate_question("   ")[0].reason == "empty_question"
    assert validate_question("x" * 1001)[0].reason == "question_too_long"
    assert validate_question("x" * 1000)[0].ok


@pytest.mark.parametrize("text,reason", [
    ("", "empty_answer"),
    ("NO_ANSWER", "refusal_sentinel"),
    ("NO_ANSWER because the context is silent.", "refusal_sentinel"),
    ("Grease is semisolid [en_grease#9].", "invalid_citation"),
    ("Grease is semisolid.", "no_citation"),
])
def test_blocked_reasons(text, reason):
    v = validate_answer(text, IDS)
    assert not v.ok and v.reason == reason


@pytest.mark.parametrize("text", [
    "주어진 문맥에서는 케이지 소재에 대한 구체적인 정보가 제공되어 있지 않습니다. [ko_ball_bearing#8]에서는 기능을 설명합니다.",
    "The context does not specify an exact temperature. [en_grease#2] mentions lithium grease.",
    "Es wird in den gegebenen Kontexten nichts über die Anzahl der Nadellager angegeben [de_schmierfett#1].",
    "Die Temperatur ist im Kontext nicht angegeben [de_schmierfett#1].",
    "문서에서 정확한 값을 찾을 수 없습니다 [en_grease#2].",
])
def test_natural_language_refusals_are_blocked(text):
    v = validate_answer(text, IDS + ["ko_ball_bearing#8"])
    assert not v.ok and v.reason == "refusal_text"


@pytest.mark.parametrize("text", [
    "케이지는 하중을 받지 않으며 볼의 위치를 유지하는 역할만 한다 [en_grease#2].",   # negation in a normal answer
    "Grease is semisolid [en_grease#2]. The context does not give the dropping point.",   # negation only in sentence 2
    "Ein Schmierfett besteht aus Schmieröl und Eindicker [de_schmierfett#1].",
])
def test_normal_answers_pass(text):
    assert validate_answer(text, IDS).ok


def test_guess_lang():
    assert guess_lang("케이지 소재는?") == "ko"
    assert guess_lang("Warum verschleißt ein Lager?") == "de"
    assert guess_lang("What is grease?") == "en"
