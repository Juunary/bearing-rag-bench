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


def _embedder(cfg: ExperimentConfig):
    """임베더: bge-m3 기본값이면 None(DenseRetriever가 예전처럼 만든다), 풀링·접두사·dtype이 다르면 그 설정으로 만든다."""
    r = cfg.retrieval
    if (r.embedding_pooling, r.embedding_query_prefix, r.embedding_doc_prefix, r.embedding_dtype, r.embedding_max_length) == ("cls", "", "", None, 512):
        return None
    from ragbench.embedding import Embedder
    return Embedder(r.embedding_model, pooling=r.embedding_pooling, query_prefix=r.embedding_query_prefix,
                    doc_prefix=r.embedding_doc_prefix, dtype=r.embedding_dtype, max_length=r.embedding_max_length)


def _dense(cfg: ExperimentConfig, translator=None):
    """dense 검색기: 영어 피벗이면 영어 번역 청크를 임베딩(캐시 키 "_en")하고 질의를 번역해 검색한다."""
    from ragbench.retrieval.dense import DenseRetriever

    r = cfg.retrieval
    emb = _embedder(cfg)
    if not r.dense_english_pivot:
        return DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search, chunk_set_id=_index_set_id(cfg), embedder=emb)
    from ragbench.retrieval.bm25_en import EnglishPivotRetriever

    inner = DenseRetriever(model_name=r.embedding_model, hnsw=r.hnsw, exact=r.exact_search, chunk_set_id=_index_set_id(cfg) + "_en", embedder=emb)
    return EnglishPivotRetriever(translator or _translator(cfg), _english_chunks_path(cfg), inner, skip_english=r.translate_skip_english)


CONCEPT_MODES = ("pool", "pool_query", "rrf_query")


def _concept(cfg: ExperimentConfig, dense_pivot, translator):
    """개념 경유 후보 검색기: 영어 dense 다리(EnglishPivotRetriever)의 안쪽 DenseRetriever와 임베더를 같이 쓴다."""
    from ragbench.concepts import load_concepts
    from ragbench.config import REPO_ROOT
    from ragbench.retrieval.concept import ConceptCandidateRetriever

    r = cfg.retrieval
    if r.concept_mode not in CONCEPT_MODES:
        raise ValueError(f"concept_mode must be one of {CONCEPT_MODES}, got {r.concept_mode!r}")
    if r.method != "hybrid_rerank" or not r.dense_english_pivot:
        raise ValueError("concept_bundle needs method 'hybrid_rerank' with dense_english_pivot")
    return ConceptCandidateRetriever(load_concepts(REPO_ROOT / r.concept_bundle), dense_pivot.inner, translator,
                                     _english_chunks_path(cfg), top_n=r.concept_pool_n, dense_top=r.concept_dense_top,
                                     dense_min=r.concept_dense_min, skip_english=r.translate_skip_english, bundle=r.concept_bundle)


def _rerank(cfg: ExperimentConfig, base, translator=None, concept=None):
    from ragbench.retrieval.rerank import CrossEncoder, RerankRetriever

    r = cfg.retrieval
    # 리랭커 종류·장치·지시문이 기본값이 아니면 cross-encoder를 여기서 만들어 넘긴다 (기본값이면 RerankRetriever가 예전처럼 만든다)
    ce = None
    if r.rerank_kind != "seq_cls" or r.rerank_device or r.rerank_instruction:
        ce = CrossEncoder(r.rerank_model, device=r.rerank_device, kind=r.rerank_kind, instruction=r.rerank_instruction)
    # 개념 검색기: pool·pool_query는 리랭커 후보를 보강하고, pool_query·rrf_query는 리랭커 질의에 정식 명칭을 붙인다
    extra = {"pool_extra": concept if concept is not None and r.concept_mode in ("pool", "pool_query") else None,
             "pool_extra_n": r.concept_pool_n,
             "query_augment": concept if concept is not None and r.concept_mode in ("pool_query", "rrf_query") else None}
    if r.rerank_text == "english":
        # 리랭커가 영어 번역 청크와 영어로 번역한 질의를 읽는다 (후보 ID는 그대로)
        return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n, cross_encoder=ce,
                               english_chunks_path=_english_chunks_path(cfg), query_translator=translator, **extra)
    return RerankRetriever(base, model_name=r.rerank_model, top_n=r.rerank_top_n, cross_encoder=ce, **extra)


def build_retriever(cfg: ExperimentConfig):
    r = cfg.retrieval
    if r.concept_mode and not r.concept_bundle:
        raise ValueError("concept_mode needs concept_bundle")
    # 번역기는 한 실험 안에서 하나만 만들어 BM25·dense·리랭커가 모델 한 벌과 캐시를 공유한다
    needs_translator = r.bm25_english_pivot or r.dense_english_pivot or r.rerank_text == "english"
    tr = _translator(cfg) if needs_translator and r.method != "bm25" else None
    if r.method == "bm25":
        return _bm25(cfg)
    if r.method == "dense":
        return _dense(cfg, tr)
    if r.method == "dense_rerank":
        # dense 후보 rerank_top_n개를 바로 리랭커에 넣는다 (BM25·RRF 없음, AutoRAG 최고 파이프라인과 같은 구조)
        return _rerank(cfg, _dense(cfg, tr), tr)
    if r.method in ("hybrid", "hybrid_rerank"):
        from ragbench.retrieval.hybrid import RRFRetriever
        parts = [_bm25(cfg, tr)]
        if r.bm25_include_original:
            # 3중 RRF: 영어 BM25 + 원문 BM25(단일 언어에 강함) + dense
            from ragbench.retrieval.bm25 import BM25Retriever
            parts.append(BM25Retriever(tokenizer=r.bm25_original_tokenizer, k1=r.bm25_k1, b=r.bm25_b))
        dense = _dense(cfg, tr)
        parts.append(dense)
        concept = _concept(cfg, dense, tr) if r.concept_bundle else None
        if concept is not None and r.concept_mode == "rrf_query":
            # 셋째 다리: 매칭된 질의에서만 후보를 내고, 아니면 빈 목록이라 RRF 결과가 2중 RRF와 같다
            parts.append(concept)
        base = RRFRetriever(parts, rrf_k=r.rrf_k, candidates=r.fusion_candidates)
        if r.method == "hybrid":
            return base
        return _rerank(cfg, base, tr, concept)
    raise ValueError(f"unknown retrieval method {r.method!r}")


def translators_of(retriever) -> list:
    """Every distinct Translator object inside a retriever tree (BM25 pivot, query expansion, reranker input)."""
    found, stack, seen = [], [retriever], set()
    while stack:
        r = stack.pop()
        if id(r) in seen:
            continue
        seen.add(id(r))
        for attr in ("translator", "query_translator"):
            t = getattr(r, attr, None)
            if t is not None and all(t is not f for f in found):
                found.append(t)
        stack.extend(getattr(r, "retrievers", []))
        stack.extend(x for x in (getattr(r, "base", None), getattr(r, "en", None), getattr(r, "inner", None),
                                 getattr(r, "pool_extra", None), getattr(r, "query_augment", None)) if x is not None)
    return found


def share_translator_model(retriever, generator) -> int:
    """Let every translator use the generator's model when it is the same model, then load any that remain.

    Serving: the translator otherwise loads its own copy on the first uncached query; loading here makes an
    out-of-memory error show up at start-up instead of on a user request. Returns the number of translators sharing.
    """
    shared = 0
    for t in translators_of(retriever):
        if t.use_generator(generator):
            shared += 1
        else:
            t._generator()
    return shared


def use_cold_translation_cache(retriever) -> int:
    """Swap every translator's cache for an empty in-memory one (benchmarks: translation latency must not be hidden by the cache)."""
    from ragbench.cache import LLMCache

    ts = translators_of(retriever)
    for t in ts:
        t.cache = LLMCache(":memory:")
    return len(ts)
