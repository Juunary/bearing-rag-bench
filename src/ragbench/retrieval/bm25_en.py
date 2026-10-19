"""English-pivot BM25: translated chunks + translated queries, same chunk ids.

[EN]
- Role: wraps BM25Retriever. index() swaps each chunk's text for its English translation
  (data/processed/chunks_en_<set>.jsonl, built by experiments/build_english_chunks.py); search()
  translates the query to English first (ragbench.translate, cached) and searches that.
- Returned ids are the original chunk ids, so gold mapping, metrics, RRF and the reranker (which
  reads the original text) work unchanged.
- Latency: the experiment runner times search() including translation, but a rerun hits the cache and
  looks fast. `run_extra()` therefore reports the original generation seconds from the cache.
- Missing translation for any chunk raises (a partial index would silently change the corpus).

[KO]
- 역할: BM25Retriever를 감싼다. index()는 청크 텍스트를 영어 번역본
  (data/processed/chunks_en_<set>.jsonl, experiments/build_english_chunks.py로 생성)으로 바꾸고,
  search()는 먼저 질의를 영어로 번역(ragbench.translate, 캐시)한 뒤 검색한다.
- 반환 ID는 원래 청크 ID라서 gold 매핑, 지표, RRF, 원문을 읽는 리랭커가 그대로 동작한다.
- 지연: 러너는 번역을 포함해 search() 시간을 재지만 재실행은 캐시 히트라 빠르게 보인다. 그래서
  `run_extra()`가 캐시에 저장된 원래 생성 시간을 따로 보고한다.
- 번역이 없는 청크가 하나라도 있으면 예외(일부만 색인하면 코퍼스가 조용히 바뀐다).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from ragbench.retrieval.base import Hit
from ragbench.retrieval.bm25 import BM25Retriever


def _translate_query(retriever, query: str) -> dict[str, Any]:
    """Translate a query (or pass it through when skip_english is on and it looks English) and log it."""
    from ragbench.validation import guess_lang

    if retriever.skip_english and guess_lang(query) == "en":
        # 영어로 보이는 질문은 모델 호출 없이 그대로 쓴다 (guess_lang은 한글·독일어 표지만 보는 휴리스틱)
        r = {"text": query, "truncated": False, "seconds": 0.0, "skipped": True}
    else:
        r = {**retriever.translator.translate(query, "query"), "skipped": False}
    retriever.query_log.append({"query": query, "english": r["text"], "truncated": r["truncated"], "seconds": r["seconds"],
                                "skipped": r["skipped"], "from_cache": bool(r.get("from_cache", False))})
    return r


class EnglishBM25Retriever:
    def __init__(self, translator, english_chunks_path: str | Path, tokenizer: str = "whitespace",
                 k1: float = 1.5, b: float = 0.75, skip_english: bool = False):
        self.name = f"bm25en_{tokenizer}"
        self.translator = translator
        self.skip_english = skip_english
        self.path = Path(english_chunks_path)
        # 실제 BM25 계산은 기존 구현을 그대로 쓰고, 이 클래스는 텍스트만 영어로 바꿔 넣는다
        self.inner = BM25Retriever(tokenizer=tokenizer, k1=k1, b=b)
        # 질의별 번역 결과·시간·잘림 여부를 모아 두었다가 결과 파일에 같이 저장한다
        self.query_log: list[dict[str, Any]] = []

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        with open(self.path, encoding="utf-8") as f:
            en = {r["chunk_id"]: r for r in map(json.loads, filter(str.strip, f))}
        # 번역본이 하나라도 빠지면 코퍼스가 조용히 달라지므로 바로 실패시킨다
        missing = [c["chunk_id"] for c in chunks if c["chunk_id"] not in en]
        if missing:
            raise ValueError(f"{len(missing)} chunks have no English translation, e.g. {missing[:3]}")
        # 청크 ID와 나머지 필드는 원본 그대로, text만 영어 번역으로 교체해서 색인한다
        stats = self.inner.index([{**c, "text": en[c["chunk_id"]]["text"]} for c in chunks])
        # 번역된 청크 수와 잘린 청크 수를 인덱스 통계에 남긴다
        stats["chunks_translated"] = sum(en[c["chunk_id"]]["translated"] for c in chunks)
        stats["chunks_truncated"] = sum(en[c["chunk_id"]]["truncated"] for c in chunks)
        return stats

    def search(self, query: str, k: int) -> list[Hit]:
        # 질의를 영어로 번역 (언어 태그가 없어 영어 질의도 그대로 통과시키는 프롬프트 사용)
        r = _translate_query(self, query)
        # 번역문으로 영어 인덱스를 검색. 반환되는 ID는 원래 청크 ID다
        return self.inner.search(r["text"], k)

    def run_extra(self) -> dict[str, Any]:
        # 캐시에 저장된 원래 생성 시간의 중앙값 = 질의 번역이 실제로 드는 지연
        secs = [q["seconds"] for q in self.query_log if not q.get("skipped")]
        return {"query_translation_seconds_p50": statistics.median(secs) if secs else None,
                "query_translations_skipped": sum(bool(q.get("skipped")) for q in self.query_log),
                "query_translations_truncated": sum(q["truncated"] for q in self.query_log),
                "query_translations": self.query_log}


class ExpandedQueryRetriever:
    """English-pivot BM25 with query expansion on the query side (the index is the English one).

    [EN]
    - mode "multi": the faithful English translation plus two alternative wordings (one LLM call); every
      wording is searched and the rankings are fused with RRF (k=60). If the model's answer does not
      contain exactly the two numbered lines, only the translation is used and the failure is counted.
    - mode "hyde": a short hypothetical encyclopedia passage that would answer the question is generated;
      BM25 searches "translation + passage" as one bag of words (HyDE with a lexical retriever).
    - Cost: one more LLM generation per query (reported as query_expansion_seconds_p50).

    [KO]
    - "multi": 충실한 영어 번역 + 다른 표현 2개(LLM 호출 1번). 표현마다 검색해 RRF(k=60)로 합친다. 모델 답에
      번호 줄 2개가 정확히 없으면 번역만 쓰고 실패 횟수를 센다.
    - "hyde": 질문에 답할 법한 짧은 가상 백과 문단을 생성해 "번역 + 문단"을 하나의 단어 묶음으로 BM25 검색한다.
    - 비용: 질문당 LLM 생성 1번 추가(query_expansion_seconds_p50로 보고).
    """

    def __init__(self, translator, english_retriever, mode: str, rrf_k: int = 60, candidates: int = 50):
        if mode not in ("multi", "hyde"):
            raise ValueError(f"unknown query expansion mode {mode!r}")
        self.translator, self.en, self.mode = translator, english_retriever, mode
        self.rrf_k, self.candidates = rrf_k, candidates
        self.name = f"{english_retriever.name}_{mode}"
        self.expand_log: list[dict[str, Any]] = []

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        return self.en.index(chunks)

    def search(self, query: str, k: int) -> list[Hit]:
        from ragbench.docfirst import parse_numbered

        base = _translate_query(self.en, query)            # 충실한 번역 (영어 BM25가 쓰는 것과 같은 번역·같은 로그)
        r = self.translator.expand(query, self.mode)
        entry: dict[str, Any] = {"query": query, "translation": base["text"], "raw": r["text"], "truncated": r["truncated"],
                                 "seconds": r["seconds"], "ok": True}
        self.expand_log.append(entry)
        inner = self.en.inner
        if self.mode == "hyde":
            passage = " ".join(r["text"].split())
            if r["truncated"] or not passage:
                entry["ok"] = False                         # 잘렸거나 비었으면 번역만으로 검색한다
                return inner.search(base["text"], k)
            return inner.search(f"{base['text']} {passage}", k)
        variants = None if r["truncated"] else parse_numbered(r["text"], 2)
        if variants is None:
            entry["ok"] = False
            return inner.search(base["text"], k)
        entry["variants"] = variants
        fused: dict[str, float] = {}
        for text in dict.fromkeys([base["text"], *variants]):       # 같은 문장은 한 번만 (순서 유지)
            for rank, (cid, _score) in enumerate(inner.search(text, self.candidates), start=1):
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (self.rrf_k + rank)
        return sorted(fused.items(), key=lambda x: -x[1])[:k]

    def run_extra(self) -> dict[str, Any]:
        secs = [e["seconds"] for e in self.expand_log]
        return {**self.en.run_extra(), "query_expansion_seconds_p50": statistics.median(secs) if secs else None,
                "query_expansion_failed": sum(not e["ok"] for e in self.expand_log), "query_expansions": self.expand_log}


class QueryPivotRetriever:
    """Translate the query to English, then search an index whose chunks are already English (docfirst variant).

    [KO] 청크가 이미 영어인 인덱스(문서 먼저 번역 방식)에서 질의만 영어로 번역해 검색한다.
    """

    def __init__(self, translator, inner, skip_english: bool = False):
        self.name = f"{inner.name}_qen"
        self.translator, self.inner, self.skip_english = translator, inner, skip_english
        self.query_log: list[dict[str, Any]] = []

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        return self.inner.index(chunks)

    def search(self, query: str, k: int) -> list[Hit]:
        r = _translate_query(self, query)
        return self.inner.search(r["text"], k)

    run_extra = EnglishBM25Retriever.run_extra
