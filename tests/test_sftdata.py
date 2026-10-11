from ragbench.sftdata import answer_ok, is_junk_chunk, parse_question, pick_answer, question_messages, question_ok

CTX = ["en_grease#2", "ko_ball_bearing#4", "de_schmierfett#1"]


def test_junk_chunks():
    ok = {"n_tokens": 300, "text": "A normal paragraph.\nAnother normal paragraph."}
    assert not is_junk_chunk(ok)
    assert is_junk_chunk({"n_tokens": 50, "text": "short"})
    formula = {"n_tokens": 300, "text": "\n".join(["R", "(", "L", ")", "=", "100"] * 4 + ["text line"])}
    assert is_junk_chunk(formula)


def test_question_prompt_and_parse():
    m = question_messages("Grease is semisolid.", "de")
    assert "in German" in m[1]["content"] and m[1]["content"].startswith("Passage:\nGrease is semisolid.")
    assert parse_question('\n"What is grease?"\nextra') == "What is grease?"
    assert parse_question("Question: Was ist Fett?") == "Was ist Fett?"
    assert parse_question("") == ""


def test_question_filters():
    assert question_ok("What is the dropping point of lithium grease?", "en") == (True, None)
    assert question_ok("short?", "en") == (False, "length")
    assert question_ok("What does the passage say about grease?", "en") == (False, "refers_to_passage")
    assert question_ok("리튬 그리스의 적점은 얼마인가요?", "ko") == (True, None)
    assert question_ok("What is grease made of?", "ko") == (False, "language")
    assert question_ok("그리스는 무엇으로 만드나요 grease?", "en") == (False, "language")


def test_answer_filter():
    good = "Grease is semisolid [en_grease#2]. It has a thickener [en_grease#2]."
    assert answer_ok(good, CTX, "en_grease#2", "en")
    assert not answer_ok("Grease is semisolid [en_grease#2]. It has a thickener.", CTX, "en_grease#2", "en")      # uncovered sentence
    assert not answer_ok("Grease is semisolid [de_schmierfett#1].", CTX, "en_grease#2", "en")                    # source chunk not cited
    assert not answer_ok("Grease is semisolid [en_grease#9].", CTX, "en_grease#2", "en")                        # fabricated id
    assert not answer_ok("NO_ANSWER", CTX, "en_grease#2", "en")
    assert not answer_ok("A [en_grease#2]. B [en_grease#2]. C [en_grease#2]. D [en_grease#2]. E [en_grease#2]. F [en_grease#2].", CTX, "en_grease#2", "en")
    assert answer_ok("케이지는 볼의 위치를 유지한다 [ko_ball_bearing#4].", CTX, "ko_ball_bearing#4", "ko")
    assert not answer_ok("The cage keeps the balls in place [ko_ball_bearing#4].", CTX, "ko_ball_bearing#4", "ko")  # wrong language for a Korean question


def test_pick_answer_takes_first_passing_candidate():
    cands = ["bad without citation.", "Good [en_grease#2].", "Also good [en_grease#2]."]
    assert pick_answer(cands, CTX, "en_grease#2", "en") == "Good [en_grease#2]."
    assert pick_answer(["nope"], CTX, "en_grease#2", "en") is None
