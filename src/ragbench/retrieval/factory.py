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


def _translator(cfg: ExperimentConfig):
    """번역기 한 개를 만든다 (같은 실험 안의 BM25와 리랭커가 모델 한 벌과 캐시를 공유한다)."""
    from ragbench.config import REPO_ROOT
    from ragbench.translate import MODEL, Translator, load_glossary

    r = cfg.retrieval
    glossary = load_glossary(REPO_ROOT / "data" / "glossary.json") if r.translate_glossary else None
    return Translator(REPO_ROOT / "logs" / "translate_cache.sqlite", model_name=r.translate_model or MODEL, glossary=glossary)


def _english_chunks_path(cfg: ExperimentConfig):
    from ragbench.config import REPO_ROOT

    suffix = "_gl" if cfg.retrieval.translate_glossary else ""      # 용어집으로 번역한 청크는 별도 파일
    return REPO_ROOT / "data" / "processed" / f"chunks_en_{chunk_set_id(cfg.chunking)}{suffix}.jsonl"


def _index_set_id(cfg: ExperimentConfig) -> str:
    """임베딩 캐시 키: 맥락 접두사를 붙인 텍스트는 같은 청크 세트라도 임베딩이 다르므로 키를 분리한다."""
    return chunk_set_id(cfg.chunking) + ("_ctx" if cfg.retrieval.contextual_prefix else "")


def _bm25(cfg: ExperimentConfig, translator=None):
    """BM25 검색기 한 곳에서 만든다: 영어 피벗이면 번역본 색인, 아니면 기존 BM25 (hybrid 분기도 같이 쓴다)."""
    r = cfg.retrieval
    if r.bm25_english_pivot:
        # 번역 모듈은 영어 피벗을 켰을 때만 import한다 (기존 실험 경로에 영향 없음)
        from ragbench.retrieval.bm25_en import EnglishBM25Retriever, ExpandedQueryRetriever
        tr = translator or _translator(cfg)
        en = EnglishBM25Retriever(tr, _english_chunks_path(cfg), tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b,
                                  skip_english=r.translate_skip_english)
        # 질의 확장: 영어 BM25를 감싸 번역 + 변형 질의(multi) 또는 가상 답변(hyde)으로 검색한다
        return ExpandedQueryRetriever(tr, en, r.query_expansion) if r.query_expansion else en
    from ragbench.retrieval.bm25 import BM25Retriever
    return BM25Retriever(tokenizer=r.bm25_tokenizer, k1=r.bm25_k1, b=r.bm25_b)


def build_retriever(cfg: ExperimentConfig):
    r = cfg.retrieval
    if r.method == "bm25":
        return _bm25(cfg)
    if r.method == "dense":
        from ragbench.retrieval.dense import DenseRetriever
        return DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search,
                              chunk_set_id=_index_set_id(cfg))
    if r.method in ("hybrid", "hybrid_rerank"):
        from ragbench.retrieval.dense import DenseRetriever
        from ragbench.retrieval.hybrid import RRFRetriever
        needs_translator = r.bm25_english_pivot or r.rerank_text == "english"
        tr = _translator(cfg) if needs_translator else None
        parts = [_bm25(cfg, tr)]
        if r.bm25_include_original:
            # 3중 RRF: 영어 BM25 + 원문 BM25(단일 언어에 강함) + dense
            from ragbench.retrieval.bm25 import BM25Retriever
            parts.append(BM25Retriever(tokenizer=r.bm25_original_tokenizer, k1=r.bm25_k1, b=r.bm25_b))
        parts.append(DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search, chunk_set_id=_index_set_id(cfg)))
        base = RRFRetriever(parts, rrf_k=r.rrf_k, candidates=r.fusion_candidates)
        if r.method == "hybrid":
            return base
        from ragbench.retrieval.rerank import RerankRetriever
        if r.rerank_text == "english":
            # 리랭커가 영어 번역 청크와 영어로 번역한 질의를 읽는다 (후보 ID는 그대로)
            return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n,
                                   english_chunks_path=_english_chunks_path(cfg), query_translator=tr)
        return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n)
    raise ValueError(f"unknown retrieval method {r.method!r}")
