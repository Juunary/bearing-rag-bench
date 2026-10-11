"""BM25 over pre-tokenized chunks (bm25s backend, tokenizer injected from ragbench.tokenize)."""

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
