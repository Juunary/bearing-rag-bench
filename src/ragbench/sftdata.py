"""Helpers for building the supervised fine-tuning set (stage 4): question prompts and quality filters.

[EN]
- Role: pure functions (no model calls) that decide which generated questions and answers may enter
  the training set, so the rules are unit-tested on CPU and the builder script stays small.
- Task being taught (decided 2026-10-12): citation completeness - every sentence of the answer ends
  with a valid citation of a chunk that was in the prompt, and the chunk the question came from is
  cited. The training answers are the base model's own best samples (self-distillation with
  rejection sampling), so the model is pushed toward behaviour it already shows only sometimes.
- Answer filter (all must hold): passes output validation (no refusal, valid ids, at least one
  citation); every sentence has a citation; 1-5 sentences; the source chunk is cited; the answer is
  in the question's language (Hangul present iff the question is Korean).
- Question filter: 8-200 characters, written in the requested language (script check), does not
  refer to "the passage", and is not too similar to any evaluation question (similarity is checked
  in the builder with the embedding model).
- Source chunks are never gold chunks of the evaluation set and are skipped when they are short or
  dominated by formula fragments.

[KO]
- 역할: 모델 호출이 없는 순수 함수로, 생성된 질문과 답변이 학습 세트에 들어갈 수 있는지 정한다. 규칙을
  CPU에서 단위 테스트하고 빌더 스크립트를 작게 유지한다.
- 가르치는 과제(2026-10-12 결정): 근거 인용 완결성. 답변의 모든 문장이 프롬프트에 있던 청크의 유효한 인용으로
  끝나고, 질문이 나온 출처 청크가 인용된다. 학습 답변은 기반 모델 자신의 최고 샘플(기각 샘플링을 쓴 자기 증류)이라
  모델이 가끔만 보이는 행동을 안정적으로 만들도록 민다.
- 답변 필터(모두 만족): 출력 검증 통과(거절 아님, 유효한 ID, 인용 1개 이상); 모든 문장에 인용; 1~5문장; 출처
  청크 인용; 질문 언어로 답함(한국어 질문일 때만 한글 포함).
- 질문 필터: 8~200자, 요청한 언어로 작성됨(문자 검사), "본문/passage"를 가리키지 않음, 평가 질문과 너무
  비슷하지 않음(유사도는 빌더에서 임베딩 모델로 검사).
- 출처 청크는 평가셋의 정답 청크가 아니어야 하고, 짧거나 수식 조각이 많은 청크는 건너뛴다.
"""

from __future__ import annotations

import re
from typing import Any

from ragbench.generation import CITE_RE, SENT_RE, parse_answer
from ragbench.validation import validate_answer

LANG_NAMES = {"ko": "Korean", "en": "English", "de": "German"}
QUESTION_SYSTEM = "You write test questions for a technical document search system."
_HANGUL = re.compile(r"[가-힣]")
_BAD_REFERENCE = re.compile(r"\b(the|this)\s+(passage|text|document|excerpt)\b|\b(der|dieser)\s+(Text|Abschnitt)\b|본문|이\s*글|위\s*글|해당\s*문서|주어진\s*(글|문서)", re.IGNORECASE)


def has_hangul(s: str) -> bool:
    return bool(_HANGUL.search(s))


def hangul_share(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    return sum(1 for c in letters if _HANGUL.match(c)) / len(letters) if letters else 0.0


def is_junk_chunk(chunk: dict[str, Any], min_tokens: int = 100, max_short_line_share: float = 0.2) -> bool:
    lines = [ln for ln in chunk["text"].split("\n") if ln.strip()]
    short = sum(1 for ln in lines if len(ln.strip()) <= 2)
    return chunk["n_tokens"] < min_tokens or (bool(lines) and short / len(lines) > max_short_line_share)


def question_messages(passage: str, lang: str) -> list[dict[str, str]]:
    user = (f"Passage:\n{passage}\n\nWrite ONE specific question in {LANG_NAMES[lang]} that can be answered using only this passage. "
            "The question must be self-contained: do not say 'the passage' or 'this text', and do not copy a full sentence from the passage. "
            "Output only the question.")
    return [{"role": "system", "content": QUESTION_SYSTEM}, {"role": "user", "content": user}]


def parse_question(text: str) -> str:
    for line in (text or "").splitlines():
        line = re.sub(r"^\s*(question|frage|질문)\s*[:：]\s*", "", line.strip(), flags=re.IGNORECASE).strip(" \"'“”「」*")
        if line:
            return line
    return ""


def question_ok(question: str, lang: str) -> tuple[bool, str | None]:
    if not 8 <= len(question) <= 200:
        return False, "length"
    if _BAD_REFERENCE.search(question):
        return False, "refers_to_passage"
    if lang == "ko" and hangul_share(question) < 0.3:
        return False, "language"
    if lang != "ko" and has_hangul(question):
        return False, "language"
    return True, None


def n_sentences(text: str) -> int:
    return len([s for s in SENT_RE.split(text.strip()) if s.strip()])


def answer_ok(text: str, context_ids: list[str], source_id: str, lang: str) -> bool:
    if not validate_answer(text, context_ids).ok:
        return False
    parsed = parse_answer(text, context_ids, {source_id})
    if parsed["sentence_coverage"] < 1.0 or not parsed["cites_gold"] or not CITE_RE.search(text):
        return False
    if not 1 <= n_sentences(text) <= 5:
        return False
    return hangul_share(text) >= 0.3 if lang == "ko" else not has_hangul(text)


def pick_answer(candidates: list[str], context_ids: list[str], source_id: str, lang: str) -> str | None:
    for c in candidates:
        if answer_ok(c, context_ids, source_id, lang):
            return c.strip()
    return None
