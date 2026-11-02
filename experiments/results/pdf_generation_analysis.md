# PDF questions: generation and judging (48 questions)

## 1. Per condition

| condition | gold in context | cites gold | faithfulness (Qwen3-8B) | faithfulness (Granite) | correctness (Qwen3-8B) | correctness (Granite) | answer_relevance (Qwen3-8B) | answer_relevance (Granite) |
|---|---|---|---|---|---|---|---|---|
| RRF + reranker | 0.750 | 0.708 | 0.829 | 0.951 | 0.732 | 0.805 | 0.951 | 0.976 |
| best PDF retrieval | 0.917 | 0.875 | 0.978 | 0.978 | 0.889 | 0.956 | 0.978 | 0.978 |
| best PDF retrieval + table headers | 0.938 | 0.917 | 0.913 | 0.978 | 0.891 | 0.978 | 0.978 | 1.000 |

## 2. Correctness by evidence kind

| condition | judge | text | table | caption |
|---|---|---|---|---|
| RRF + reranker | Qwen3-8B | 0.696 (n=23) | 0.769 (n=13) | 0.800 (n=5) |
| RRF + reranker | Granite | 0.783 (n=23) | 0.846 (n=13) | 0.800 (n=5) |
| best PDF retrieval | Qwen3-8B | 0.875 (n=24) | 0.857 (n=14) | 1.000 (n=7) |
| best PDF retrieval | Granite | 1.000 (n=24) | 0.929 (n=14) | 0.857 (n=7) |
| best PDF retrieval + table headers | Qwen3-8B | 0.833 (n=24) | 0.933 (n=15) | 1.000 (n=7) |
| best PDF retrieval + table headers | Granite | 1.000 (n=24) | 0.933 (n=15) | 1.000 (n=7) |

## 3. Paired comparisons (A - B, 95% interval by question; no multiplicity correction)

| A | B | metric | mean diff | 95% CI | better/worse/tie | n |
|---|---|---|---|---|---|---|
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | gold_in_context | +0.167 | +0.042 .. +0.292 | 10/2/36 | 48 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | cites_gold | +0.167 | +0.042 .. +0.312 | 10/2/36 | 48 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | faithfulness (Qwen3-8B) | +0.150 | +0.050 .. +0.275 | 6/0/34 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | faithfulness (Granite) | +0.025 | -0.050 .. +0.100 | 2/1/37 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | correctness (Qwen3-8B) | +0.150 | +0.025 .. +0.275 | 7/1/32 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | correctness (Granite) | +0.150 | +0.025 .. +0.300 | 7/1/32 | 40 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | gold_in_context | +0.021 | +0.000 .. +0.062 | 1/0/47 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | cites_gold | +0.042 | +0.000 .. +0.104 | 2/0/46 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Qwen3-8B) | -0.067 | -0.156 .. +0.000 | 0/3/42 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Granite) | +0.000 | -0.067 .. +0.067 | 1/1/43 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | correctness (Qwen3-8B) | +0.000 | -0.067 .. +0.067 | 1/1/43 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | correctness (Granite) | +0.022 | -0.044 .. +0.111 | 2/1/42 | 45 |
