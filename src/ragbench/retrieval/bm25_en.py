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


class EnglishBM25Retriever:
    def __init__(self, translator, english_chunks_path: str | Path, tokenizer: str = "whitespace",
                 k1: float = 1.5, b: float = 0.75):
        self.name = f"bm25en_{tokenizer}"
        self.translator = translator
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
        r = self.translator.translate(query, "query")
        self.query_log.append({"query": query, "english": r["text"], "truncated": r["truncated"], "seconds": r["seconds"]})
        # 번역문으로 영어 인덱스를 검색. 반환되는 ID는 원래 청크 ID다
        return self.inner.search(r["text"], k)

    def run_extra(self) -> dict[str, Any]:
        # 캐시에 저장된 원래 생성 시간의 중앙값 = 질의 번역이 실제로 드는 지연
        secs = [q["seconds"] for q in self.query_log]
        return {"query_translation_seconds_p50": statistics.median(secs) if secs else None,
                "query_translations_truncated": sum(q["truncated"] for q in self.query_log),
                "query_translations": self.query_log}
