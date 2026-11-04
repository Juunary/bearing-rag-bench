"""Concept-mediated candidates: chunks that mention the concepts matched by the query, ranked by the dense leg.

[EN]
- Role: an extra candidate source that is empty for queries without a matched concept (so those queries keep
  exactly the retrieval they had) and, for matched queries, returns the chunks mentioning the matched concepts
  (plus their 1-hop related concepts) ordered by cosine between the translated query and the chunk embedding.
- Concept -> chunk sets are built mechanically at index time: a chunk belongs to a concept if any alias occurs
  in its original or English text (`concepts.alias_in_text`). No chunk id is ever written by hand.
- Reuses the English dense leg: its Embedder (one bge-m3 in memory) and its stored chunk embeddings
  (`DenseRetriever.emb`, L2-normalised, so a dot product is the cosine; exact, not HNSW).
- The query is translated through the same cached Translator but without touching the pivot's query_log, so
  the stored translation statistics stay one entry per query.
- Used by RerankRetriever as `pool_extra` (candidates added to the reranker pool) and/or `query_augment`
  (canonical concept names appended to the reranker query), or as a third RRF leg (factory, concept_mode).

[KO]
- 역할: 개념이 매칭되지 않은 질의에는 빈 결과를 돌려주고(그 질의의 검색은 원래와 완전히 같음), 매칭된 질의에는 매칭 개념
  (+ 1홉 관련 개념)이 나오는 청크를 번역 질의와의 코사인 순으로 돌려주는 추가 후보 공급원.
- 개념 -> 청크 집합은 색인 때 기계적으로 만든다: 원문 또는 영어 텍스트에 별칭이 나오면 그 개념의 청크다. 청크 ID를 손으로
  적지 않는다.
- 영어 dense 다리의 임베더(bge-m3 한 벌)와 저장된 청크 임베딩(`DenseRetriever.emb`, 정규화됨 -> 내적 = 코사인, 정확 계산)을
  그대로 쓴다.
- 질의 번역은 같은 캐시 번역기를 쓰되 피벗의 query_log에는 기록하지 않아, 저장되는 번역 통계는 질의당 1건 그대로다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ragbench.concepts import Concept, ConceptMatch, ConceptMatcher, alias_in_text
from ragbench.retrieval.base import Hit


class ConceptCandidateRetriever:
    name = "concept_dense"

    def __init__(self, concepts: list[Concept], dense, translator, english_chunks_path: str | Path | None,
                 top_n: int = 10, dense_top: int = 1, dense_min: float = 0.55, skip_english: bool = False,
                 bundle: str = ""):
        self.concepts, self.dense, self.translator = concepts, dense, translator
        self.english_chunks_path, self.top_n, self.skip_english, self.bundle = english_chunks_path, top_n, skip_english, bundle
        # 임베더는 dense 다리의 것을 공유한다 (페이지 임베딩·질의 임베딩 모두 같은 모델)
        self.matcher = ConceptMatcher(concepts, embedder=getattr(dense, "embedder", None), dense_top=dense_top, dense_min=dense_min)
        self.chunk_sets: dict[str, set[str]] = {}
        self.row: dict[str, int] = {}
        self.last_match: ConceptMatch = ConceptMatch()
        self.match_log: list[dict[str, Any]] = []

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        texts = {c["chunk_id"]: [c["text"]] for c in chunks}
        if self.english_chunks_path:
            with open(self.english_chunks_path, encoding="utf-8") as f:
                for r in map(json.loads, filter(str.strip, f)):
                    if r["chunk_id"] in texts:
                        texts[r["chunk_id"]].append(r["text"])
        self.chunk_sets = {c.id: set() for c in self.concepts}
        for cid, ts in texts.items():
            for c in self.concepts:
                if any(alias_in_text(form, lang, t) for lang, form in c.aliases() for t in ts):
                    self.chunk_sets[c.id].add(cid)
        self.row = {cid: i for i, cid in enumerate(c["chunk_id"] for c in chunks)}
        self.matcher.index()
        per = {c.id: len(self.chunk_sets[c.id]) for c in self.concepts}
        # 전체 청크의 15%를 넘는 개념은 별칭이 너무 일반적일 가능성이 크다 (드라이런에서 확인용)
        return {"n_concepts": len(self.concepts), "chunks_per_concept": per,
                "concepts_over_15pct": [k for k, n in per.items() if chunks and n > 0.15 * len(chunks)]}

    def _english(self, query: str) -> str:
        if self.skip_english:
            from ragbench.validation import guess_lang
            if guess_lang(query) == "en":
                return query
        return self.translator.translate(query, "query")["text"]

    def search(self, query: str, k: int) -> list[Hit]:
        en = self._english(query)
        emb = getattr(self.dense, "emb", None)
        qvec = None
        if emb is not None and self.matcher.page_emb is not None:
            qvec = self.dense.embedder.encode([en])[0]
        m = self.matcher.match(query, en, qvec)
        self.last_match = m
        self.match_log.append({"query": query, "english": en, **m.to_dict()})
        if not m.ids or emb is None:
            return []
        # 주 개념의 청크를 먼저, 관련 개념만의 청크를 그 뒤에 두고 각 묶음 안에서는 코사인 순으로 정렬한다
        primary = set().union(*(self.chunk_sets.get(c, set()) for c in m.ids))
        secondary = set().union(*(self.chunk_sets.get(c, set()) for c in m.related)) - primary
        if qvec is None:
            qvec = self.dense.embedder.encode([en])[0]
        out: list[Hit] = []
        for group in (primary, secondary):
            rows = [self.row[c] for c in group if c in self.row]
            if not rows:
                continue
            ids = [self.dense.chunk_ids[r] for r in rows]
            scores = emb[rows] @ qvec
            out += sorted(zip(ids, (float(s) for s in scores)), key=lambda x: -x[1])
        return out[: min(k, self.top_n)]

    def augment_terms(self) -> list[str]:
        """Canonical English names of the concepts matched by the last query (related concepts excluded)."""
        return self.last_match.canonical_names

    def run_extra(self) -> dict[str, Any]:
        matched = [m for m in self.match_log if m["ids"]]
        return {"concept_bundle": self.bundle, "concept_n": len(self.concepts), "concept_queries": len(self.match_log),
                "concept_queries_matched": len(matched), "concept_queries_alias": sum(bool(m["alias"]) for m in matched),
                "concept_queries_dense": sum(bool(m["dense"]) for m in matched), "concept_matches": self.match_log}
