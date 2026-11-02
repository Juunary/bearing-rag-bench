# Judge agreement: Qwen3-8B vs Granite 3.3 8B (same prompts, greedy)

## 1. Per result file and dimension (answers both judges rated)

| result | dimension | n | YES Qwen | YES Granite | agreement | Cohen's kappa |
|---|---|---|---|---|---|---|
| s3_gen_cite_refuse_v1 | faithfulness | 40 | 0.950 | 0.975 | 0.925 | -0.034 |
| s3_gen_cite_refuse_v1 | correctness | 40 | 0.800 | 0.900 | 0.850 | 0.423 |
| s3_gen_cite_refuse_v1 | answer_relevance | 40 | 1.000 | 1.000 | 1.000 | nan |
| v2g_base_bf16 | faithfulness | 76 | 0.908 | 0.961 | 0.921 | 0.365 |
| v2g_base_bf16 | correctness | 77 | 0.805 | 0.909 | 0.870 | 0.481 |
| v2g_base_bf16 | answer_relevance | 77 | 0.948 | 0.961 | 0.935 | 0.252 |
| v2g_base_4bit | faithfulness | 78 | 0.910 | 0.962 | 0.897 | 0.154 |
| v2g_base_4bit | correctness | 78 | 0.769 | 0.897 | 0.821 | 0.372 |
| v2g_base_4bit | answer_relevance | 78 | 0.949 | 0.949 | 0.974 | 0.736 |
| v2g_qlora_s42 | faithfulness | 76 | 0.921 | 0.947 | 0.921 | 0.360 |
| v2g_qlora_s42 | correctness | 77 | 0.792 | 0.922 | 0.844 | 0.385 |
| v2g_qlora_s42 | answer_relevance | 77 | 0.922 | 0.961 | 0.961 | 0.648 |
| v2g_lora_s42 | faithfulness | 76 | 0.961 | 0.974 | 0.961 | 0.380 |
| v2g_lora_s42 | correctness | 77 | 0.818 | 0.935 | 0.831 | 0.243 |
| v2g_lora_s42 | answer_relevance | 77 | 0.961 | 0.974 | 0.987 | 0.794 |
| v2g_ret_b_rrf_en_rerank | faithfulness | 84 | 0.881 | 0.940 | 0.940 | 0.638 |
| v2g_ret_b_rrf_en_rerank | correctness | 84 | 0.857 | 0.917 | 0.893 | 0.471 |
| v2g_ret_b_rrf_en_rerank | answer_relevance | 84 | 0.929 | 0.964 | 0.940 | 0.417 |
| v2g_ret_x2_rerank_en_text | faithfulness | 88 | 0.955 | 0.989 | 0.943 | -0.019 |
| v2g_ret_x2_rerank_en_text | correctness | 88 | 0.886 | 0.966 | 0.898 | 0.269 |
| v2g_ret_x2_rerank_en_text | answer_relevance | 88 | 0.977 | 0.989 | 0.966 | -0.015 |
| v2g_cmp_li | faithfulness | 79 | 0.911 | 0.975 | 0.937 | 0.422 |
| v2g_cmp_li | correctness | 79 | 0.797 | 0.937 | 0.835 | 0.315 |
| v2g_cmp_li | answer_relevance | 79 | 0.937 | 0.975 | 0.937 | 0.259 |
| v2g_cmp_hs | faithfulness | 79 | 0.924 | 0.975 | 0.924 | 0.220 |
| v2g_cmp_hs | correctness | 80 | 0.812 | 0.912 | 0.850 | 0.381 |
| v2g_cmp_hs | answer_relevance | 80 | 0.950 | 0.963 | 0.938 | 0.254 |
| v2g_cmp_ar | faithfulness | 82 | 0.915 | 0.963 | 0.951 | 0.578 |
| v2g_cmp_ar | correctness | 82 | 0.817 | 0.927 | 0.841 | 0.309 |
| v2g_cmp_ar | answer_relevance | 82 | 0.951 | 0.963 | 0.963 | 0.553 |

## 2. Human-graded answers (8, s3_gen_cite_refuse_v1; counts, no rate claimed)

| judge | correctness | faithfulness | answer relevance |
|---|---|---|---|
| qwen | 7/7 | 5/7 | 7/7 |
| granite | 6/7 | 5/7 | 7/7 |

## 3. Paired comparisons under each judge (A - B, document-cluster 95% interval; questions both answers were judged on)

| A | B | dimension | Qwen: mean diff (CI) | Granite: mean diff (CI) |
|---|---|---|---|---|
| v2g_ret_x2_rerank_en_text | v2g_base_bf16 | faithfulness | +0.066 (-0.022 .. +0.151) | +0.040 (+0.000 .. +0.091) |
| v2g_ret_x2_rerank_en_text | v2g_base_bf16 | correctness | +0.105 (+0.013 .. +0.208) | +0.066 (+0.000 .. +0.137) |
| v2g_ret_b_rrf_en_rerank | v2g_base_bf16 | faithfulness | -0.013 (-0.061 .. +0.027) | -0.013 (-0.044 .. +0.000) |
| v2g_ret_b_rrf_en_rerank | v2g_base_bf16 | correctness | +0.052 (+0.000 .. +0.114) | +0.000 (-0.037 .. +0.039) |
| v2g_lora_s42 | v2g_base_bf16 | faithfulness | +0.053 (+0.000 .. +0.117) | +0.000 (-0.039 .. +0.041) |
| v2g_lora_s42 | v2g_base_bf16 | correctness | +0.013 (-0.043 .. +0.076) | +0.013 (+0.000 .. +0.045) |
| v2g_qlora_s42 | v2g_base_4bit | faithfulness | +0.000 (-0.064 .. +0.063) | -0.013 (-0.070 .. +0.045) |
| v2g_qlora_s42 | v2g_base_4bit | correctness | +0.013 (-0.045 .. +0.068) | +0.013 (-0.044 .. +0.071) |
| v2g_ret_x2_rerank_en_text | v2g_cmp_ar | faithfulness | +0.049 (-0.025 .. +0.127) | +0.025 (-0.024 .. +0.078) |
| v2g_ret_x2_rerank_en_text | v2g_cmp_ar | correctness | +0.086 (+0.012 .. +0.162) | +0.049 (+0.011 .. +0.104) |
| v2g_cmp_ar | v2g_cmp_li | faithfulness | +0.000 (-0.060 .. +0.063) | -0.013 (-0.060 .. +0.028) |
| v2g_cmp_ar | v2g_cmp_li | correctness | +0.025 (-0.035 .. +0.089) | -0.013 (-0.056 .. +0.028) |
| v2g_cmp_ar | v2g_cmp_hs | faithfulness | +0.000 (-0.049 .. +0.050) | +0.000 (+0.000 .. +0.000) |
| v2g_cmp_ar | v2g_cmp_hs | correctness | +0.000 (-0.059 .. +0.063) | +0.013 (-0.027 .. +0.057) |
