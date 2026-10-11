### 1. automatic metrics (n=45)

| condition | has_citation | citations_valid | cites_gold | sentence_coverage | refused | answer tokens | generation s (p50) |
|---|---|---|---|---|---|---|---|
| base bf16 | 0.978 | 0.978 | 0.756 | 0.857 | 0.000 | 123 | 3.5 |
| base 4-bit | 1.000 | 0.978 | 0.711 | 0.636 | 0.000 | 115 | 3.9 |
| QLoRA r16 | 0.978 | 0.956 | 0.756 | 0.946 | 0.000 | 122 | 10.0 |
| LoRA r16 | 0.978 | 0.978 | 0.756 | 0.886 | 0.000 | 130 | 6.9 |

### 2. sentence-level citation rate vs the matching untuned base (paired bootstrap)

| tuned/changed | vs | mean diff | 95% interval | better / worse questions |
|---|---|---|---|---|
| LoRA r16 | base bf16 | +0.028 | -0.014 .. +0.076 | 6 / 3 |
| QLoRA r16 | base 4-bit | +0.310 | +0.220 .. +0.396 | 32 / 1 |
| base 4-bit | base bf16 | -0.221 | -0.308 .. -0.133 | 2 / 24 |

### 3. judged quality (Qwen3-8B judge; share of YES among applicable answers)

| condition | faithfulness | answer_relevance | correctness | outcome classes |
|---|---|---|---|---|
| base bf16 | 0.925 (n=40) | 0.975 (n=40) | 0.850 (n=40) | {'ok': 29, 'correct_refusal': 4, 'generation_failure': 6, 'retrieval_failure': 5, 'over_refusal': 1} |

### 4. training

| run | trainable params | base weights GiB | peak GPU GiB | train time | tokens/s | train examples | val loss before -> final | adapter MB |
|---|---|---|---|---|---|---|---|---|
| s4_qlora_r16 | 33.0M | 2.5 | 4.3 | 9.9 min | 1333 | 125 | 0.220 -> 0.216 | 126 |
| s4_lora_r16 | 33.0M | 7.5 | 9.4 | 9.7 min | 1355 | 125 | 0.109 -> 0.121 | 126 |

s4_qlora_r16 validation loss by epoch: before=0.220, epoch_1=0.197, epoch_2=0.212, epoch_3=0.216

s4_lora_r16 validation loss by epoch: before=0.109, epoch_1=0.120, epoch_2=0.121, epoch_3=0.121
