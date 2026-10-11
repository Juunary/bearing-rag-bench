import pytest

from ragbench.judge import DIMENSIONS, build_judge_messages, parse_verdict, select_passages

BY_ID = {"a#1": {"chunk_id": "a#1", "text": "Alpha text."}, "b#2": {"chunk_id": "b#2", "text": "Beta text."}, "c#3": {"chunk_id": "c#3", "text": "Gamma."}}
CTX = ["a#1", "b#2", "c#3"]


@pytest.mark.parametrize("text,expected", [
    ("Supported by the passage.\nVERDICT: YES", True),
    ("Not supported.\nverdict: no", False),
    ("VERDICT: YES then later VERDICT: NO", False),       # the last verdict wins
    ("I think it is fine.", None),
    ("", None),
    (None, None),
])
def test_parse_verdict(text, expected):
    assert parse_verdict(text) is expected


def test_select_passages_prefers_cited_in_context_order():
    assert [p["chunk_id"] for p in select_passages("x [c#3] y [a#1]", CTX, BY_ID)] == ["a#1", "c#3"]
    assert [p["chunk_id"] for p in select_passages("no citation", CTX, BY_ID)] == CTX
    assert [p["chunk_id"] for p in select_passages("bad [z#9]", CTX, BY_ID)] == CTX     # unknown id -> all context


def test_dimension_prompts_contain_only_what_they_judge():
    ans, q = "An answer [a#1].", "What?"
    psg = [BY_ID["a#1"]]
    ctx = build_judge_messages("context_relevance", q, passages=psg)[1]["content"]
    assert "Passages:" in ctx and "Answer:" not in ctx and "Reference:" not in ctx
    fa = build_judge_messages("faithfulness", q, answer=ans, passages=psg)[1]["content"]
    assert "Passages:" in fa and "Answer: An answer" in fa and "Reference:" not in fa
    ar = build_judge_messages("answer_relevance", q, answer=ans)[1]["content"]
    assert "Passages:" not in ar and "Reference:" not in ar and "Answer:" in ar
    co = build_judge_messages("correctness", q, answer=ans, references=["Ref one.", "Ref two."])[1]["content"]
    assert "- Ref one.\n- Ref two." in co and "Passages:" not in co
    for m in (ctx, fa, ar, co):
        assert m.rstrip().endswith("`VERDICT: YES` or `VERDICT: NO`.")


def test_unknown_dimension():
    assert set(DIMENSIONS) == {"faithfulness", "answer_relevance", "context_relevance", "correctness"}
    with pytest.raises(ValueError):
        build_judge_messages("style", "q")
