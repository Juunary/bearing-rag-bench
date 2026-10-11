"""LLM-as-a-judge for RAG answers: faithfulness, answer relevance, context relevance, correctness.

[EN]
- Role: label each generated answer with four yes/no judgements using a local judge model, so the
  generation stage can be evaluated without a human for every answer (humans grade a small sample to
  check the judge).
- Dimensions (one prompt per dimension, so one judgement cannot leak into another):
  - faithfulness: is every factual statement of the answer supported by the passages it cites
    (all context passages if it cites none)?
  - answer_relevance: does the answer address the question (correctness not judged)?
  - context_relevance: do the five context passages contain the information needed for the question?
    Judged without the answer. Compared with the gold labels as a check on the judge itself.
  - correctness: does the answer agree with the reference evidence (the eval set's gold sentences)?
- Refusals (NO_ANSWER) are not judged on faithfulness, answer relevance or correctness (not
  applicable); context_relevance is still judged.
- Judge model (decided 2026-10-12): Qwen/Qwen3-8B, a different and larger model than the generator
  (Qwen3-4B-Instruct-2507) to reduce self-preference, split over two GPUs with accelerate, thinking
  mode off, greedy decoding. Same model family, so some shared bias remains.
- Output format: one sentence of reasoning, then "VERDICT: YES|NO". The last verdict line is parsed;
  anything else is recorded as unparsable (None) and excluded.
- Judge calls go through the SQLite cache (key includes the judge revision), so a run is resumable and
  repeated runs are identical.

[KO]
- 역할: 로컬 판정 모델로 생성된 답변마다 예/아니오 판정 4개를 붙여, 모든 답을 사람이 보지 않고도 생성
  단계를 평가한다(사람은 작은 표본을 채점해 판정 모델을 점검한다).
- 판정 항목(항목마다 프롬프트를 따로 써서 한 판정이 다른 판정에 새지 않게 함):
  - faithfulness(충실도): 답변의 모든 사실 진술이 인용한 청크로 뒷받침되는가(인용이 없으면 컨텍스트
    전체)?
  - answer_relevance(답변 관련성): 답이 질문이 묻는 것을 다루는가(정확성은 보지 않음)?
  - context_relevance(컨텍스트 관련성): 컨텍스트 5개 청크에 질문에 답할 정보가 있는가? 답변 없이 판정하며
    정답 라벨과 비교해 판정 모델 자체를 점검한다.
  - correctness(정확성): 답이 기준 근거(평가셋의 정답 문장)와 일치하는가?
- 거절(NO_ANSWER)은 충실도·답변 관련성·정확성 판정 대상이 아니다(해당 없음). 컨텍스트 관련성은 판정한다.
- 판정 모델(2026-10-12 결정): Qwen/Qwen3-8B. 자기 답변을 후하게 채점하는 편향을 줄이려고 생성기(Qwen3-4B-
  Instruct-2507)와 다른 더 큰 모델을 쓰며, accelerate로 GPU 2장에 나누고 생각 모드를 끄고 greedy로
  디코딩한다. 같은 모델 계열이라 일부 공통 편향은 남는다.
- 출력 형식: 한 문장 추론 뒤 "VERDICT: YES|NO". 마지막 판정 줄을 파싱하며 그 외는 파싱 불가(None)로
  기록하고 집계에서 뺀다.
- 판정 호출은 SQLite 캐시(키에 판정 모델 리비전 포함)를 거치므로 중단 후 재개할 수 있고 반복 실행 결과가
  같다.
"""

from __future__ import annotations

import re
from typing import Any

from ragbench.cache import LLMCache, make_key
from ragbench.generation import CITE_RE

DIMENSIONS = ("faithfulness", "answer_relevance", "context_relevance", "correctness")
JUDGE_PROMPT_VERSION = "judge_v1"

SYSTEM = "You are a strict, impartial evaluator of answers produced by a retrieval-augmented system. Follow the instructions exactly."
TASKS = {
    "faithfulness": ("Task: decide whether the Answer is faithful to the Passages. The Answer is faithful only if every factual "
                     "statement in it is supported by the Passages (stated or clearly implied). Ignore citation brackets and "
                     "wording differences. The Passages and the Answer may be in different languages."),
    "answer_relevance": ("Task: decide whether the Answer addresses the Question. Judge only whether it tries to answer what was "
                         "asked, not whether it is correct. An answer that only says the information is missing does not address "
                         "the Question."),
    "context_relevance": ("Task: decide whether the Passages together contain the information needed to answer the Question. "
                          "Judge only the Passages. The Passages may be in a different language than the Question."),
    "correctness": ("Task: decide whether the Answer is correct by comparing it with the Reference. The Reference is verified "
                    "evidence and may be in a different language than the Question. The Answer is correct if the facts it gives "
                    "for what the Question asks agree with the Reference and do not contradict it. It is incorrect if it gives "
                    "different facts, omits the requested fact, or only says the information is missing."),
}
FORMAT = "First write one short sentence of reasoning. Then on a new line write exactly `VERDICT: YES` or `VERDICT: NO`."
VERDICT_RE = re.compile(r"VERDICT:\s*(YES|NO)\b", re.IGNORECASE)


def parse_verdict(text: str) -> bool | None:
    found = VERDICT_RE.findall(text or "")
    return None if not found else found[-1].upper() == "YES"


def select_passages(answer: str, context_ids: list[str], by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Passages a faithfulness judgement is made against: those the answer cites (in context order), else all."""
    cited = {c for c in CITE_RE.findall(answer or "")}
    chosen = [i for i in context_ids if i in cited] or list(context_ids)
    return [by_id[i] for i in chosen]


def _passages(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{c['chunk_id']}] {c['text']}" for c in chunks)


def build_judge_messages(dimension: str, question: str, answer: str | None = None,
                         passages: list[dict[str, Any]] | None = None, references: list[str] | None = None) -> list[dict[str, str]]:
    if dimension not in TASKS:
        raise ValueError(f"unknown dimension {dimension!r}; choose from {DIMENSIONS}")
    parts = [f"Question: {question}"]
    if dimension in ("faithfulness", "context_relevance"):
        parts.append(f"Passages:\n\n{_passages(passages or [])}")
    if dimension == "correctness":
        parts.append("Reference:\n" + "\n".join(f"- {r}" for r in (references or [])))
    if dimension != "context_relevance":
        parts.append(f"Answer: {answer}")
    parts.append(f"{TASKS[dimension]}\n{FORMAT}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n\n".join(parts)}]


class Judge:
    """Qwen3-8B (or another chat model) split over the visible GPUs, greedy, thinking off, cached."""

    def __init__(self, model_name: str = "Qwen/Qwen3-8B", cache: LLMCache | None = None, max_gpu_gib: int = 10):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        from ragbench.embedding import hf_cached_revision

        self.model_name, self.cache = model_name, cache
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        n = torch.cuda.device_count()
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=torch.bfloat16, device_map="auto", max_memory={i: f"{max_gpu_gib}GiB" for i in range(n)}).eval()
        self.revision = hf_cached_revision(model_name)

    def ask(self, messages: list[dict[str, str]], max_new_tokens: int = 80) -> dict[str, Any]:
        import torch

        key = make_key(self.model_name, self.revision, messages, max_new_tokens, decoding="greedy-nothink")
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                return {**hit, "cached": True}
        enc = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                                 return_dict=True, enable_thinking=False).to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
        text = self.tokenizer.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        res = {"text": text, "prompt_tokens": int(enc["input_ids"].shape[1])}
        if self.cache is not None:
            self.cache.put(key, res)
        return {**res, "cached": False}
