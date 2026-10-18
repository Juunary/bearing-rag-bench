"""Build a retriever from an ExperimentConfig (shared by experiment runners and the pipeline).

[EN]
- Role: one place that maps retrieval.method ("bm25", "dense", "hybrid", "hybrid_rerank") to the
  concrete retriever objects, so the experiment scripts and the serving pipeline cannot drift apart.
- Heavy imports (torch models) happen lazily inside the branches that need them.

[KO]
- 역할: retrieval.method("bm25", "dense", "hybrid", "hybrid_rerank")를 실제 검색기 객체로 바꾸는 곳을
  한 군데로 모아, 실험 스크립트와 서비스 파이프라인이 서로 어긋나지 않게 한다.
- torch 모델 같은 무거운 import는 필요한 분기 안에서만 지연 로드한다.
"""

from __future__ import annotations

from ragbench.chunking import chunk_set_id
from ragbench.config import ExperimentConfig


def _bm25(cfg: ExperimentConfig):
    """BM25 검색기 한 곳에서 만든다: 영어 피벗이면 번역본 색인, 아니면 기존 BM25 (hybrid 분기도 같이 쓴다)."""
    r = cfg.retrieval
    if r.bm25_english_pivot:
        # 번역 모듈은 영어 피벗을 켰을 때만 import한다 (기존 실험 경로에 영향 없음)
        from ragbench.config import REPO_ROOT
        from ragbench.retrieval.bm25_en import EnglishBM25Retriever
        from ragbench.translate import Translator
        from ragbench.translate import MODEL, load_glossary
        glossary = load_glossary(REPO_ROOT / "data" / "glossary.json") if r.translate_glossary else None
        suffix = "_gl" if r.translate_glossary else ""      # 용어집으로 번역한 청크는 별도 파일
        return EnglishBM25Retriever(Translator(REPO_ROOT / "logs" / "translate_cache.sqlite", model_name=r.translate_model or MODEL,
                                               glossary=glossary),
                                    REPO_ROOT / "data" / "processed" / f"chunks_en_{chunk_set_id(cfg.chunking)}{suffix}.jsonl",
                                    tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b, skip_english=r.translate_skip_english)
    from ragbench.retrieval.bm25 import BM25Retriever
    return BM25Retriever(tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b)


def build_retriever(cfg: ExperimentConfig):
    r = cfg.retrieval
    if r.method == "bm25":
        return _bm25(cfg)
    if r.method == "dense":
        from ragbench.retrieval.dense import DenseRetriever
        return DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search,
                              chunk_set_id=chunk_set_id(cfg.chunking))
    if r.method in ("hybrid", "hybrid_rerank"):
        from ragbench.retrieval.dense import DenseRetriever
        from ragbench.retrieval.hybrid import RRFRetriever
        base = RRFRetriever(
            [_bm25(cfg),
             DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search,
                            chunk_set_id=chunk_set_id(cfg.chunking))],
            rrf_k=r.rrf_k, candidates=r.fusion_candidates)
        if r.method == "hybrid":
            return base
        from ragbench.retrieval.rerank import RerankRetriever
        return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n)
    raise ValueError(f"unknown retrieval method {r.method!r}")
