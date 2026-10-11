"""Input and output validation: block answers that are not grounded in the retrieved context.

[EN]
- Role: the last gate before an answer reaches a user. A blocked answer is replaced by a fixed
  message in the question's language, and the reason is logged.
- Output checks (decided 2026-10-12; order matters):
  1. empty answer.
  2. refusal sentinel NO_ANSWER (the model's own "no evidence" signal, see generation.py).
  3. natural-language refusal in the FIRST sentence (ko/en/de patterns). The refusal prompt does not
     always obey the sentinel (stage 3: one of the nine questions without evidence answered "not
     specified in the context" instead). Only the first sentence is inspected so that a normal
     answer that merely contains a negation later on is not blocked.
  4. a cited chunk id that was not in the prompt (a fabricated source).
  5. no citation at all (an unsupported claim).
- What this does NOT catch: a well-formed answer whose citation is real but does not support the
  claim (stage 3 example: a fork-seal question answered from a generic seal article). That needs
  faithfulness grading, not a rule.
- Input checks: empty, too long (> 1000 characters). Cheap, prevents wasted retrieval/LLM calls.
- guess_lang is a heuristic (Hangul -> ko, German words/umlauts -> de, else en) used only to pick the
  language of the fixed message when the caller does not pass one.

[KO]
- 역할: 답변이 사용자에게 나가기 전 마지막 관문. 차단된 답변은 질문 언어의 고정 문구로 바뀌고 사유가
  로그에 남는다.
- 출력 검사(2026-10-12 결정, 순서가 중요):
  1. 빈 답변.
  2. 거절 센티널 NO_ANSWER(모델이 스스로 보내는 "근거 없음" 신호, generation.py 참고).
  3. 첫 문장의 자연어 거절(ko/en/de 패턴). 거절 프롬프트도 센티널을 항상 따르지 않는다(3단계: 근거가 없던
     9개 중 1개가 센티널 대신 "문맥에 명시되지 않았다"고 답함). 일반 답변이 뒤에서 부정문을 쓰는 것만으로
     막히지 않도록 첫 문장만 본다.
  4. 프롬프트에 없던 청크 ID 인용(꾸며낸 출처).
  5. 인용이 전혀 없음(근거 없는 주장).
- 잡지 못하는 것: 인용은 실제지만 주장을 뒷받침하지 않는 정상 형식의 답(3단계 예: 포크 씰 질문에 일반
  씰 문서로 답함). 규칙이 아니라 충실도 채점이 필요하다.
- 입력 검사: 빈 입력, 너무 긴 입력(1000자 초과). 검색·LLM 호출 낭비를 막는다.
- guess_lang은 휴리스틱(한글 -> ko, 독일어 단어·움라우트 -> de, 그 외 en)이며 호출자가 언어를 주지 않을
  때 고정 문구의 언어를 고르는 용도다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ragbench.generation import CITE_RE, NO_ANSWER, SENT_RE

MAX_QUESTION_CHARS = 1000

SAFE_MESSAGES = {
    "ko": "제공된 문서에서 이 질문에 답할 근거를 찾지 못했습니다.",
    "en": "I could not find supporting evidence for this question in the provided documents.",
    "de": "Für diese Frage habe ich in den vorliegenden Dokumenten keine Belege gefunden.",
}
INVALID_INPUT_MESSAGES = {
    "ko": "질문을 입력해 주세요(1000자 이내).",
    "en": "Please enter a question (at most 1000 characters).",
    "de": "Bitte geben Sie eine Frage ein (höchstens 1000 Zeichen).",
}

_REFUSAL = [re.compile(p, re.IGNORECASE) for p in (
    # ko: "정보가 제공되어 있지 않습니다", "찾을 수 없습니다"
    r"(정보|내용|데이터|근거|언급|설명|수치|값)[^.。\[]{0,20}(되어 있지 않|되지 않|나와 있지 않|없)",
    r"(찾을|알|확인할|답할|판단할) 수 (가 )?없",
    # en
    r"\b(does not|doesn't|do not|did not|no)\s+(specify|contain|provide|mention|include|state|give|information)",
    r"\bnot\s+(specified|mentioned|provided|stated|given|available)\b",
    r"\b(cannot|can't|unable to)\s+(find|determine|answer)",
    # de
    r"\bnicht\s+(angegeben|erwähnt|enthalten|genannt|spezifiziert)",
    r"\bkeine\s+(Information|Informationen|Angabe|Angaben|Hinweis)",
    r"\bnichts\s+über\b",
    r"\bnicht\s+(beantworten|bestimmen)",
)]
_HANGUL = re.compile(r"[가-힣]")
_GERMAN = re.compile(r"[äöüßÄÖÜ]|\b(der|die|das|und|ist|wie|warum|welche[rsn]?|was|wann|wo|nicht|ein|eine|für|bei)\b", re.IGNORECASE)


def guess_lang(text: str) -> str:
    if _HANGUL.search(text):
        return "ko"
    if _GERMAN.search(text):
        return "de"
    return "en"


@dataclass
class Verdict:
    ok: bool
    reason: str | None = None     # None when ok


def validate_question(question: str) -> tuple[Verdict, str]:
    cleaned = (question or "").strip()
    if not cleaned:
        return Verdict(False, "empty_question"), cleaned
    if len(cleaned) > MAX_QUESTION_CHARS:
        return Verdict(False, "question_too_long"), cleaned
    return Verdict(True), cleaned


def first_sentence(text: str) -> str:
    parts = [s for s in SENT_RE.split(text.strip()) if s.strip()]
    return parts[0] if parts else ""


def validate_answer(text: str, provided_ids: list[str]) -> Verdict:
    stripped = (text or "").strip()
    if not stripped:
        return Verdict(False, "empty_answer")
    if stripped == NO_ANSWER or stripped.startswith(NO_ANSWER):
        return Verdict(False, "refusal_sentinel")
    head = first_sentence(stripped)
    if any(p.search(head) for p in _REFUSAL):
        return Verdict(False, "refusal_text")
    cited = CITE_RE.findall(stripped)
    if any(c not in set(provided_ids) for c in cited):
        return Verdict(False, "invalid_citation")
    if not cited:
        return Verdict(False, "no_citation")
    return Verdict(True)
