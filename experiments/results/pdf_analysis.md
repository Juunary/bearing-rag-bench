# Retrieval on Wikipedia + PDF (903 chunks)

## 1. PDF questions (48; text 26, table 15, caption 7; table header in another chunk 5)

| setting | R@5 | MRR@10 | nDCG@10 | mono | cross | text | table | caption | table, header split |
|---|---|---|---|---|---|---|---|---|---|
| b_bm25_kiwi | 0.300 | 0.352 | 0.308 | 0.693 | 0.116 | 0.299 | 0.377 | 0.197 | 0.256 |
| b_dense | 0.592 | 0.532 | 0.526 | 0.555 | 0.511 | 0.655 | 0.396 | 0.325 | 0.155 |
| b_rrf_rerank | 0.649 | 0.654 | 0.632 | 0.735 | 0.580 | 0.721 | 0.552 | 0.473 | 0.420 |
| b_bm25_en | 0.667 | 0.712 | 0.668 | 0.681 | 0.661 | 0.710 | 0.649 | 0.550 | 0.433 |
| b_rrf_en_rerank | 0.705 | 0.683 | 0.670 | 0.730 | 0.640 | 0.748 | 0.595 | 0.540 | 0.349 |
| x2_rerank_en_text | 0.841 | 0.781 | 0.755 | 0.763 | 0.750 | 0.835 | 0.657 | 0.664 | 0.316 |
| x12_dense_rerank | 0.664 | 0.666 | 0.632 | 0.730 | 0.582 | 0.731 | 0.521 | 0.500 | 0.328 |
| x13_dense_en | 0.685 | 0.601 | 0.596 | 0.585 | 0.602 | 0.687 | 0.521 | 0.418 | 0.221 |
| x13_dense_en_rerank_en_text | 0.795 | 0.733 | 0.708 | 0.742 | 0.692 | 0.799 | 0.578 | 0.650 | 0.325 |
| x13_rrf_en_dense_en_rerank_en_text | 0.856 | 0.785 | 0.774 | 0.763 | 0.780 | 0.835 | 0.680 | 0.748 | 0.360 |

## 2. nDCG@10 per language pair (8 questions each)

| setting | de->de | de->en | en->de | en->en | ko->de | ko->en |
|---|---|---|---|---|---|---|
| b_bm25_kiwi | 0.64 | 0.17 | 0.00 | 0.74 | 0.08 | 0.21 |
| b_dense | 0.45 | 0.46 | 0.20 | 0.66 | 0.58 | 0.80 |
| b_rrf_rerank | 0.65 | 0.62 | 0.28 | 0.82 | 0.49 | 0.93 |
| b_bm25_en | 0.61 | 0.70 | 0.44 | 0.76 | 0.67 | 0.84 |
| b_rrf_en_rerank | 0.64 | 0.59 | 0.47 | 0.82 | 0.57 | 0.93 |
| x2_rerank_en_text | 0.62 | 0.72 | 0.66 | 0.90 | 0.81 | 0.81 |
| x12_dense_rerank | 0.64 | 0.57 | 0.34 | 0.82 | 0.49 | 0.93 |
| x13_dense_en | 0.50 | 0.62 | 0.37 | 0.67 | 0.55 | 0.86 |
| x13_dense_en_rerank_en_text | 0.58 | 0.72 | 0.59 | 0.90 | 0.64 | 0.82 |
| x13_rrf_en_dense_en_rerank_en_text | 0.62 | 0.75 | 0.75 | 0.90 | 0.81 | 0.81 |

## 3. Paired comparisons on the PDF questions (nDCG@10, A - B; cluster interval over only 6 documents)

| A | B | mean diff | 95% CI (question) | 95% CI (document cluster) | better/worse/tie | sign-test p |
|---|---|---|---|---|---|---|
| x2_rerank_en_text | b_rrf_rerank | +0.123 | +0.034 .. +0.218 | +0.012 .. +0.232 | 17/10/21 | 0.248 |
| x13_dense_en_rerank_en_text | x2_rerank_en_text | -0.046 | -0.100 .. +0.001 | -0.112 .. +0.001 | 5/6/37 | 1.000 |
| x13_dense_en | b_dense | +0.070 | +0.012 .. +0.131 | +0.006 .. +0.105 | 16/7/25 | 0.093 |
| b_bm25_en | b_bm25_kiwi | +0.359 | +0.240 .. +0.482 | +0.284 .. +0.491 | 31/6/11 | 0.000 |
| x12_dense_rerank | b_rrf_rerank | -0.000 | -0.023 .. +0.021 | -0.021 .. +0.027 | 3/4/41 | 1.000 |

## 4. v2 questions (90) without and with the PDF chunks

PDF chunks are not in the v2 gold, so a relevant PDF chunk in the ranking counts as a miss.

| setting | nDCG@10 wiki | nDCG@10 wiki + pdf | diff | 95% CI (document cluster) | questions with a PDF chunk in top 5 |
|---|---|---|---|---|---|
| b_bm25_kiwi | 0.336 | 0.320 | -0.016 | -0.038 .. +0.002 | 33/90 |
| b_dense | 0.487 | 0.460 | -0.026 | -0.047 .. -0.011 | 37/90 |
| b_rrf_rerank | 0.586 | 0.570 | -0.016 | -0.052 .. +0.014 | 29/90 |
| b_bm25_en | 0.749 | 0.729 | -0.020 | -0.046 .. +0.003 | 37/90 |
| b_rrf_en_rerank | 0.656 | 0.642 | -0.013 | -0.036 .. +0.002 | 31/90 |
| x2_rerank_en_text | 0.895 | 0.865 | -0.029 | -0.065 .. -0.003 | 28/90 |
| x12_dense_rerank | 0.642 | 0.603 | -0.040 | -0.079 .. -0.011 | 29/90 |
| x13_dense_en | 0.738 | 0.703 | -0.035 | -0.069 .. -0.010 | 36/90 |
| x13_dense_en_rerank_en_text | 0.891 | 0.852 | -0.039 | -0.077 .. -0.011 | 29/90 |
| x13_rrf_en_dense_en_rerank_en_text | 0.893 | 0.869 | -0.024 | -0.057 .. -0.001 | 28/90 |

## 5. Table caption and header rows repeated in chunks (chunking.table_header; PDF questions)

| setting | nDCG@10 | with headers | diff (95% CI, question) | table (15) | with headers | header split (5) | with headers |
|---|---|---|---|---|---|---|---|
| b_bm25_kiwi | 0.308 | 0.328 | +0.019 (-0.004 .. +0.053) | 0.377 | 0.440 | 0.256 | 0.415 |
| b_dense | 0.526 | 0.585 | +0.059 (+0.022 .. +0.105) | 0.396 | 0.562 | 0.155 | 0.557 |
| b_rrf_rerank | 0.632 | 0.661 | +0.029 (+0.008 .. +0.055) | 0.552 | 0.642 | 0.420 | 0.551 |
| b_bm25_en | 0.668 | 0.693 | +0.025 (-0.002 .. +0.061) | 0.649 | 0.745 | 0.433 | 0.659 |
| b_rrf_en_rerank | 0.670 | 0.709 | +0.039 (+0.011 .. +0.079) | 0.595 | 0.721 | 0.349 | 0.607 |
| x2_rerank_en_text | 0.755 | 0.819 | +0.065 (+0.022 .. +0.118) | 0.657 | 0.864 | 0.316 | 0.706 |
| x12_dense_rerank | 0.632 | 0.684 | +0.052 (+0.017 .. +0.097) | 0.521 | 0.688 | 0.328 | 0.588 |
| x13_dense_en | 0.596 | 0.640 | +0.044 (+0.012 .. +0.087) | 0.521 | 0.661 | 0.221 | 0.565 |
| x13_dense_en_rerank_en_text | 0.708 | 0.752 | +0.044 (+0.010 .. +0.088) | 0.578 | 0.714 | 0.325 | 0.598 |
| x13_rrf_en_dense_en_rerank_en_text | 0.774 | 0.831 | +0.057 (+0.020 .. +0.103) | 0.680 | 0.864 | 0.360 | 0.706 |
