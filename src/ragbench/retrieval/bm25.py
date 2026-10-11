"""BM25 retriever: bm25s backend over pre-tokenized chunks, tokenizer injected.

[EN]
- Role: lexical baseline. index() tokenizes every chunk with the chosen tokenizer and builds a
  bm25s index; search() tokenizes the query the same way and returns top-k (chunk_id, score).
- Why bm25s (decided 2026-10-11): fast, tested, accepts pre-tokenized token lists so our own
  tokenizers plug in. Formula (Lucene variant): score = sum IDF(t) * tf*(k1+1) / (tf + k1*(1-b+b*|d|/avgdl)).
- Defaults k1=1.5, b=0.75 (bm25s defaults; standard values). Zero-score hits are dropped.
- Index stats (build seconds, vocab size, avg tokens per chunk) go into the result file so the
  tokenizers can be compared on cost as well as quality.
- Alternative: own numpy implementation (formula visible; ~50 lines) - skipped for time.

[KO]
- 역할: 어휘 기반 기준선. index()는 선택한 토크나이저로 모든 청크를 토큰화해 bm25s 인덱스를 만들고,
  search()는 질의를 같은 방식으로 토큰화해 상위 k개 (청크ID, 점수)를 돌려준다.
- bm25s를 쓰는 이유(2026-10-11 결정): 빠르고 검증됐으며 미리 토큰화한 리스트를 받아 자체 토크나이저를
  꽂을 수 있다. 수식(Lucene 변형): score = Σ IDF(t)·tf·(k1+1) / (tf + k1·(1−b+b·|d|/avgdl)).
- 기본값 k1=1.5, b=0.75(bm25s 기본, 표준값). 점수 0인 결과는 버린다.
- 인덱스 통계(빌드 시간, 어휘 크기, 청크당 평균 토큰)를 결과 파일에 넣어 토크나이저를 품질뿐 아니라
  비용으로도 비교한다.
- 대안: numpy 직접 구현(수식이 드러남, 약 50줄). 시간상 보류.
"""

from __future__ import annotations

import time
from typing import Any

import bm25s

from ragbench.retrieval.base import Hit
from ragbench.tokenize import get_tokenizer


class BM25Retriever:
    def __init__(self, tokenizer: str = "whitespace", k1: float = 1.5, b: float = 0.75):
        self.name = f"bm25_{tokenizer}"
        self.tokenizer_name = tokenizer
        self.tokenize = get_tokenizer(tokenizer)
        self.k1, self.b = k1, b
        self.model: bm25s.BM25 | None = None
        self.chunk_ids: list[str] = []

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        self.chunk_ids = [c["chunk_id"] for c in chunks]
        corpus_tokens = [self.tokenize(c["text"]) for c in chunks]
        t_tok = time.perf_counter() - t0
        self.model = bm25s.BM25(k1=self.k1, b=self.b)
        self.model.index(corpus_tokens, show_progress=False)
        vocab = {t for toks in corpus_tokens for t in toks}
        return {
            "build_seconds": time.perf_counter() - t0, "tokenize_seconds": t_tok,
            "n_chunks": len(chunks), "vocab_size": len(vocab),
            "avg_tokens_per_chunk": sum(map(len, corpus_tokens)) / max(1, len(corpus_tokens)),
        }

    def search(self, query: str, k: int) -> list[Hit]:
        assert self.model is not None, "call index() first"
        q = self.tokenize(query)
        if not q:
            return []
        k = min(k, len(self.chunk_ids))
        idx, scores = self.model.retrieve([q], k=k, show_progress=False)
        return [(self.chunk_ids[i], float(s)) for i, s in zip(idx[0], scores[0]) if s > 0]
