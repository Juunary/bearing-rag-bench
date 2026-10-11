"""Answer generation from retrieved chunks with a local instruction-tuned model (plain transformers).

[EN]
- Role: turn (question, retrieved chunks) into a chat prompt, generate a grounded answer, and parse
  the answer for citations and refusals.
- Model (decided 2026-10-12): Qwen/Qwen3-4B-Instruct-2507, local, bf16 (7.5 GiB on one 12 GB GPU).
  Chosen because it is Apache-2.0, not gated, multilingual, and fits the GPU without quantization.
  No external API is used (no data leaves the machine).
- Prompts are versioned strings so a result file records exactly which wording produced it:
  - cite_v1: answer only from the context and cite the passage id in square brackets after every
    sentence.
  - cite_refuse_v1: cite_v1 plus "if the context lacks the information output exactly NO_ANSWER".
    A fixed sentinel is language independent and can be checked by code (input/output validation in
    stage 3.5 maps it to a user-facing message).
- Instructions are written in English (the model follows them most reliably) and the answer must be
  in the question's language.
- Decoding is greedy (do_sample=False, batch size 1): the same input gives the same answer, which
  caching and regression tests need.
- Context order = retrieval rank (best first). Each passage is prefixed with its chunk id, e.g.
  [de_waelzlager#5], so the model can cite it and code can check the citation.

[KO]
- 역할: (질문, 검색된 청크)로 채팅 프롬프트를 만들고, 근거 기반 답변을 생성하고, 답변에서 인용과 거절을
  파싱한다.
- 모델(2026-10-12 결정): Qwen/Qwen3-4B-Instruct-2507, 로컬, bf16(12GB GPU 한 장에서 7.5GiB). Apache-2.0,
  승인 불필요, 다국어, 양자화 없이 GPU에 올라간다는 이유. 외부 API를 쓰지 않아 데이터가 밖으로 나가지 않는다.
- 프롬프트는 버전이 붙은 문자열이라 결과 파일에 어떤 문구가 답을 만들었는지 정확히 남는다.
  - cite_v1: 컨텍스트에서만 답하고 모든 문장 뒤에 근거 청크 ID를 [ ]로 인용.
  - cite_refuse_v1: cite_v1에 "컨텍스트에 정보가 없으면 정확히 NO_ANSWER만 출력"을 더한다. 고정 문자열은
    언어와 무관하고 코드로 검사할 수 있다(3.5단계 입출력 검증이 사용자용 문구로 바꾼다).
- 지시문은 영어로 쓰고(모델이 가장 안정적으로 따름) 답변은 질문 언어로 하게 했다.
- 디코딩은 greedy(do_sample=False, 배치 1): 같은 입력이면 같은 답이 나와 캐시와 회귀 테스트가 가능하다.
- 컨텍스트 순서 = 검색 순위(좋은 순). 각 문단 앞에 [de_waelzlager#5] 같은 청크 ID를 붙여 모델이 인용하고
  코드가 인용을 검증할 수 있게 한다.
"""

from __future__ import annotations

import re
import time
from typing import Any

NO_ANSWER = "NO_ANSWER"
CITE_RE = re.compile(r"\[([A-Za-z0-9_]+#\d+)\]")
SENT_RE = re.compile(r"(?<=[.!?。])\s+")

_BASE = (
    "You are a technical assistant for bearings and automotive parts. "
    "Answer the question using ONLY the context passages below. "
    "After every sentence, cite the id of the passage that supports it in square brackets, "
    "for example [en_grease#2]. "
    "Answer in the same language as the question, in at most four sentences."
)
PROMPTS: dict[str, str] = {
    "cite_v1": _BASE,
    "cite_refuse_v1": _BASE + f" If the context does not contain the information needed to answer, output exactly {NO_ANSWER} and nothing else.",
}


def format_context(chunks: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{c['chunk_id']}] {c['text']}" for c in chunks)


def build_messages(prompt_version: str, question: str, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    if prompt_version not in PROMPTS:
        raise ValueError(f"unknown prompt_version {prompt_version!r}; choose from {sorted(PROMPTS)}")
    user = f"Context:\n\n{format_context(chunks)}\n\nQuestion: {question}"
    return [{"role": "system", "content": PROMPTS[prompt_version]}, {"role": "user", "content": user}]


def parse_answer(text: str, provided_ids: list[str], gold_ids: set[str] | list[str] = ()) -> dict[str, Any]:
    """Machine-checkable properties of an answer.

    refused: the answer is exactly the sentinel. cited: ids in order of appearance.
    citations_valid: at least one citation and every cited id was in the prompt.
    cites_gold: some cited id is a gold chunk. sentence_coverage: share of sentences with a citation.
    """
    stripped = text.strip()
    refused = stripped == NO_ANSWER
    cited = CITE_RE.findall(text)
    provided = set(provided_ids)
    sentences = [s for s in SENT_RE.split(stripped) if s.strip()] if not refused else []
    covered = sum(1 for s in sentences if CITE_RE.search(s))
    return {
        "refused": refused,
        "cited": cited,
        "has_citation": bool(cited),
        "citations_valid": bool(cited) and all(c in provided for c in cited),
        "cites_gold": any(c in set(gold_ids) for c in cited),
        "sentence_coverage": (covered / len(sentences)) if sentences else 0.0,
    }


class Generator:
    """Local causal LM, greedy decoding, one prompt at a time."""

    def __init__(self, model_name: str, device: str = "cuda:0"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        from ragbench.embedding import hf_cached_revision

        self.model_name, self.device = model_name, device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to(device).eval()
        self.revision = hf_cached_revision(model_name)

    def generate(self, messages: list[dict[str, str]], max_new_tokens: int = 256) -> dict[str, Any]:
        import torch

        enc = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
        ).to(self.device)
        if self.device.startswith("cuda"):
            torch.cuda.synchronize(self.device)
        t0 = time.perf_counter()
        with torch.no_grad():
            out = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
        if self.device.startswith("cuda"):
            torch.cuda.synchronize(self.device)
        seconds = time.perf_counter() - t0
        new = out[0][enc["input_ids"].shape[1]:]
        return {
            "text": self.tokenizer.decode(new, skip_special_tokens=True).strip(),
            "prompt_tokens": int(enc["input_ids"].shape[1]),
            "completion_tokens": int(len(new)),
            "seconds": seconds,
        }
