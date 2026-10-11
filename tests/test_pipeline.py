from ragbench.cache import LLMCache
from ragbench.pipeline import RAGPipeline
from ragbench.requestlog import RequestLogger
from ragbench.validation import SAFE_MESSAGES

CHUNKS = [{"chunk_id": "en_grease#2", "text": "Grease is semisolid."}, {"chunk_id": "de_schmierfett#1", "text": "Fett besteht aus Öl."},
          {"chunk_id": "ko_ball_bearing#4", "text": "케이지가 없으면 볼은 이탈한다."}]


class FakeRetriever:
    def __init__(self): self.calls = 0
    def search(self, q, k):
        self.calls += 1
        return [(c["chunk_id"], 1.0 - 0.1 * i) for i, c in enumerate(CHUNKS)][:k]


class FakeGenerator:
    model_name, revision = "fake", "rev1"
    def __init__(self, text): self.text, self.calls = text, 0
    def generate(self, messages, max_new_tokens=256):
        self.calls += 1
        return {"text": self.text, "prompt_tokens": 100, "completion_tokens": 10, "seconds": 0.5}


def make(tmp_path, text="Grease is semisolid [en_grease#2]."):
    gen, ret = FakeGenerator(text), FakeRetriever()
    pipe = RAGPipeline(ret, CHUNKS, gen, LLMCache(tmp_path / "c.sqlite"), RequestLogger(tmp_path / "log.jsonl"), context_k=3, config_id="t")
    return pipe, gen, ret


def test_grounded_answer_is_delivered_and_logged(tmp_path):
    pipe, gen, _ = make(tmp_path)
    r = pipe.answer("What is grease?", lang="en", request_id="r1")
    assert not r.blocked and r.answer == "Grease is semisolid [en_grease#2]." and r.context_ids == ["en_grease#2", "de_schmierfett#1", "ko_ball_bearing#4"]
    row = pipe.logger.read()[0]
    assert row["request_id"] == "r1" and row["prompt_tokens"] == 100 and row["cache_hit"] is False and row["blocked"] is False
    assert [x["chunk_id"] for x in row["retrieved"]][0] == "en_grease#2" and row["prompt"][1]["content"].endswith("Question: What is grease?")
    assert set(row["latency_ms"]) == {"retrieve", "generate", "total"} and row["model_revision"] == "rev1"


def test_second_identical_request_hits_cache_and_skips_the_model(tmp_path):
    pipe, gen, _ = make(tmp_path)
    a = pipe.answer("What is grease?", lang="en"); b = pipe.answer("What is grease?", lang="en")
    assert gen.calls == 1 and not a.cache_hit and b.cache_hit and a.answer == b.answer
    assert b.timings_ms["generate"] == 0.0
    assert [r["cache_hit"] for r in pipe.logger.read()] == [False, True]


def test_different_question_misses_the_cache(tmp_path):
    pipe, gen, _ = make(tmp_path)
    pipe.answer("What is grease?", lang="en"); pipe.answer("What is oil?", lang="en")
    assert gen.calls == 2


def test_ungrounded_answers_are_replaced_by_a_fixed_message_in_the_question_language(tmp_path):
    for text, reason in (("NO_ANSWER", "refusal_sentinel"), ("Grease is semisolid.", "no_citation"), ("x [en_grease#9].", "invalid_citation")):
        pipe, _, _ = make(tmp_path, text=text)
        pipe.cache = LLMCache(":memory:")
        r = pipe.answer("케이지 소재는?", request_id="b-" + reason)
        assert r.blocked and r.reason == reason and r.answer == SAFE_MESSAGES["ko"] and r.raw_answer == text
        assert pipe.logger.read()[-1]["raw_answer"] == text


def test_invalid_input_skips_retrieval_and_model(tmp_path):
    pipe, gen, ret = make(tmp_path)
    r = pipe.answer("   ", lang="de")
    assert r.blocked and r.reason == "empty_question" and ret.calls == 0 and gen.calls == 0
    assert pipe.logger.read()[0]["block_reason"] == "empty_question"
