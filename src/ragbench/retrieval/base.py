from __future__ import annotations

from typing import Any, Protocol

Hit = tuple[str, float]   # (chunk_id, score) best first


class Retriever(Protocol):
    name: str

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the index. Returns index statistics (build seconds, size, ...)."""

    def search(self, query: str, k: int) -> list[Hit]: ...
