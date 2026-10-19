# v2 pooled re-scoring

pool: 1086 judged chunks, 0 without a label, depth 3, 25 configs

## Judge controls

- known gold chunks labelled >= 1: 15/16
- random chunks of other documents labelled 0: 16/16

pooled relevant chunks added to gold': 97 in 45 questions

## nDCG@10 and Recall@5, original gold vs pooled gold'

| config | nDCG orig | nDCG pooled | R@5 orig | R@5 pooled |
|---|---|---|---|---|
| b_bm25_en | 0.749 | 0.764 | 0.745 | 0.721 |
| b_bm25_kiwi | 0.336 | 0.351 | 0.330 | 0.324 |
| b_bm25_subword | 0.325 | 0.356 | 0.326 | 0.316 |
| b_bm25_whitespace | 0.328 | 0.339 | 0.313 | 0.305 |
| b_dense | 0.487 | 0.528 | 0.514 | 0.499 |
| b_rrf | 0.360 | 0.396 | 0.341 | 0.347 |
| b_rrf_en | 0.637 | 0.663 | 0.695 | 0.653 |
| b_rrf_en_rerank | 0.656 | 0.678 | 0.679 | 0.636 |
| b_rrf_rerank | 0.586 | 0.624 | 0.608 | 0.588 |
| x11_bm25_en_skip | 0.756 | 0.766 | 0.745 | 0.718 |
| x1_rrf3 | 0.455 | 0.490 | 0.391 | 0.397 |
| x1_rrf3_rerank | 0.639 | 0.664 | 0.658 | 0.621 |
| x2_orig_rerank_n100 | 0.636 | 0.661 | 0.656 | 0.618 |
| x2_rerank_en_text | 0.895 | 0.903 | 0.892 | 0.852 |
| x2_rerank_n100 | 0.652 | 0.675 | 0.671 | 0.631 |
| x2_rerank_n50 | 0.652 | 0.673 | 0.667 | 0.627 |
| x3_bm25_en_gl | 0.770 | 0.799 | 0.782 | 0.757 |
| x3_rrf_en_rerank_gl | 0.654 | 0.677 | 0.682 | 0.642 |
| x4_bm25_en_stem | 0.756 | 0.771 | 0.781 | 0.743 |
| x4_bm25_en_stem_stop | 0.744 | 0.763 | 0.760 | 0.723 |
| x5_bm25_en_hyde | 0.769 | 0.789 | 0.817 | 0.764 |
| x5_bm25_en_multi | 0.688 | 0.706 | 0.720 | 0.680 |
| x6_bm25_kiwi_ctx | 0.337 | 0.354 | 0.330 | 0.321 |
| x6_dense_ctx | 0.435 | 0.474 | 0.460 | 0.463 |
| x6_rrf_rerank_ctx | 0.565 | 0.604 | 0.590 | 0.570 |

Kendall tau between the system order by original and by pooled nDCG@10: 0.973 (25 systems)

## Paired comparisons on pooled nDCG@10 (A - B)

| A | B | mean diff | 95% CI (question) | 95% CI (cluster) | better/worse/tie |
|---|---|---|---|---|---|
| b_rrf_en_rerank | b_rrf_rerank | +0.053 | +0.025 .. +0.085 | +0.026 .. +0.083 | 24/8/58 |
| b_bm25_en | b_bm25_kiwi | +0.412 | +0.317 .. +0.506 | +0.316 .. +0.509 | 69/11/10 |
| b_bm25_en | b_dense | +0.235 | +0.145 .. +0.326 | +0.137 .. +0.328 | 62/18/10 |
| x1_rrf3_rerank | b_rrf_en_rerank | -0.014 | -0.033 .. +0.001 | -0.032 .. +0.001 | 3/11/76 |
| x5_bm25_en_multi | b_bm25_en | -0.058 | -0.111 .. -0.010 | -0.118 .. -0.000 | 23/30/37 |
| x4_bm25_en_stem | b_bm25_en | +0.007 | -0.026 .. +0.041 | -0.029 .. +0.047 | 24/26/40 |
