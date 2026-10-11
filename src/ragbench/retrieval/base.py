"""Common retriever interface.

[EN]
- Role: every retriever (BM25, dense, RRF hybrid, reranked) exposes index(chunks) -> stats and
  search(query, k) -> [(chunk_id, score), ...] best first, so the runner and the hybrid fuser
  treat them interchangeably.
- Protocol (structural typing) instead of a base class: no shared state, nothing to inherit.

[KO]
- 역할: 모든 검색기(BM25, dense, RRF 하이브리드, 리랭크)가 index(chunks) -> 통계,
  search(query, k) -> [(청크ID, 점수), ...] (좋은 순)로 같은 모양을 갖게 해 러너와 융합기가 구분 없이 쓴다.
- 기반 클래스 대신 Protocol(구조적 타이핑): 공유 상태가 없으니 상속할 것도 없다.
"""

from __future__ import annotations

from typing import Any, Protocol

Hit = tuple[str, float]   # (chunk_id, score) best first


class Retriever(Protocol):
    name: str

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the index. Returns index statistics (build seconds, size, ...)."""

    def search(self, query: str, k: int) -> list[Hit]: ...
