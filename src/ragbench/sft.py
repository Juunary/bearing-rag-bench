"""Tokenisation and loss masking for supervised fine-tuning on chat data.

[EN]
- Role: turn (prompt messages, target answer) into token ids and tell the trainer which positions
  are the answer, so the loss is computed on the answer only (not on the long prompt).
- Method: the prompt ids come from the chat template with add_generation_prompt=True; the full ids
  come from the same template with the assistant answer appended. The answer span is what the full
  ids add after the prompt ids (the template's end-of-turn token included, so the model learns to
  stop). The prefix property (full ids start with the prompt ids) is asserted, because a template
  that changes earlier tokens would silently shift the mask.
- Memory: the trainer asks the model for logits of the last R+1 positions only (logits_to_keep), not
  for all ~2300 positions x 152k vocabulary; this is what makes training fit on a 12 GB card.
- Loss: token-level cross-entropy averaged over the answer tokens of one example.

[KO]
- 역할: (프롬프트 메시지, 목표 답변)을 토큰 ID로 바꾸고 어느 위치가 답변인지 알려 줘, 긴 프롬프트가 아니라
  답변에만 손실을 계산하게 한다.
- 방법: 프롬프트 ID는 chat template에 add_generation_prompt=True를 준 결과이고, 전체 ID는 같은 template에
  어시스턴트 답변을 붙인 결과다. 답변 구간은 전체 ID가 프롬프트 ID 뒤에 더한 부분이다(모델이 멈추는 법을
  배우도록 template의 턴 종료 토큰 포함). template이 앞쪽 토큰을 바꾸면 마스크가 조용히 어긋나므로 전체 ID가
  프롬프트 ID로 시작한다는 성질을 assert한다.
- 메모리: 학습기는 약 2300개 위치 x 15.2만 어휘 전체가 아니라 마지막 R+1개 위치의 로짓만 모델에 요청한다
  (logits_to_keep). 12GB GPU에서 학습이 되게 하는 핵심이다.
- 손실: 한 예시의 답변 토큰에 대한 토큰 단위 교차 엔트로피 평균.
"""

from __future__ import annotations

from typing import Any


def encode_example(tokenizer, messages: list[dict[str, str]], answer: str) -> tuple[list[int], int]:
    """Return (full token ids, number of answer tokens R). The answer occupies the last R positions."""
    prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True, return_dict=True)["input_ids"]
    full = tokenizer.apply_chat_template(messages + [{"role": "assistant", "content": answer}], tokenize=True, return_dict=True)["input_ids"]
    assert full[: len(prompt)] == prompt, "chat template changed earlier tokens when the answer was appended"
    # the template ends the turn with "<|im_end|>\n"; the trailing newline is not part of what the model must produce
    while full and tokenizer.decode(full[-1:]).strip() == "":
        full = full[:-1]
    r = len(full) - len(prompt)
    assert r > 0, "empty answer span"
    return full, r


def example_stats(examples: list[tuple[list[int], int]]) -> dict[str, Any]:
    n = len(examples)
    return {"n": n, "mean_tokens": sum(len(i) for i, _ in examples) / max(1, n), "max_tokens": max((len(i) for i, _ in examples), default=0),
            "mean_answer_tokens": sum(r for _, r in examples) / max(1, n)}
