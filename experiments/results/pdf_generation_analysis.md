# PDF questions: generation and judging (48 questions)

## 1. Per condition

| condition | gold in context | cites gold | faithfulness (Qwen3-8B) | faithfulness (Granite) | correctness (Qwen3-8B) | correctness (Granite) | answer_relevance (Qwen3-8B) | answer_relevance (Granite) |
|---|---|---|---|---|---|---|---|---|
| RRF + reranker | 0.750 | 0.708 | 0.829 | 0.951 | 0.732 | 0.805 | 0.951 | 0.976 |
| best PDF retrieval | 0.917 | 0.875 | 0.978 | 0.978 | 0.889 | 0.956 | 0.978 | 0.978 |
| best PDF retrieval + table headers | 0.938 | 0.917 | 0.913 | 0.978 | 0.891 | 0.978 | 0.978 | 1.000 |
| best PDF retrieval + table headers, top 10 | 0.979 | 0.938 | 0.936 | 0.957 | 0.957 | 0.957 | 0.957 | 1.000 |

Prompt tokens and generation seconds per answer (median):

| condition | prompt tokens | seconds |
|---|---|---|
| RRF + reranker | 2197 | 3.18 |
| best PDF retrieval | 2210 | 3.23 |
| best PDF retrieval + table headers | 2253 | 2.91 |
| best PDF retrieval + table headers, top 10 | 4395 | 2.85 |

## 2. Correctness by evidence kind

| condition | judge | text | table | caption |
|---|---|---|---|---|
| RRF + reranker | Qwen3-8B | 0.696 (n=23) | 0.769 (n=13) | 0.800 (n=5) |
| RRF + reranker | Granite | 0.783 (n=23) | 0.846 (n=13) | 0.800 (n=5) |
| best PDF retrieval | Qwen3-8B | 0.875 (n=24) | 0.857 (n=14) | 1.000 (n=7) |
| best PDF retrieval | Granite | 1.000 (n=24) | 0.929 (n=14) | 0.857 (n=7) |
| best PDF retrieval + table headers | Qwen3-8B | 0.833 (n=24) | 0.933 (n=15) | 1.000 (n=7) |
| best PDF retrieval + table headers | Granite | 1.000 (n=24) | 0.933 (n=15) | 1.000 (n=7) |
| best PDF retrieval + table headers, top 10 | Qwen3-8B | 0.960 (n=25) | 0.933 (n=15) | 1.000 (n=7) |
| best PDF retrieval + table headers, top 10 | Granite | 1.000 (n=25) | 0.867 (n=15) | 1.000 (n=7) |

## 3. Paired comparisons (A - B, 95% interval by question; no multiplicity correction)

| A | B | metric | mean diff | 95% CI | better/worse/tie | n |
|---|---|---|---|---|---|---|
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | gold_in_context | +0.167 | +0.042 .. +0.292 | 10/2/36 | 48 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | cites_gold | +0.167 | +0.042 .. +0.312 | 10/2/36 | 48 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | sentence_coverage | +0.100 | +0.014 .. +0.186 | 15/5/28 | 48 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | faithfulness (Qwen3-8B) | +0.150 | +0.050 .. +0.275 | 6/0/34 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | faithfulness (Granite) | +0.025 | -0.050 .. +0.100 | 2/1/37 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | correctness (Qwen3-8B) | +0.150 | +0.025 .. +0.275 | 7/1/32 | 40 |
| pdfg_x13_rrf_en_dense_en_rerank_en_text | pdfg_b_rrf_rerank | correctness (Granite) | +0.150 | +0.025 .. +0.300 | 7/1/32 | 40 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | gold_in_context | +0.021 | +0.000 .. +0.062 | 1/0/47 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | cites_gold | +0.042 | +0.000 .. +0.104 | 2/0/46 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | sentence_coverage | +0.029 | +0.000 .. +0.072 | 3/0/45 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Qwen3-8B) | -0.067 | -0.156 .. +0.000 | 0/3/42 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Granite) | +0.000 | -0.067 .. +0.067 | 1/1/43 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | correctness (Qwen3-8B) | +0.000 | -0.067 .. +0.067 | 1/1/43 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text | pdfg_x13_rrf_en_dense_en_rerank_en_text | correctness (Granite) | +0.022 | -0.044 .. +0.111 | 2/1/42 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | gold_in_context | +0.042 | +0.000 .. +0.104 | 2/0/46 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | cites_gold | +0.021 | -0.062 .. +0.125 | 3/2/43 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | sentence_coverage | -0.161 | -0.239 .. -0.083 | 3/19/26 | 48 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Qwen3-8B) | +0.022 | -0.067 .. +0.111 | 3/2/40 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | faithfulness (Granite) | -0.022 | -0.067 .. +0.000 | 0/1/44 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | correctness (Qwen3-8B) | +0.067 | -0.044 .. +0.178 | 5/2/38 | 45 |
| pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10 | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | correctness (Granite) | -0.022 | -0.111 .. +0.044 | 1/2/42 | 45 |

## 4. Serving prompt cite_refuse_v1, top 5 vs top 10 (automatic metrics, not judged)

| context | refused | over_refusal | gold_in_context | cites_gold | sentence_coverage |
|---|---|---|---|---|---|
| top 5 | 0.062 | 0.042 | 0.938 | 0.875 | 0.816 |
| top 10 | 0.021 | 0.021 | 0.979 | 0.896 | 0.686 |

| metric | top 10 - top 5 | 95% CI | top 10 higher/lower/tie |
|---|---|---|---|
| refused | -0.042 | -0.125 .. +0.042 | 1/3/44 |
| over_refusal | -0.021 | -0.083 .. +0.042 | 1/2/45 |
| gold_in_context | +0.042 | +0.000 .. +0.104 | 2/0/46 |
| cites_gold | +0.021 | -0.083 .. +0.125 | 4/3/41 |
| sentence_coverage | -0.131 | -0.233 .. -0.023 | 4/18/26 |
