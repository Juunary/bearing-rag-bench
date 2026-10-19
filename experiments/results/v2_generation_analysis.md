# v2 generation analysis (90 questions)

Selection metric (training answers were chosen by it): sentence_coverage. Independent of the selection: cites_gold, judged metrics, answer language.

## 1. Every condition

| condition | sentence_coverage | cites_gold | citations_valid | refused | gold_in_context | faithfulness | correctness | answer_relevance | answer_language_ok |
|---|---|---|---|---|---|---|---|---|---|
| base_bf16 | 0.821 (n=90) | 0.722 (n=90) | 0.989 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.896 (n=77) | 0.805 (n=77) | 0.948 (n=77) | 0.978 (n=90) |
| base_4bit | 0.595 (n=90) | 0.711 (n=90) | 0.967 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.910 (n=78) | 0.769 (n=78) | 0.949 (n=78) | 1.000 (n=90) |
| qlora_s42 | 0.896 (n=90) | 0.711 (n=90) | 0.989 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.909 (n=77) | 0.792 (n=77) | 0.922 (n=77) | 1.000 (n=90) |
| qlora_s43 | 0.883 (n=90) | 0.689 (n=90) | 0.956 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.923 (n=78) | 0.756 (n=78) | 0.910 (n=78) | 1.000 (n=90) |
| qlora_s44 | 0.886 (n=90) | 0.722 (n=90) | 0.967 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.909 (n=77) | 0.792 (n=77) | 0.935 (n=77) | 1.000 (n=90) |
| lora_s42 | 0.890 (n=90) | 0.733 (n=90) | 0.967 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.948 (n=77) | 0.818 (n=77) | 0.961 (n=77) | 1.000 (n=90) |
| lora_s43 | 0.878 (n=90) | 0.733 (n=90) | 0.978 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.923 (n=78) | 0.795 (n=78) | 0.936 (n=78) | 1.000 (n=90) |
| lora_s44 | 0.898 (n=90) | 0.711 (n=90) | 0.989 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.910 (n=78) | 0.808 (n=78) | 0.936 (n=78) | 1.000 (n=90) |
| xqlora_s42 | 0.905 (n=90) | 0.711 (n=90) | 0.967 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.926 (n=81) | 0.802 (n=81) | 0.901 (n=81) | 1.000 (n=90) |
| xlora_s42 | 0.884 (n=90) | 0.722 (n=90) | 0.978 (n=90) | 0.000 (n=90) | 0.767 (n=90) | 0.924 (n=79) | 0.797 (n=79) | 0.962 (n=79) | 0.989 (n=90) |
| ret_b_rrf_en_rerank | 0.854 (n=90) | 0.744 (n=90) | 0.989 (n=90) | 0.000 (n=90) | 0.833 (n=90) | 0.881 (n=84) | 0.857 (n=84) | 0.929 (n=84) | 0.989 (n=90) |
| ret_x2_rerank_en_text | 0.886 (n=90) | 0.933 (n=90) | 1.000 (n=90) | 0.000 (n=90) | 0.989 (n=90) | 0.955 (n=88) | 0.886 (n=88) | 0.977 (n=88) | 0.989 (n=90) |

## 2. Seed spread (mean ± sd over the seeds present)

| method | seeds | sentence_coverage | cites_gold | citations_valid | refused | gold_in_context | faithfulness | correctness | answer_relevance | answer_language_ok |
|---|---|---|---|---|---|---|---|---|---|---|
| qlora | 3 | 0.888 ± 0.007 | 0.707 ± 0.017 | 0.970 ± 0.017 | 0.000 ± 0.000 | 0.767 ± 0.000 | 0.914 ± 0.008 | 0.780 ± 0.021 | 0.922 ± 0.012 | 1.000 ± 0.000 |
| lora | 3 | 0.889 ± 0.010 | 0.726 ± 0.013 | 0.978 ± 0.011 | 0.000 ± 0.000 | 0.767 ± 0.000 | 0.927 ± 0.019 | 0.807 ± 0.012 | 0.944 ± 0.015 | 1.000 ± 0.000 |

## 3. Paired comparisons (A - B per question; seed-averaged where the condition has seeds)

| A | B | metric | mean diff | 95% CI (question) | 95% CI (cluster) | better/worse/tie |
|---|---|---|---|---|---|---|
| qlora (seed avg) | base_4bit | sentence_coverage | +0.293 | +0.236 .. +0.350 | +0.232 .. +0.347 | 65/3/22 |
| qlora (seed avg) | base_4bit | cites_gold | -0.004 | -0.037 .. +0.026 | -0.029 .. +0.020 | 3/3/84 |
| qlora (seed avg) | base_4bit | faithfulness | -0.000 | -0.064 .. +0.064 | -0.063 .. +0.063 | 5/8/65 |
| qlora (seed avg) | base_4bit | correctness | -0.000 | -0.051 .. +0.051 | -0.056 .. +0.049 | 3/3/72 |
| lora (seed avg) | base_bf16 | sentence_coverage | +0.067 | +0.034 .. +0.104 | +0.036 .. +0.100 | 22/6/62 |
| lora (seed avg) | base_bf16 | cites_gold | +0.004 | -0.011 .. +0.022 | -0.010 .. +0.023 | 1/1/88 |
| lora (seed avg) | base_bf16 | faithfulness | +0.022 | -0.035 .. +0.082 | -0.030 .. +0.076 | 5/5/67 |
| lora (seed avg) | base_bf16 | correctness | +0.013 | -0.048 .. +0.074 | -0.044 .. +0.072 | 6/4/67 |
| qlora (seed avg) | base_bf16 | sentence_coverage | +0.067 | +0.025 .. +0.111 | +0.025 .. +0.105 | 22/11/57 |
| qlora (seed avg) | base_bf16 | cites_gold | -0.015 | -0.037 .. +0.004 | -0.037 .. +0.004 | 1/4/85 |
| qlora (seed avg) | base_bf16 | faithfulness | -0.000 | -0.056 .. +0.056 | -0.057 .. +0.056 | 5/5/67 |
| qlora (seed avg) | base_bf16 | correctness | -0.013 | -0.078 .. +0.052 | -0.080 .. +0.052 | 3/5/69 |
| qlora (seed avg) | lora (seed avg) | sentence_coverage | -0.001 | -0.027 .. +0.025 | -0.029 .. +0.023 | 11/12/67 |
| qlora (seed avg) | lora (seed avg) | cites_gold | -0.019 | -0.041 .. -0.004 | -0.040 .. -0.003 | 0/4/86 |
| qlora (seed avg) | lora (seed avg) | faithfulness | -0.021 | -0.060 .. +0.009 | -0.056 .. +0.008 | 3/6/69 |
| qlora (seed avg) | lora (seed avg) | correctness | -0.030 | -0.081 .. +0.017 | -0.085 .. +0.016 | 3/7/68 |

## 4. Cross-language-only training set vs general set (cross-language questions only; one seed each)

| method | training set | sentence_coverage | cites_gold | faithfulness | correctness | answer_language_ok |
|---|---|---|---|---|---|---|
| qlora | general | 0.872 (n=60) | 0.583 (n=60) | 0.851 (n=47) | 0.681 (n=47) | 1.000 (n=60) |
| qlora | cross-only | 0.890 (n=60) | 0.583 (n=60) | 0.882 (n=51) | 0.706 (n=51) | 1.000 (n=60) |
| lora | general | 0.850 (n=60) | 0.600 (n=60) | 0.915 (n=47) | 0.745 (n=47) | 1.000 (n=60) |
| lora | cross-only | 0.844 (n=60) | 0.583 (n=60) | 0.878 (n=49) | 0.694 (n=49) | 0.983 (n=60) |

## 5. Retrieval effect on the answers (base bf16 model)

| contexts from | gold_in_context | cites_gold | faithfulness | correctness | answer_relevance |
|---|---|---|---|---|---|
| RRF + reranker (original) | 0.767 (n=90) | 0.722 (n=90) | 0.896 (n=77) | 0.805 (n=77) | 0.948 (n=77) |
| English-pivot RRF + reranker | 0.833 (n=90) | 0.744 (n=90) | 0.881 (n=84) | 0.857 (n=84) | 0.929 (n=84) |
| English-pivot RRF + reranker with English reranker input | 0.989 (n=90) | 0.933 (n=90) | 0.955 (n=88) | 0.886 (n=88) | 0.977 (n=88) |

- gold_in_context, ret_b_rrf_en_rerank minus original: +0.067, CI question +0.022..+0.122, CI cluster +0.022..+0.123, better/worse/tie 6/0/84

- cites_gold, ret_b_rrf_en_rerank minus original: +0.022, CI question -0.033..+0.078, CI cluster -0.032..+0.078, better/worse/tie 4/2/84

- correctness, ret_b_rrf_en_rerank minus original: +0.052, CI question +0.000..+0.117, CI cluster +0.000..+0.114, better/worse/tie 5/1/71

- faithfulness, ret_b_rrf_en_rerank minus original: -0.013, CI question -0.065..+0.026, CI cluster -0.061..+0.027, better/worse/tie 1/2/74

- gold_in_context, ret_x2_rerank_en_text minus original: +0.222, CI question +0.133..+0.311, CI cluster +0.120..+0.320, better/worse/tie 21/1/68

- cites_gold, ret_x2_rerank_en_text minus original: +0.211, CI question +0.122..+0.300, CI cluster +0.125..+0.292, better/worse/tie 20/1/69

- correctness, ret_x2_rerank_en_text minus original: +0.105, CI question +0.013..+0.197, CI cluster +0.013..+0.208, better/worse/tie 11/3/62

- faithfulness, ret_x2_rerank_en_text minus original: +0.066, CI question -0.013..+0.145, CI cluster -0.022..+0.151, better/worse/tie 7/2/67

## 6. Answer language (ko: Hangul present; en/de: no Hangul; German vs English is not distinguished)

| condition | ko questions | en questions | de questions |
|---|---|---|---|
| base_bf16 | 1.00 | 0.93 | 1.00 |
| base_4bit | 1.00 | 1.00 | 1.00 |
| qlora_s42 | 1.00 | 1.00 | 1.00 |
| qlora_s43 | 1.00 | 1.00 | 1.00 |
| qlora_s44 | 1.00 | 1.00 | 1.00 |
| lora_s42 | 1.00 | 1.00 | 1.00 |
| lora_s43 | 1.00 | 1.00 | 1.00 |
| lora_s44 | 1.00 | 1.00 | 1.00 |
| xqlora_s42 | 1.00 | 1.00 | 1.00 |
| xlora_s42 | 1.00 | 0.97 | 1.00 |
| ret_b_rrf_en_rerank | 1.00 | 0.97 | 1.00 |
| ret_x2_rerank_en_text | 1.00 | 1.00 | 0.97 |
