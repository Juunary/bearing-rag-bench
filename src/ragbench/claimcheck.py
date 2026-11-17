"""Claim check: is every sentence of an answer supported by the passages it cites?

[EN]
- Role: output validation (validation.validate_answer) checks the form of an answer: a refusal, citations present,
  cited ids among the context. A fluent answer that cites a real passage but says something the passage does not say
  passes it (graded examples: a torsional vibration question answered with needle roller bearings, electrical
  fluting explained as fretting). This module checks the content, sentence by sentence.
- Splitting: sentences by generation.SENT_RE; a fragment that is only citation marks ("... . [en_x#1]") is attached to
  the sentence before it. Citation marks are removed from the statement the checker reads.
- Verdict per sentence:
  - no citation of its own -> checked against the passages cited elsewhere in the answer ("inherited"; all context
    passages if the answer cites none), or unsupported unchecked with strict=True ("no_citation");
  - a cited id that is not a context passage -> unsupported ("unknown_citation");
  - otherwise the checker model reads only the cited passages and the statement and answers SUPPORTED or
    NOT_SUPPORTED (prompt claim_v1, greedy, at most 8 new tokens); an unparsable reply is None (not counted).
- Model: the serving generator (Qwen3-4B-Instruct-2507) is reused, so no extra GPU memory is needed (decided
  2026-11-17). It checks answers it wrote itself, so it may be lenient; experiments/eval_claimcheck.py compares it
  with human grades and with the Qwen3-8B judge.
- Calls go through LLMCache with the same key rule as generation (model, revision, messages, max_new_tokens).
- Policies (`apply_policy`): off (nothing changes), flag (text unchanged, unsupported sentences listed for the UI),
  strip (unsupported sentences removed; blocked if nothing cited is left), block (blocked when the share of
  supported sentences is below `min_support`).

[KO]
- 역할: 출력 검증(validation.validate_answer)은 형식만 본다(거절인지, 인용이 있는지, 인용 ID가 컨텍스트에 있는지). 실제 청크를
  인용하면서 그 청크에 없는 말을 하는 매끄러운 답은 통과한다(채점된 예: 비틀림 진동 질문에 니들 롤러 베어링, 전식 플루팅을
  프레팅으로 설명). 이 모듈은 문장 단위로 내용을 확인한다.
- 문장 분리: generation.SENT_RE. 인용 표시만 있는 조각("... . [en_x#1]")은 앞 문장에 붙인다. 검사 모델이 읽는 문장에서는 인용
  표시를 뺀다.
- 문장별 판정: 자기 인용 없음 -> 답변의 다른 곳에서 인용한 청크로 검사(inherited, 인용이 없으면 컨텍스트 전체), strict=True면
  검사 없이 근거 없음(no_citation). 컨텍스트에 없는 ID 인용 -> 근거 없음(unknown_citation).
  그 밖에는 인용한 청크만 넣고 SUPPORTED / NOT_SUPPORTED를 묻는다(claim_v1, greedy, 최대 8토큰). 파싱 불가는 None(집계 제외).
- 모델: 서비스 생성 모델(Qwen3-4B-Instruct-2507)을 그대로 써서 GPU 메모리가 늘지 않는다(2026-11-17 결정). 자기 답을 자기가
  검사하므로 관대할 수 있다. experiments/eval_claimcheck.py에서 사람 채점, Qwen3-8B 판정과 비교한다.
- 호출은 생성과 같은 키 규칙(모델, 리비전, 메시지, max_new_tokens)으로 LLMCache를 거친다.
- 정책(`apply_policy`): off(변화 없음), flag(답은 그대로, 근거 없는 문장 목록을 UI에 전달), strip(근거 없는 문장 삭제, 인용 문장이
  하나도 안 남으면 차단), block(뒷받침 비율이 `min_support` 미만이면 차단).
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from ragbench.cache import LLMCache, make_key
from ragbench.generation import CITE_RE, NO_ANSWER, SENT_RE

PROMPT_VERSION = "claim_v1"
POLICIES = ("off", "flag", "strip", "block")
MAX_NEW = 8
_ONLY_CITES = re.compile(r"^(\s*\[[A-Za-z0-9_.\-]+#\d+\]\s*[.。]?\s*)+$")
# 문장 맨 앞의 인용 표시 뒤에 공백(또는 끝)이 오면 앞 문장의 인용이다. "[kb_x#0]에 따르면"처럼 바로 붙으면 이 문장의 일부
_LEADING_CITES = re.compile(r"^((?:\s*\[[A-Za-z0-9_.\-]+#\d+\])+\s*[.。]?)(?=\s|$)\s*")
_BROKEN_CITE = re.compile(r"\[[A-Za-z0-9_.\-#]*$")    # 생성 길이 한도에서 잘린 인용 ("... [kb_shaft_seat_repair")
_SYSTEM = ("You are a strict fact checker for technical texts about bearings and automotive parts. You are given "
           "passages and one statement. Decide whether every factual claim in the statement is directly supported by "
           "the passages. A claim that adds a cause, a number, a part name or a recommendation the passages do not give "
           "is not supported. The statement may be in another language than the passages. "
           "Reply with exactly one word: SUPPORTED or NOT_SUPPORTED.")


@dataclass
class Claim:
    text: str                       # 원래 문장 (인용 표시 포함)
    cited: list[str]
    supported: bool | None = None   # None = 판정 파싱 불가
    reason: str | None = None       # no_citation | unknown_citation | model | unparsable


@dataclass
class ClaimReport:
    claims: list[Claim] = field(default_factory=list)
    seconds: float = 0.0
    model_calls: int = 0

    @property
    def judged(self) -> list[Claim]:
        return [c for c in self.claims if c.supported is not None]

    @property
    def support_ratio(self) -> float:
        j = self.judged
        return sum(c.supported for c in j) / len(j) if j else 1.0

    @property
    def unsupported(self) -> list[int]:
        return [i for i, c in enumerate(self.claims) if c.supported is False]

    def to_dict(self) -> dict[str, Any]:
        return {"claims": [asdict(c) for c in self.claims], "support_ratio": round(self.support_ratio, 4),
                "unsupported": self.unsupported, "seconds": round(self.seconds, 4), "model_calls": self.model_calls,
                "prompt_version": PROMPT_VERSION}


def split_claims(answer: str) -> list[Claim]:
    text = (answer or "").strip()
    if not text or text.startswith(NO_ANSWER):
        return []
    claims: list[Claim] = []
    for part in SENT_RE.split(text):
        lead = _LEADING_CITES.match(part)
        if lead and claims:
            # 마침표 뒤에 온 인용 표시("... . [en_x#1] 다음 문장")는 앞 문장의 인용이다
            claims[-1].text = f"{claims[-1].text} {lead.group(1).strip()}"
            claims[-1].cited += CITE_RE.findall(lead.group(1))
            part = part[lead.end():]
        if not part.strip() or _ONLY_CITES.match(part) or not statement_text(Claim(part, [])):
            continue
        claims.append(Claim(part.strip(), CITE_RE.findall(part)))
    return claims


def statement_text(claim: Claim) -> str:
    return re.sub(r"\s+", " ", _BROKEN_CITE.sub("", CITE_RE.sub("", claim.text))).strip()


def build_check_messages(statement: str, passages: list[dict[str, Any]]) -> list[dict[str, str]]:
    ctx = "\n\n".join(f"[{p['chunk_id']}] {p['text']}" for p in passages)
    return [{"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Passages:\n\n{ctx}\n\nStatement: {statement}\n\nAnswer SUPPORTED or NOT_SUPPORTED."}]


def parse_support(text: str) -> bool | None:
    t = (text or "").upper()
    if "NOT_SUPPORTED" in t or "NOT SUPPORTED" in t or "UNSUPPORTED" in t:
        return False
    if "SUPPORTED" in t:
        return True
    return None


class ClaimChecker:
    """strict=False (default): a sentence without its own citation is checked against the passages the answer cites
    elsewhere (all context passages if it cites none), since the generator often cites once per paragraph: 66 of the
    102 graded answers (eval/human_gold) have a sentence without a citation of its own, and every one of them cites
    elsewhere. strict=True marks such a sentence unsupported without asking the model.

    [KO] strict=False(기본): 자기 인용이 없는 문장은 답변의 다른 곳에서 인용한 청크(인용이 하나도 없으면 컨텍스트 전체)로 검사한다.
    생성 모델은 문단 끝에 한 번만 인용하는 경우가 많다. strict=True면 검사 없이 근거 없음.
    """

    def __init__(self, generator, cache: LLMCache | None = None, strict: bool = False):
        self.generator, self.cache, self.strict = generator, cache, strict

    def _ask(self, messages: list[dict[str, str]]) -> str:
        key = make_key(self.generator.model_name, self.generator.revision, messages, MAX_NEW)
        out = self.cache.get(key) if self.cache is not None else None
        if out is None:
            out = self.generator.generate(messages, max_new_tokens=MAX_NEW)
            if self.cache is not None:
                self.cache.put(key, out)
        return out["text"]

    def check(self, answer: str, passages: list[dict[str, Any]]) -> ClaimReport:
        t0 = time.perf_counter()
        by_id = {p["chunk_id"]: p for p in passages}
        report = ClaimReport(split_claims(answer))
        answer_cites = [i for c in report.claims for i in c.cited if i in by_id]
        fallback = list(dict.fromkeys(answer_cites)) or list(by_id)
        for c in report.claims:
            if any(i not in by_id for i in c.cited):
                c.supported, c.reason = False, "unknown_citation"
                continue
            if not c.cited and self.strict:
                c.supported, c.reason = False, "no_citation"
                continue
            ids = list(dict.fromkeys(c.cited)) or fallback
            c.supported = parse_support(self._ask(build_check_messages(statement_text(c), [by_id[i] for i in ids])))
            c.reason = ("model" if c.cited else "inherited") if c.supported is not None else "unparsable"
            report.model_calls += 1
        report.seconds = time.perf_counter() - t0
        return report


@dataclass
class PolicyResult:
    text: str | None            # None = 차단
    blocked: bool
    reason: str | None
    flagged: list[int]


def apply_policy(answer: str, report: ClaimReport, policy: str, min_support: float = 1.0) -> PolicyResult:
    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}, got {policy!r}")
    flagged = report.unsupported
    if policy in ("off", "flag") or not report.claims:
        return PolicyResult(answer, False, None, flagged if policy == "flag" else [])
    if policy == "block":
        ok = report.support_ratio >= min_support
        return PolicyResult(answer if ok else None, not ok, None if ok else "claim_unsupported", flagged)
    # strip: 근거 없는 문장을 지운다. 남은 문장에 인용이 하나도 없으면 차단
    kept = [c.text for i, c in enumerate(report.claims) if i not in set(flagged)]
    if not kept or not any(CITE_RE.search(t) for t in kept):
        return PolicyResult(None, True, "claim_unsupported", flagged)
    return PolicyResult(" ".join(kept), False, None, flagged)
