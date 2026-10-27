"""LlamaIndex and Haystack retrieval pipelines on the shared corpus and questions.

[EN]
- Same inputs for every system: our 346 chunks, the 90 questions, BAAI/bge-m3 embeddings, the reranker
  BAAI/bge-reranker-v2-m3 (cuda:0). Only the framework code differs. No query rewriting, no translation:
  the frameworks' standard retrieval components are used as documented.
- Variants (default = the usual out-of-the-box call with top_k 10; tuned = candidate lists of 50 per retriever,
  fused to 30 and reranked to 10, which is how our own pipeline is configured):
  LlamaIndex: li_vector, li_bm25, li_hybrid_rrf (default), li_hybrid_rerank (tuned)
  Haystack:   hs_bm25, hs_dense, hs_hybrid_rrf (default), hs_hybrid_rerank (tuned)
- Their BM25 uses the frameworks' own tokenization (English stemming / regex words), i.e. no Korean morphology.
- Usage: uv run python run_frameworks.py [llamaindex|haystack|all]

[KO]
- 모든 시스템에 같은 입력: 우리 청크 346개, 90문항, BAAI/bge-m3 임베딩, 리랭커 BAAI/bge-reranker-v2-m3(cuda:0).
  프레임워크 코드만 다르다. 질의 재작성도 번역도 없이 프레임워크의 표준 검색 컴포넌트를 문서대로 쓴다.
- 변형(default = top_k 10의 흔한 기본 호출, tuned = 검색기마다 후보 50개를 합쳐 30개로 만든 뒤 리랭커로 10개,
  우리 파이프라인의 구성과 같은 방식):
  LlamaIndex: li_vector, li_bm25, li_hybrid_rrf(default), li_hybrid_rerank(tuned)
  Haystack:   hs_bm25, hs_dense, hs_hybrid_rrf(default), hs_hybrid_rerank(tuned)
- 이들의 BM25는 프레임워크 자체 토큰화(영어 어간 추출 / 정규식 단어)를 쓰므로 한국어 형태소 분석이 없다.
- 사용: uv run python run_frameworks.py [llamaindex|haystack|all]
"""

from __future__ import annotations

import sys
import time

from cmp_common import evaluate_system, load_corpus, load_qa

DEVICE = "cuda:0"
EMB = "BAAI/bge-m3"
RERANK = "BAAI/bge-reranker-v2-m3"


def run_llamaindex(corpus, qa):
    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.core.llms.mock import MockLLM
    from llama_index.core.postprocessor import SentenceTransformerRerank
    from llama_index.core.retrievers import QueryFusionRetriever
    from llama_index.core.schema import QueryBundle, TextNode
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.retrievers.bm25 import BM25Retriever

    Settings.llm = MockLLM()                       # 질의 재작성을 쓰지 않으므로 LLM은 호출되지 않는다 (기본값 OpenAI를 피하기 위한 자리 채움)
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMB, device=DEVICE, max_length=512)
    nodes = [TextNode(id_=c["id"], text=c["text"]) for c in corpus]
    t0 = time.perf_counter()
    index = VectorStoreIndex(nodes)
    print(f"llamaindex index built in {time.perf_counter() - t0:.1f}s", flush=True)

    def to_hits(nws):
        return [(n.node.node_id, n.score or 0.0) for n in nws]

    def vector(k):
        return index.as_retriever(similarity_top_k=k)

    def bm25(k):
        return BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=k)

    def fusion(k_each, k_out):
        return QueryFusionRetriever([vector(k_each), bm25(k_each)], similarity_top_k=k_out, num_queries=1, mode="reciprocal_rerank",
                                    use_async=False, llm=MockLLM())

    v10, b10, f_default = vector(10), bm25(10), fusion(10, 10)
    f_tuned = fusion(50, 30)
    reranker = SentenceTransformerRerank(model=RERANK, top_n=10, device=DEVICE)
    evaluate_system("li_vector", "LlamaIndex", "VectorStoreIndex, bge-m3, top 10", lambda q, k: to_hits(v10.retrieve(q)), qa)
    evaluate_system("li_bm25", "LlamaIndex", "BM25Retriever defaults (English stemmer), top 10", lambda q, k: to_hits(b10.retrieve(q)), qa)
    evaluate_system("li_hybrid_rrf", "LlamaIndex", "QueryFusionRetriever (vector + BM25, reciprocal rank fusion), top 10 each, fused 10",
                    lambda q, k: to_hits(f_default.retrieve(q)), qa)
    evaluate_system("li_hybrid_rerank", "LlamaIndex", "QueryFusionRetriever 50 each -> 30, SentenceTransformerRerank bge-reranker-v2-m3 -> 10",
                    lambda q, k: to_hits(reranker.postprocess_nodes(f_tuned.retrieve(q), QueryBundle(q))), qa)


def run_haystack(corpus, qa):
    from haystack import Document
    from haystack.components.joiners import DocumentJoiner
    from haystack.components.retrievers.in_memory import InMemoryBM25Retriever, InMemoryEmbeddingRetriever
    from haystack.document_stores.in_memory import InMemoryDocumentStore
    from haystack.utils import ComponentDevice
    from haystack_integrations.components.embedders.sentence_transformers import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
    from haystack_integrations.components.rankers.sentence_transformers import SentenceTransformersSimilarityRanker

    device = ComponentDevice.from_str(DEVICE)
    store = InMemoryDocumentStore()
    docs = [Document(id=c["id"], content=c["text"]) for c in corpus]
    t0 = time.perf_counter()
    doc_emb = SentenceTransformersDocumentEmbedder(model=EMB, device=device)
    doc_emb.warm_up()
    store.write_documents(doc_emb.run(documents=docs)["documents"])
    print(f"haystack index built in {time.perf_counter() - t0:.1f}s", flush=True)
    text_emb = SentenceTransformersTextEmbedder(model=EMB, device=device)
    text_emb.warm_up()
    bm25 = InMemoryBM25Retriever(document_store=store)
    dense = InMemoryEmbeddingRetriever(document_store=store)
    ranker = SentenceTransformersSimilarityRanker(model=RERANK, top_k=10, device=device)
    ranker.warm_up()

    def hits(documents):
        return [(d.id, d.score or 0.0) for d in documents]

    def s_bm25(q, k):
        return hits(bm25.run(query=q, top_k=10)["documents"])

    def s_dense(q, k):
        return hits(dense.run(query_embedding=text_emb.run(text=q)["embedding"], top_k=10)["documents"])

    def hybrid(q, each, out):
        a = bm25.run(query=q, top_k=each)["documents"]
        b = dense.run(query_embedding=text_emb.run(text=q)["embedding"], top_k=each)["documents"]
        return DocumentJoiner(join_mode="reciprocal_rank_fusion", top_k=out).run(documents=[a, b])["documents"]

    evaluate_system("hs_bm25", "Haystack", "InMemoryBM25Retriever defaults, top 10", s_bm25, qa)
    evaluate_system("hs_dense", "Haystack", "InMemoryEmbeddingRetriever, bge-m3, top 10", s_dense, qa)
    evaluate_system("hs_hybrid_rrf", "Haystack", "BM25 + embedding retrievers joined by DocumentJoiner reciprocal_rank_fusion, top 10 each, fused 10",
                    lambda q, k: hits(hybrid(q, 10, 10)), qa)
    evaluate_system("hs_hybrid_rerank", "Haystack", "BM25 + embedding 50 each, RRF -> 30, SentenceTransformersSimilarityRanker bge-reranker-v2-m3 -> 10",
                    lambda q, k: hits(ranker.run(query=q, documents=hybrid(q, 50, 30), top_k=10)["documents"]), qa)


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    corpus, qa = load_corpus(), load_qa()
    if which in ("llamaindex", "all"):
        run_llamaindex(corpus, qa)
    if which in ("haystack", "all"):
        run_haystack(corpus, qa)


if __name__ == "__main__":
    main()
