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
- "en_stem" / "en_stem_stop" (added 2026-10-19, for the English-pivot BM25 only): whitespace tokens
  reduced with the Snowball English stemmer (PyStemmer: bearings -> bearing, lubrication ->
  lubric), the second variant also drops bm25s's 33 English stopwords. They must only be used on
  English text (translated chunks and queries); on ko/de text they would stem nonsense.
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
- "en_stem" / "en_stem_stop"(2026-10-19 추가, 영어 피벗 BM25 전용): 공백 토큰을 Snowball 영어 stemmer
  (PyStemmer)로 줄인다(bearings -> bearing, lubrication -> lubric). 두 번째는 bm25s의 영어 불용어 33개도
  버린다. 영어 텍스트(번역한 청크·질의)에만 써야 하며 한국어·독일어에 쓰면 의미 없는 어간이 나온다.
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


@lru_cache(maxsize=1)
def _en_stemmer():
    import Stemmer     # PyStemmer: Snowball 알고리즘의 C 구현 (bm25s도 같은 라이브러리를 쓴다)
    return Stemmer.Stemmer("english")


def en_stem_tokenize(text: str) -> list[str]:
    return _en_stemmer().stemWords(whitespace_tokenize(text))


def en_stem_stop_tokenize(text: str) -> list[str]:
    from bm25s.stopwords import STOPWORDS_EN
    stop = set(STOPWORDS_EN)
    return _en_stemmer().stemWords([t for t in whitespace_tokenize(text) if t not in stop])    # 불용어는 어간 추출 전에 제거


TOKENIZERS: dict[str, Tokenizer] = {
    "whitespace": whitespace_tokenize,
    "kiwi": kiwi_tokenize,
    "subword": subword_tokenize,
    "en_stem": en_stem_tokenize,
    "en_stem_stop": en_stem_stop_tokenize,
}


def get_tokenizer(name: str) -> Tokenizer:
    try:
        return TOKENIZERS[name]
    except KeyError:
        raise ValueError(f"unknown tokenizer {name!r}; choose from {sorted(TOKENIZERS)}") from None
