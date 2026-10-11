### overall

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.404 | 0.430 | 0.421 | 45 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.411 | 0.425 | 0.410 | 45 |
| s1_bm25_subword | subword | False | bm25 | - | 0.400 | 0.428 | 0.422 | 45 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.511 | 0.505 | 0.510 | 45 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.511 | 0.505 | 0.510 | 45 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.411 | 0.428 | 0.426 | 45 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.615 | 0.702 | 0.631 | 45 |

### de->de

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.815 | 0.741 | 0.757 | 9 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.815 | 0.759 | 0.768 | 9 |
| s1_bm25_subword | subword | False | bm25 | - | 0.722 | 0.713 | 0.753 | 9 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.537 | 0.659 | 0.634 | 9 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.537 | 0.659 | 0.634 | 9 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.796 | 0.787 | 0.783 | 9 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.722 | 0.846 | 0.796 | 9 |

### de->en

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.417 | 0.531 | 0.484 | 4 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.417 | 0.528 | 0.483 | 4 |
| s1_bm25_subword | subword | False | bm25 | - | 0.500 | 0.500 | 0.491 | 4 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.417 | 0.417 | 0.510 | 4 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.417 | 0.417 | 0.510 | 4 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.417 | 0.417 | 0.452 | 4 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.500 | 0.542 | 0.510 | 4 |

### de->ko

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_bm25_subword | subword | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.750 | 0.750 | 0.740 | 2 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.750 | 0.750 | 0.740 | 2 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.750 | 1.000 | 0.880 | 2 |

### en->de

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.000 | 0.036 | 0.027 | 4 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.083 | 0.050 | 0.031 | 4 |
| s1_bm25_subword | subword | False | bm25 | - | 0.083 | 0.083 | 0.065 | 4 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.000 | 0.000 | 0.000 | 4 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.000 | 0.000 | 0.000 | 4 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.000 | 0.000 | 0.000 | 4 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.167 | 0.083 | 0.074 | 4 |

### en->en

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.741 | 0.889 | 0.820 | 9 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.741 | 0.833 | 0.779 | 9 |
| s1_bm25_subword | subword | False | bm25 | - | 0.741 | 0.889 | 0.834 | 9 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.796 | 0.701 | 0.742 | 9 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.796 | 0.701 | 0.742 | 9 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.796 | 0.889 | 0.838 | 9 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.907 | 0.852 | 0.846 | 9 |

### en->ko

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_bm25_subword | subword | False | bm25 | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 1.000 | 1.000 | 0.939 | 2 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 1.000 | 1.000 | 0.939 | 2 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.000 | 0.000 | 0.000 | 2 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.750 | 1.000 | 0.807 | 2 |

### ko->de

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.000 | 0.000 | 0.000 | 5 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.000 | 0.000 | 0.000 | 5 |
| s1_bm25_subword | subword | False | bm25 | - | 0.000 | 0.000 | 0.000 | 5 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.167 | 0.267 | 0.149 | 5 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.167 | 0.267 | 0.149 | 5 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.000 | 0.000 | 0.000 | 5 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.167 | 0.400 | 0.176 | 5 |

### ko->en

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.000 | 0.024 | 0.054 | 7 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.000 | 0.000 | 0.000 | 7 |
| s1_bm25_subword | subword | False | bm25 | - | 0.000 | 0.000 | 0.000 | 7 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.429 | 0.260 | 0.306 | 7 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.429 | 0.260 | 0.306 | 7 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.000 | 0.024 | 0.057 | 7 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.571 | 0.686 | 0.612 | 7 |

### ko->ko

| exp_id | bm25_tokenizer | exact_search | method | rerank_model | recall@5 | mrr@10 | ndcg@10 | n |
|---|---|---|---|---|---|---|---|---|
| s1_bm25_whitespace | whitespace | False | bm25 | - | 0.833 | 0.750 | 0.776 | 3 |
| s1_bm25_kiwi | kiwi | False | bm25 | - | 0.833 | 0.833 | 0.827 | 3 |
| s1_bm25_subword | subword | False | bm25 | - | 0.833 | 0.833 | 0.827 | 3 |
| s1_dense_bge_m3_exact | whitespace | True | dense | - | 0.667 | 0.714 | 0.751 | 3 |
| s1_dense_bge_m3 | whitespace | False | dense | - | 0.667 | 0.714 | 0.751 | 3 |
| s1_hybrid_rrf | kiwi | False | hybrid | - | 0.833 | 0.778 | 0.793 | 3 |
| s1_hybrid_rrf_rerank | kiwi | False | hybrid_rerank | BAAI/bge-reranker-v2-m3 | 0.833 | 1.000 | 0.920 | 3 |
