"""Hybrid retrieval by Reciprocal Rank Fusion (RRF) over any number of retrievers.

[EN]
- Role: run each base retriever for `candidates` results, fuse by rank only:
      score(d) = sum_over_retrievers 1 / (rrf_k + rank_r(d)),  rank is 1-based
  and return the top k of the fused list.
- Why RRF (book ch.12 hybrid): BM25 scores (unbounded) and cosine scores ([-1,1]) live on
  different scales; fusing by rank needs no normalisation or tuned weights. rrf_k=60 is the
  value from the original paper (Cormack et al. 2009): large enough that rank 1 vs rank 2 does
  not dominate, small enough that deep ranks still contribute a little.
- Alternatives: convex score combination after min-max normalisation (needs a weight and is
  sensitive to score distribution), learned fusion (needs training data).
- Per-hit provenance (rank in each retriever) is kept for failure analysis.

[KO]
- 역할: 각 기본 검색기에서 `candidates`개를 받아 순위만으로 융합한다:
      score(d) = Σ_검색기 1 / (rrf_k + rank_r(d)),  rank는 1부터
  융합 목록의 상위 k개를 돌려준다.
- RRF를 쓰는 이유(책 12장 하이브리드): BM25 점수(상한 없음)와 코사인 점수([-1,1])는 스케일이 다르다.
  순위 융합은 정규화나 가중치 튜닝이 필요 없다. rrf_k=60은 원 논문(Cormack 외 2009) 값으로,
  1위와 2위 차이가 지배하지 않을 만큼 크고 깊은 순위도 조금은 기여할 만큼 작다.
- 대안: min-max 정규화 후 가중합(가중치 필요, 점수 분포에 민감), 학습 기반 융합(학습 데이터 필요).
- 실패 분석을 위해 각 검색기에서의 순위(출처)를 결과에 남긴다.
"""

from __future__ import annotations

import time
from typing import Any

from ragbench.retrieval.base import Hit


class RRFRetriever:
    def __init__(self, retrievers: list, rrf_k: int = 60, candidates: int = 50):
        self.retrievers = retrievers
        self.rrf_k, self.candidates = rrf_k, candidates
        self.name = "rrf(" + "+".join(r.name for r in retrievers) + f")_k{rrf_k}"
        self.last_provenance: dict[str, dict[str, int]] = {}

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        t0 = time.perf_counter()
        stats = {r.name: r.index(chunks) for r in self.retrievers}
        stats["build_seconds"] = time.perf_counter() - t0
        return stats

    def search(self, query: str, k: int) -> list[Hit]:
        fused: dict[str, float] = {}
        prov: dict[str, dict[str, int]] = {}
        for r in self.retrievers:
            for rank, (cid, _score) in enumerate(r.search(query, self.candidates), start=1):
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (self.rrf_k + rank)
                prov.setdefault(cid, {})[r.name] = rank
        ranked = sorted(fused.items(), key=lambda x: -x[1])[:k]
        self.last_provenance = {cid: prov[cid] for cid, _ in ranked}
        return ranked
