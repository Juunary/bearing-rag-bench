"""Tokenizers for lexical (BM25) retrieval. Each maps one text -> list[str].

[EN]
- Role: make "what is a token" an injectable choice so BM25 quality can be compared per tokenizer.
- "whitespace": NFKC, lowercase, strip punctuation, split on spaces. Baseline that exposes the
  Korean problem: 베어링은 / 베어링을 / 베어링의 become three unrelated terms.
- "kiwi": kiwipiepy morphological analysis, keep content morphemes (nouns, verb/adjective roots,
  numerals, Latin-script SL tokens, hanja, numbers), drop particles/endings/punctuation.
  Latin words in en/de text come out as SL tokens, so one tokenizer serves all three languages
  (no stemming for en/de). Trailing "." on SL tokens is stripped.
- "subword": the embedding model's tokenizer (bge-m3, XLM-R SentencePiece). One vocabulary for
  all languages; splits German compounds (Kegel/rollen/lager) but shreds Korean into syllables
  (베/어/링), which is reported as-is in the results.
- Not chosen for stage 1: character bigrams, Snowball German stemmer (candidates for stage 2).

[KO]
- 역할: "토큰이 무엇인가"를 주입 가능한 선택지로 만들어 토크나이저별 BM25 품질을 비교한다.
- "whitespace": NFKC, 소문자화, 구두점 제거, 공백 분리. 한국어 문제를 드러내는 기준선:
  베어링은/베어링을/베어링의가 서로 다른 세 단어가 된다.
- "kiwi": kiwipiepy 형태소 분석. 내용 형태소(명사, 용언 어근, 수사, 라틴 문자 SL, 한자, 숫자)만 남기고
  조사·어미·구두점은 버린다. en/de 텍스트의 라틴 단어는 SL 토큰으로 나오므로 하나의 토크나이저로
  세 언어를 처리한다(en/de 어간 추출은 없음). SL 토큰 끝의 "."은 제거.
- "subword": 임베딩 모델 토크나이저(bge-m3, XLM-R SentencePiece). 세 언어 공통 어휘. 독일어 복합명사는
  나뉘지만(Kegel/rollen/lager) 한국어는 음절 단위로 부서진다(베/어/링). 결과에 그대로 기록한다.
- 1단계 미채택: 문자 bigram, Snowball 독일어 stemmer(2단계 후보).
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Callable

Tokenizer = Callable[[str], list[str]]

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)

# Kiwi POS tags to keep: common/proper/bound nouns, numerals, verb & adjective roots, root morphemes,
# foreign (Latin-script) words, hanja, numbers.
KIWI_KEEP = {"NNG", "NNP", "NNB", "NR", "VV", "VA", "XR", "SL", "SH", "SN"}


def whitespace_tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).lower()
    return _PUNCT_RE.sub(" ", text).split()


@lru_cache(maxsize=1)
def _kiwi():
    from kiwipiepy import Kiwi
    return Kiwi()


def kiwi_tokenize(text: str) -> list[str]:
    out = []
    for t in _kiwi().tokenize(unicodedata.normalize("NFKC", text)):
        if t.tag in KIWI_KEEP:
            form = _PUNCT_RE.sub("", t.form).lower()   # SL tokens may carry trailing "." / ","
            if form:
                out.append(form)
    return out


@lru_cache(maxsize=1)
def _hf_tokenizer(name: str = "BAAI/bge-m3"):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(name)


def subword_tokenize(text: str) -> list[str]:
    toks = _hf_tokenizer().tokenize(unicodedata.normalize("NFKC", text))
    out = []
    for t in toks:
        t = t.replace("▁", "")        # SentencePiece word-start marker
        if t and not _PUNCT_RE.fullmatch(t):
            out.append(t.lower())
    return out


TOKENIZERS: dict[str, Tokenizer] = {
    "whitespace": whitespace_tokenize,
    "kiwi": kiwi_tokenize,
    "subword": subword_tokenize,
}


def get_tokenizer(name: str) -> Tokenizer:
    try:
        return TOKENIZERS[name]
    except KeyError:
        raise ValueError(f"unknown tokenizer {name!r}; choose from {sorted(TOKENIZERS)}") from None
