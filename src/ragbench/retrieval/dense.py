"""Dense retriever: bge-m3 embeddings + hnswlib ANN index (or exact numpy search as ground truth).

[EN]
- Role: index() embeds chunks (cached), builds an HNSW graph with (m, ef_construction); search()
  embeds the query and runs knn with ef_search. exact=True skips HNSW and does a full dot-product
  scan, which is the ground truth for measuring ANN recall in the HNSW sweep.
- Why hnswlib directly (decided 2026-10-11): the three HNSW knobs are explicit constructor /
  set_ef calls, nothing hidden behind a database; small corpus (hundreds of chunks) needs no server.
- Space "ip" (inner product) on L2-normalised vectors == cosine similarity; scores are in [-1, 1].
- Index stats recorded: build seconds, bytes on disk (save_index to a temp file), m, ef_construction,
  ef_search, embed time, whether embeddings came from cache.
- Reproducibility: the graph is built with num_threads=1. With the default (all cores) the
  insertion order, and so the graph, differs per run: 31 of 60 test queries returned a different
  top-50 list across 5 builds, 0 of 60 with one thread.
- Caveat: with only ~350 vectors HNSW recall will be ~1.0 for almost any setting; the sweep
  reports that honestly and discusses corpus size as the cause.

[KO]
- 역할: index()는 청크를 임베딩(캐시)하고 (m, ef_construction)으로 HNSW 그래프를 만든다. search()는
  질의를 임베딩해 ef_search로 knn을 돈다. exact=True면 HNSW 없이 전체 내적 스캔을 하며, 이것이 HNSW
  sweep에서 ANN recall을 재는 기준(ground truth)이다.
- hnswlib 직접 사용 이유(2026-10-11 결정): HNSW 파라미터 3개가 생성자·set_ef 호출로 그대로 드러나고
  DB 뒤에 숨지 않는다. 수백 개 청크라 서버가 필요 없다.
- "ip"(내적) 공간 + L2 정규화 벡터 = 코사인 유사도. 점수 범위 [-1, 1].
- 기록하는 인덱스 통계: 빌드 시간, 디스크 바이트(임시 파일로 save_index), m, ef_construction,
  ef_search, 임베딩 시간, 캐시 사용 여부.
- 재현성: 그래프를 num_threads=1로 만든다. 기본값(전체 코어)은 삽입 순서가 실행마다 달라 그래프도
  달라진다: 테스트 질문 60개 중 31개가 5번 빌드에서 상위 50개 목록이 달랐고, 단일 스레드는 0개였다.
- 주의: 벡터가 약 350개뿐이라 거의 모든 설정에서 HNSW recall이 1.0 근처가 된다. sweep 결과는 그대로
  기록하고 코퍼스 크기를 원인으로 분석한다.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any

import hnswlib
import numpy as np

from ragbench.config import HNSWConfig
from ragbench.embedding import Embedder
from ragbench.retrieval.base import Hit


class DenseRetriever:
    def __init__(self, model_name: str = "BAAI/bge-m3", hnsw: HNSWConfig | None = None,
                 exact: bool = False, embedder: Embedder | None = None, chunk_set_id: str = "default"):
        self.hnsw = hnsw or HNSWConfig()
        self.exact = exact
        self.name = f"dense_{'exact' if exact else f'hnsw_m{self.hnsw.m}_efc{self.hnsw.ef_construction}_ef{self.hnsw.ef_search}'}"
        self.embedder = embedder or Embedder(model_name)
        self.chunk_set_id = chunk_set_id
        self.chunk_ids: list[str] = []
        self.emb: np.ndarray | None = None
        self.index_: hnswlib.Index | None = None

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        self.chunk_ids = [c["chunk_id"] for c in chunks]
        self.emb, emb_info = self.embedder.encode_chunks_cached(chunks, self.chunk_set_id)
        stats: dict[str, Any] = {"n_chunks": len(chunks), "dim": int(self.emb.shape[1]),
                                 "model_revision": self.embedder.revision, **emb_info}
        if self.exact:
            stats.update(build_seconds=0.0, index_bytes=int(self.emb.nbytes), exact=True)
            return stats
        t0 = time.perf_counter()
        self.index_ = hnswlib.Index(space="ip", dim=self.emb.shape[1])
        self.index_.init_index(max_elements=len(chunks), M=self.hnsw.m, ef_construction=self.hnsw.ef_construction,
                               random_seed=42)
        # single-threaded insertion: multi-threaded add_items builds a different graph on every run
        self.index_.add_items(self.emb, np.arange(len(chunks)), num_threads=1)
        self.index_.set_ef(self.hnsw.ef_search)
        build = time.perf_counter() - t0
        with tempfile.NamedTemporaryFile(suffix=".hnsw", delete=False) as f:
            tmp = f.name
        self.index_.save_index(tmp)
        size = os.path.getsize(tmp)
        os.unlink(tmp)
        stats.update(build_seconds=build, index_bytes=size, m=self.hnsw.m,
                     ef_construction=self.hnsw.ef_construction, ef_search=self.hnsw.ef_search, exact=False)
        return stats

    def set_ef(self, ef: int) -> None:
        """ef_search can change after build (hnswlib set_ef); used by the sweep."""
        self.hnsw.ef_search = ef
        if self.index_ is not None:
            self.index_.set_ef(ef)

    def search_vec(self, qvec: np.ndarray, k: int) -> list[Hit]:
        k = min(k, len(self.chunk_ids))
        if self.exact:
            scores = self.emb @ qvec
            top = np.argpartition(-scores, k - 1)[:k]
            top = top[np.argsort(-scores[top])]
            return [(self.chunk_ids[i], float(scores[i])) for i in top]
        labels, dists = self.index_.knn_query(qvec[None, :], k=k)   # ip space returns 1 - dot
        return [(self.chunk_ids[i], float(1.0 - d)) for i, d in zip(labels[0], dists[0])]

    def search(self, query: str, k: int) -> list[Hit]:
        qvec = self.embedder.encode([query])[0]
        return self.search_vec(qvec, k)
