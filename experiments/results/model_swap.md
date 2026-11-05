# Model swap: 2026 embedding and reranker models in the best pipelines

One model replaced at a time; prompts, pooling and dtype follow the model cards (scripts/make_model_configs.py).

## v2 questions (90, Wikipedia corpus)

| setting | embedding / reranker | R@5 | MRR@10 | nDCG@10 | mono | cross | nDCG diff vs baseline | question CI | cluster CI | better/worse/tie | index s | query p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | bge-m3 / bge-reranker-v2-m3 | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 | - | - | - | - | 0 | 184 |
| emb_qwen3_0.6b | Qwen3-Embedding-0.6B / bge-reranker-v2-m3 | 0.873 | 0.916 | 0.878 | 0.902 | 0.866 | -0.017 | -0.043 .. +0.004 | -0.043 .. +0.004 | 3/5/82 | 4 | 196 |
| emb_gemma2 | embeddinggemma-2 / bge-reranker-v2-m3 | 0.897 | 0.934 | 0.890 | 0.906 | 0.882 | -0.005 | -0.016 .. +0.001 | -0.013 .. +0.002 | 4/3/83 | 2 | 201 |
| rr_qwen3_0.6b | bge-m3 / Qwen3-Reranker-0.6B | 0.884 | 0.873 | 0.854 | 0.865 | 0.849 | -0.040 | -0.074 .. -0.008 | -0.072 .. -0.010 | 13/26/51 | 0 | 660 |
| rr_qwen3_4b | bge-m3 / Qwen3-Reranker-4B | 0.918 | 0.932 | 0.901 | 0.902 | 0.900 | +0.006 | -0.022 .. +0.034 | -0.030 .. +0.041 | 19/17/54 | 0 | 3688 |

## PDF questions (48, Wikipedia + PDF, table headers)

| setting | embedding / reranker | R@5 | MRR@10 | nDCG@10 | mono | cross | nDCG diff vs baseline | question CI | cluster CI | better/worse/tie | index s | query p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | bge-m3 / bge-reranker-v2-m3 | 0.882 | 0.850 | 0.831 | 0.811 | 0.842 | - | - | - | - | 0 | 196 |
| emb_qwen3_0.6b | Qwen3-Embedding-0.6B / bge-reranker-v2-m3 | 0.872 | 0.847 | 0.816 | 0.788 | 0.830 | -0.015 | -0.039 .. +0.000 | -0.046 .. +0.000 | 0/2/46 | 11 | 213 |
| emb_gemma2 | embeddinggemma-2 / bge-reranker-v2-m3 | 0.903 | 0.851 | 0.832 | 0.813 | 0.842 | +0.001 | +0.000 .. +0.002 | +0.000 .. +0.002 | 2/0/46 | 6 | 222 |
| rr_qwen3_0.6b | bge-m3 / Qwen3-Reranker-0.6B | 0.873 | 0.883 | 0.850 | 0.832 | 0.858 | +0.018 | -0.038 .. +0.074 | -0.036 .. +0.070 | 13/8/27 | 0 | 570 |
| rr_qwen3_4b | bge-m3 / Qwen3-Reranker-4B | 0.931 | 0.903 | 0.896 | 0.848 | 0.920 | +0.065 | -0.001 .. +0.131 | -0.004 .. +0.130 | 19/5/24 | 0 | 2969 |

