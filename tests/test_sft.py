import pytest

from ragbench.sft import encode_example

MSGS = [{"role": "system", "content": "Cite every sentence."}, {"role": "user", "content": "Context: [a#1] Grease.\n\nQuestion: What is grease?"}]
ANSWER = "Grease is semisolid [a#1]."


@pytest.fixture(scope="module")
def tok():
    from transformers import AutoTokenizer
    try:
        return AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Instruct-2507", local_files_only=True)
    except Exception:   # tokenizer not cached on this machine
        pytest.skip("Qwen3 tokenizer not available offline")


def test_answer_span_is_exactly_the_answer_plus_end_of_turn(tok):
    ids, r = encode_example(tok, MSGS, ANSWER)
    decoded = tok.decode(ids[-r:])
    assert decoded.startswith(ANSWER) and decoded.endswith("<|im_end|>")
    prompt = tok.apply_chat_template(MSGS, add_generation_prompt=True, tokenize=True, return_dict=True)["input_ids"]
    assert ids[: len(prompt)] == prompt and len(ids) == len(prompt) + r


def test_korean_answer_and_no_trailing_newline(tok):
    ids, r = encode_example(tok, MSGS, "케이지는 볼의 위치를 유지한다 [a#1].")
    assert tok.decode(ids[-r:]).rstrip().endswith("<|im_end|>") and tok.decode(ids[-1:]).strip() != ""
