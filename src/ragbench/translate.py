"""English pivot translation with the local Qwen3-4B model (queries and chunks), cached in SQLite.

[EN]
- Role: put every text into one language before keyword search. BM25 cannot match a Korean query
  against English or German chunks (cross-language nDCG about 0.10), so queries and chunks are both
  translated to English and BM25 runs on English only (decided 2026-10-14, option B).
- Model: the generation model already used in this repository (Qwen3-4B-Instruct-2507, greedy).
  No external API. The term list lives in the prompt (standard engineering terms), not in a dictionary.
- Query prompt is language-agnostic ("if already English, return it unchanged") because the
  retriever receives text without a language tag. Chunk prompts are used only for non-English chunks;
  English chunks are never sent to the model.
- Truncation: a translation that used all `max_new_tokens` is flagged `truncated` and counted in the
  result; it is kept as is (no retry), so the effect shows up in the numbers.
- Cache: LLMCache keyed by (model, revision, messages, max_new_tokens); a rerun costs no GPU time.
  The original generation seconds are stored in the cache value so latency can still be reported.

[KO]
- 역할: 키워드 검색 전에 모든 텍스트를 한 언어로 맞춘다. BM25는 한국어 질의로 영어·독일어 청크를 맞출 수
  없으므로(교차 언어 nDCG 약 0.10) 질의와 청크를 모두 영어로 번역하고 영어끼리 BM25를 돌린다
  (2026-10-14 결정, B안).
- 모델: 저장소에서 이미 쓰는 생성 모델(Qwen3-4B-Instruct-2507, greedy). 외부 API 없음. 용어는 사전이
  아니라 프롬프트(표준 공학 용어 사용 지시)로 처리한다.
- 질의 프롬프트는 검색기가 언어 태그 없이 텍스트만 받으므로 언어 무관("이미 영어면 그대로")이다.
  청크 프롬프트는 영어가 아닌 청크에만 쓰고, 영어 청크는 모델에 보내지 않는다.
- 잘림: `max_new_tokens`를 다 쓴 번역은 `truncated`로 표시하고 결과에 집계한다. 재시도 없이 그대로 써서
  영향이 숫자에 드러나게 한다.
- 캐시: LLMCache 키 = (모델, 리비전, 메시지, max_new_tokens). 재실행은 GPU를 쓰지 않는다. 지연을
  보고할 수 있도록 원래 생성 시간을 캐시 값에 같이 저장한다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ragbench.cache import LLMCache, make_key

# 번역 모델: 3단계 생성에 쓰는 모델을 그대로 재사용 (새 의존성 없음)
MODEL = "Qwen/Qwen3-4B-Instruct-2507"
SYSTEM = "You are a professional technical translator for mechanical engineering (bearings, seals, lubrication, tribology, automotive parts)."
# 질의는 짧아서 96, 청크는 최대 384토큰 원문이 영어로 늘어날 수 있어 768로 여유를 둔다
MAX_NEW_TOKENS = {"query": 96, "passage": 768, "numbered": 900}
# 모델이 "Translation:" 같은 머리말을 붙이는 경우를 지우기 위한 패턴
_PREFIX = re.compile(r"^\s*(translation|english|translated text)\s*[:：]\s*", re.IGNORECASE)

# 질의/본문 지시문. 용어 통일(구름 베어링 = Wälzlager = rolling bearing)이 교차 언어 매칭의 핵심이라 예시로 박아 둔다
_INSTRUCTION = {
    "query": ("Translate the following search question into English. If it is already English, output it unchanged. "
              "Use the standard English engineering term for technical words "
              "(for example 구름 베어링 and Wälzlager both become 'rolling bearing'). Output only the translation."),
    "passage": ("Translate the following text into English. Keep numbers, units, formulas, symbols and proper nouns unchanged. "
                "Use the standard English engineering term for technical words "
                "(for example 구름 베어링 and Wälzlager both become 'rolling bearing'). Keep the line breaks. Output only the translation."),
}


def load_glossary(path: str | Path) -> list[dict[str, Any]]:
    import json

    return json.loads(Path(path).read_text(encoding="utf-8"))["entries"]


def glossary_hint(text: str, entries: list[dict[str, Any]]) -> str:
    """Term hints for the entries whose ko/de form occurs in `text` ("" if none).

    A matched form that is only a part of a longer matched form is dropped (마찰 inside 구름 마찰), so the
    hint names the most specific term.
    """
    low = text.lower()
    found = [(form, e["en"]) for e in entries for form in e["ko"] + e["de"] if form.lower() in low]
    found = [(f, en) for f, en in found if not any(f != g and f.lower() in g.lower() for g, _ in found)]
    found.sort(key=lambda fe: low.find(fe[0].lower()))      # 텍스트에 나온 순서대로
    seen, lines = set(), []
    for f, en in found:
        if (f.lower(), en) not in seen:
            seen.add((f.lower(), en))
            lines.append(f"{f} = {en}")
    return "; ".join(lines)


def translation_messages(text: str, kind: str, hint: str = "") -> list[dict[str, str]]:
    # kind 오타가 조용히 다른 프롬프트로 가지 않게 바로 예외
    if kind not in _INSTRUCTION:
        raise ValueError(f"kind must be 'query' or 'passage', got {kind!r}")
    # 용어 힌트는 지시문 뒤, 본문 앞에 둔다 (힌트가 없으면 메시지가 예전과 같아 캐시가 그대로 맞는다)
    hint_line = f"\n\nRequired term translations (use exactly these): {hint}" if hint else ""
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{_INSTRUCTION[kind]}{hint_line}\n\n{text}"}]


# 문서 먼저 번역(docfirst) 방식: 번호 붙은 문장을 번호 그대로 한 줄씩 번역하게 해서 원문-번역 문장 정렬을 유지한다
_NUMBERED_INSTRUCTION = ("Translate each numbered sentence into English. Output exactly one line per input line, "
                         "keeping the same numbers in the form [n]. Do not merge, split, add or drop sentences. "
                         "Keep numbers, units, formulas, symbols and proper nouns unchanged. "
                         "Use the standard English engineering term for technical words "
                         "(for example 구름 베어링 and Wälzlager both become 'rolling bearing'). Output only the translated lines.")


def numbered_messages(numbered: str, title: str, section_path: list[str]) -> list[dict[str, str]]:
    # 제목·절 경로는 용어 일관성을 위한 문맥이고 번역 대상이 아니다
    context = f"Document title: {title}\nSection: {' > '.join(section_path) or '(lead)'}\n(Context only, do not translate.)"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{_NUMBERED_INSTRUCTION}\n\n{context}\n\n{numbered}"}]


def clean_translation(text: str, kind: str) -> str:
    # 머리말 제거 후, 질의는 줄바꿈·따옴표까지 정리한다 (본문은 줄바꿈을 보존)
    out = _PREFIX.sub("", (text or "").strip())
    if kind == "query":
        out = " ".join(out.split()).strip(" \"'“”「」*")
    return out


class Translator:
    """Cached translator. The model is loaded on the first cache miss only."""

    def __init__(self, cache_path: str | Path, model_name: str = MODEL, device: str = "cuda:0",
                 glossary: list[dict[str, Any]] | None = None):
        self.model_name, self.device = model_name, device
        self.glossary = glossary          # 있으면 번역할 텍스트에 나온 용어의 힌트를 프롬프트에 붙인다
        # 캐시가 있으면 모델을 올릴 필요가 없으므로 Generator는 첫 캐시 미스 때 로드한다
        self.cache = LLMCache(cache_path)
        self._gen = None
        self._revision: str | None = None

    def _generator(self):
        if self._gen is None:
            # 무거운 import는 여기서만 (캐시 히트만 있는 실행은 torch를 로드하지 않음)
            from ragbench.generation import Generator

            self._gen = Generator(self.model_name, device=self.device)
            self._revision = self._gen.revision
        return self._gen

    def _revision_for_key(self) -> str | None:
        # 캐시 키에 모델 리비전이 들어가야 모델이 바뀌면 캐시가 무효화된다
        if self._revision is None:
            from ragbench.embedding import hf_cached_revision

            self._revision = hf_cached_revision(self.model_name)
        return self._revision

    def translate(self, text: str, kind: str) -> dict[str, Any]:
        """Return {"text", "truncated", "seconds", "completion_tokens", "from_cache"}."""
        hint = glossary_hint(text, self.glossary) if self.glossary else ""
        out = self._run(translation_messages(text, kind, hint), MAX_NEW_TOKENS[kind])
        return {**out, "text": clean_translation(out["text"], kind)}

    def translate_numbered(self, numbered: str, title: str, section_path: list[str]) -> dict[str, Any]:
        """Numbered sentences for the docfirst build; the raw model text is returned (the caller parses the numbers)."""
        return self._run(numbered_messages(numbered, title, section_path), MAX_NEW_TOKENS["numbered"])

    def _run(self, messages: list[dict[str, str]], limit: int) -> dict[str, Any]:
        # 1) 캐시 조회: 같은 모델·리비전·프롬프트·길이 제한이면 GPU 없이 즉시 반환
        key = make_key(self.model_name, self._revision_for_key(), messages, limit)
        hit = self.cache.get(key)
        if hit is not None:
            return {**hit, "from_cache": True}
        # 2) 캐시 미스: 실제로 생성하고, 한도를 다 쓰면 잘린 번역으로 표시한다 (재시도 없음)
        out = self._generator().generate(messages, max_new_tokens=limit)
        value = {"text": out["text"], "truncated": out["completion_tokens"] >= limit,
                 "seconds": out["seconds"], "completion_tokens": out["completion_tokens"]}
        # 3) 원래 생성 시간(seconds)까지 저장해 두어 재실행해도 번역 지연을 보고할 수 있게 한다
        self.cache.put(key, value)
        return {**value, "from_cache": False}
