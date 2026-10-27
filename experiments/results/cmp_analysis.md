# Comparison with LlamaIndex, Haystack and AutoRAG (90 questions, 346 chunks)

clusters (primary-evidence documents): 39

## 1. All systems

tier: default = framework defaults of the component, tuned = hybrid + reranker or English pivot, search = AutoRAG module of its search.

| system | tier | R@5 | MRR@10 | nDCG@10 | mono | cross | p50 ms (not comparable) |
|---|---|---|---|---|---|---|---|
| this repo: BM25 whitespace | default | 0.313 | 0.394 | 0.328 | 0.772 | 0.106 | 0.1 |
| this repo: BM25 kiwi | default | 0.330 | 0.405 | 0.336 | 0.788 | 0.110 | 0.2 |
| this repo: dense bge-m3 | default | 0.514 | 0.506 | 0.487 | 0.760 | 0.350 | 8.4 |
| this repo: RRF | default | 0.341 | 0.433 | 0.360 | 0.825 | 0.128 | 8.7 |
| this repo: RRF + reranker | tuned | 0.608 | 0.650 | 0.586 | 0.864 | 0.448 | 168.9 |
| this repo: English BM25 | tuned | 0.745 | 0.768 | 0.749 | 0.702 | 0.772 | 375.6 |
| this repo: English RRF + reranker (original text) | tuned | 0.679 | 0.700 | 0.656 | 0.876 | 0.545 | 175.4 |
| this repo: English RRF + reranker (English text) | tuned | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 | 184.2 |
| LlamaIndex: BM25 | default | 0.323 | 0.379 | 0.323 | 0.755 | 0.107 | 0.4 |
| LlamaIndex: vector | default | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 | 18.4 |
| LlamaIndex: hybrid (reciprocal rerank fusion) | default | 0.434 | 0.471 | 0.444 | 0.811 | 0.261 | 19.0 |
| LlamaIndex: hybrid + reranker | tuned | 0.617 | 0.654 | 0.592 | 0.863 | 0.456 | 521.1 |
| Haystack: BM25 | default | 0.322 | 0.380 | 0.315 | 0.761 | 0.091 | 6.6 |
| Haystack: dense | default | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 | 23.1 |
| Haystack: hybrid (RRF) | default | 0.419 | 0.470 | 0.425 | 0.821 | 0.227 | 30.5 |
| Haystack: hybrid + reranker | tuned | 0.612 | 0.659 | 0.591 | 0.860 | 0.456 | 580.2 |
| AutoRAG: BM25 space | search | 0.309 | 0.365 | 0.312 | 0.732 | 0.103 | 0.1 |
| AutoRAG: BM25 porter_stemmer | search | 0.320 | 0.350 | 0.310 | 0.732 | 0.098 | 0.1 |
| AutoRAG: BM25 ko_kiwi | search | 0.333 | 0.400 | 0.333 | 0.791 | 0.104 | 15.9 |
| AutoRAG: vector | search | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 | 0.3 |
| AutoRAG: hybrid RRF | search | 0.397 | 0.441 | 0.407 | 0.817 | 0.203 | 0.1 |
| AutoRAG: hybrid CC (mm) | search | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 | 0.6 |
| AutoRAG: hybrid CC (z) | search | 0.484 | 0.509 | 0.465 | 0.825 | 0.284 | 0.6 |
| AutoRAG: hybrid CC (dbsf) | search | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 | 0.6 |
| AutoRAG: reranker FlagEmbedding (best pipeline) | search | 0.660 | 0.689 | 0.642 | 0.873 | 0.527 | 11.7 |
| AutoRAG: reranker SentenceTransformer | search | 0.660 | 0.689 | 0.642 | 0.873 | 0.527 | 6.0 |

## 2. Paired comparisons (nDCG@10, A - B; 12 comparisons chosen after the retrieval numbers were known, no multiplicity correction)

| A | B | mean diff | 95% CI (question) | 95% CI (document cluster) | better/worse/tie | sign-test p |
|---|---|---|---|---|---|---|
| cmp_li_vector | v2_b_dense | -0.000 | -0.001 .. +0.000 | -0.001 .. +0.000 | 1/1/88 | 1.000 |
| cmp_hs_dense | v2_b_dense | -0.000 | -0.001 .. +0.000 | -0.001 .. +0.000 | 1/1/88 | 1.000 |
| cmp_li_bm25 | v2_b_bm25_whitespace | -0.005 | -0.028 .. +0.018 | -0.027 .. +0.017 | 7/10/73 | 0.629 |
| cmp_hs_bm25 | v2_b_bm25_whitespace | -0.013 | -0.030 .. +0.000 | -0.029 .. -0.000 | 6/11/73 | 0.332 |
| cmp_li_hybrid_rerank | v2_b_rrf_rerank | +0.005 | -0.001 .. +0.017 | -0.001 .. +0.018 | 4/4/82 | 1.000 |
| cmp_hs_hybrid_rerank | v2_b_rrf_rerank | +0.004 | -0.015 .. +0.027 | -0.015 .. +0.027 | 2/4/84 | 0.688 |
| cmp_ar_rerank_flag | v2_b_rrf_rerank | +0.056 | +0.024 .. +0.094 | +0.025 .. +0.094 | 18/5/67 | 0.011 |
| cmp_ar_rerank_flag | cmp_li_hybrid_rerank | +0.050 | +0.019 .. +0.088 | +0.022 .. +0.086 | 17/4/69 | 0.007 |
| v2_x2_rerank_en_text | cmp_ar_rerank_flag | +0.253 | +0.183 .. +0.325 | +0.169 .. +0.333 | 51/9/30 | 0.000 |
| v2_x2_rerank_en_text | cmp_li_hybrid_rerank | +0.303 | +0.230 .. +0.379 | +0.214 .. +0.385 | 56/7/27 | 0.000 |
| v2_x2_rerank_en_text | cmp_hs_hybrid_rerank | +0.304 | +0.231 .. +0.379 | +0.217 .. +0.387 | 56/7/27 | 0.000 |
| v2_b_bm25_en | cmp_ar_bm25_ko_kiwi | +0.415 | +0.311 .. +0.519 | +0.308 .. +0.519 | 63/11/16 | 0.000 |

## 3. nDCG@10 per language pair (10 questions each)

| system | de->de | de->en | de->ko | en->de | en->en | en->ko | ko->de | ko->en | ko->ko |
|---|---|---|---|---|---|---|---|---|---|
| this repo: BM25 whitespace | 0.83 | 0.27 | 0.01 | 0.09 | 0.83 | 0.23 | 0.00 | 0.04 | 0.65 |
| this repo: BM25 kiwi | 0.83 | 0.31 | 0.02 | 0.09 | 0.83 | 0.24 | 0.00 | 0.00 | 0.70 |
| this repo: dense bge-m3 | 0.81 | 0.45 | 0.29 | 0.16 | 0.71 | 0.68 | 0.19 | 0.33 | 0.76 |
| this repo: RRF + reranker | 0.88 | 0.58 | 0.38 | 0.20 | 0.86 | 0.73 | 0.21 | 0.59 | 0.85 |
| this repo: English BM25 | 0.69 | 0.78 | 0.73 | 0.91 | 0.85 | 0.88 | 0.78 | 0.55 | 0.56 |
| this repo: English RRF + reranker (original text) | 0.88 | 0.67 | 0.42 | 0.42 | 0.87 | 0.83 | 0.25 | 0.68 | 0.88 |
| this repo: English RRF + reranker (English text) | 0.87 | 0.93 | 0.83 | 0.97 | 0.92 | 0.91 | 0.84 | 0.87 | 0.92 |
| LlamaIndex: BM25 | 0.85 | 0.26 | 0.01 | 0.09 | 0.75 | 0.24 | 0.00 | 0.04 | 0.66 |
| LlamaIndex: vector | 0.81 | 0.45 | 0.29 | 0.16 | 0.71 | 0.68 | 0.19 | 0.33 | 0.76 |
| LlamaIndex: hybrid + reranker | 0.88 | 0.58 | 0.38 | 0.20 | 0.86 | 0.73 | 0.25 | 0.59 | 0.85 |
| Haystack: BM25 | 0.84 | 0.25 | 0.02 | 0.08 | 0.83 | 0.20 | 0.00 | 0.00 | 0.61 |
| Haystack: dense | 0.81 | 0.45 | 0.29 | 0.16 | 0.71 | 0.68 | 0.19 | 0.33 | 0.76 |
| Haystack: hybrid + reranker | 0.88 | 0.58 | 0.34 | 0.20 | 0.86 | 0.80 | 0.25 | 0.57 | 0.84 |
| AutoRAG: BM25 ko_kiwi | 0.83 | 0.31 | 0.02 | 0.07 | 0.83 | 0.23 | 0.00 | 0.00 | 0.71 |
| AutoRAG: vector | 0.81 | 0.45 | 0.29 | 0.16 | 0.71 | 0.68 | 0.19 | 0.33 | 0.76 |
| AutoRAG: reranker FlagEmbedding (best pipeline) | 0.88 | 0.65 | 0.38 | 0.36 | 0.86 | 0.84 | 0.25 | 0.68 | 0.88 |

## 4. Generation (base bf16 Qwen3-4B-Instruct-2507, prompt cite_v1, top 5) and judge (Qwen3-8B)

See run_judge.py for the outcome classes. cites_gold = cited a gold chunk; judged rates are among the answers each dimension applies to.

| retrieval feeding the generator | gold in context | cites_gold | faithfulness | correctness | answer relevance | refused |
|---|---|---|---|---|---|---|
| this repo (English RRF + reranker, original text) | 0.833 | 0.744 | 0.881 | 0.857 | 0.929 | 0.000 |
| this repo (English RRF + reranker, English text) | 0.989 | 0.933 | 0.955 | 0.886 | 0.977 | 0.000 |
| LlamaIndex hybrid + reranker | 0.778 | 0.733 | 0.911 | 0.797 | 0.937 | 0.000 |
| Haystack hybrid + reranker | 0.778 | 0.733 | 0.912 | 0.812 | 0.950 | 0.000 |
| AutoRAG best pipeline | 0.811 | 0.744 | 0.915 | 0.817 | 0.951 | 0.000 |

## 5. Paired generation comparisons (A - B, 95% interval by primary-evidence document; pairs chosen after the generation means were known, no multiplicity correction)

| A | B | metric | mean diff | 95% CI (document cluster) | better/worse/tie | n |
|---|---|---|---|---|---|---|
| cmp_ar | cmp_li | gold_in_context | +0.033 | +0.000 .. +0.076 | 3/0/87 | 90 |
| cmp_ar | cmp_li | cites_gold | +0.011 | -0.038 .. +0.062 | 3/2/85 | 90 |
| cmp_ar | cmp_li | faithfulness | +0.000 | -0.060 .. +0.063 | 3/3/73 | 79 |
| cmp_ar | cmp_li | correctness | +0.025 | -0.035 .. +0.089 | 4/2/73 | 79 |
| cmp_ar | cmp_hs | gold_in_context | +0.033 | +0.000 .. +0.076 | 3/0/87 | 90 |
| cmp_ar | cmp_hs | cites_gold | +0.011 | -0.038 .. +0.062 | 3/2/85 | 90 |
| cmp_ar | cmp_hs | faithfulness | +0.000 | -0.049 .. +0.050 | 2/2/76 | 80 |
| cmp_ar | cmp_hs | correctness | +0.000 | -0.059 .. +0.063 | 3/3/74 | 80 |
| cmp_li | cmp_hs | gold_in_context | +0.000 | +0.000 .. +0.000 | 0/0/90 | 90 |
| cmp_li | cmp_hs | cites_gold | +0.000 | +0.000 .. +0.000 | 0/0/90 | 90 |
| cmp_li | cmp_hs | faithfulness | +0.000 | -0.038 .. +0.036 | 1/1/77 | 79 |
| cmp_li | cmp_hs | correctness | -0.013 | -0.069 .. +0.042 | 2/3/74 | 79 |
| ret_x2_rerank_en_text | cmp_ar | gold_in_context | +0.178 | +0.077 .. +0.277 | 17/1/72 | 90 |
| ret_x2_rerank_en_text | cmp_ar | cites_gold | +0.189 | +0.106 .. +0.267 | 18/1/71 | 90 |
| ret_x2_rerank_en_text | cmp_ar | faithfulness | +0.049 | -0.025 .. +0.127 | 6/2/73 | 81 |
| ret_x2_rerank_en_text | cmp_ar | correctness | +0.086 | +0.012 .. +0.162 | 9/2/70 | 81 |
| ret_x2_rerank_en_text | cmp_li | gold_in_context | +0.211 | +0.110 .. +0.307 | 20/1/69 | 90 |
| ret_x2_rerank_en_text | cmp_li | cites_gold | +0.200 | +0.115 .. +0.278 | 19/1/70 | 90 |
| ret_x2_rerank_en_text | cmp_li | faithfulness | +0.051 | -0.026 .. +0.132 | 6/2/70 | 78 |
| ret_x2_rerank_en_text | cmp_li | correctness | +0.115 | +0.027 .. +0.211 | 12/3/63 | 78 |
| ret_x2_rerank_en_text | cmp_hs | gold_in_context | +0.211 | +0.110 .. +0.307 | 20/1/69 | 90 |
| ret_x2_rerank_en_text | cmp_hs | cites_gold | +0.200 | +0.115 .. +0.278 | 19/1/70 | 90 |
| ret_x2_rerank_en_text | cmp_hs | faithfulness | +0.051 | -0.025 .. +0.130 | 6/2/71 | 79 |
| ret_x2_rerank_en_text | cmp_hs | correctness | +0.089 | +0.000 .. +0.187 | 11/4/64 | 79 |
| ret_b_rrf_en_rerank | cmp_ar | gold_in_context | +0.022 | +0.000 .. +0.056 | 2/0/88 | 90 |
| ret_b_rrf_en_rerank | cmp_ar | cites_gold | +0.000 | -0.047 .. +0.044 | 2/2/86 | 90 |
| ret_b_rrf_en_rerank | cmp_ar | faithfulness | -0.037 | -0.092 .. +0.013 | 1/4/77 | 82 |
| ret_b_rrf_en_rerank | cmp_ar | correctness | +0.037 | -0.013 .. +0.087 | 4/1/77 | 82 |
