# bearing-rag-bench

[한국어](README.md) | English

An experiment repository that implements and measures RAG retrieval, generation, evaluation, operations and fine-tuning on Korean, English and German technical documents about bearings and automotive parts.
No RAG framework (LangChain, LlamaIndex) is used. Chunking, BM25, embeddings, HNSW, RRF, reranking, metrics, caching, validation and the LoRA training loop are implemented directly.

## Components

| Area | Implementation |
|---|---|
| Chunking | 384 bge-m3 tokens, 48 overlap, paragraph and sentence boundaries |
| Retrieval | BM25 (bm25s; whitespace, kiwipiepy morphemes, subword tokenizers), dense (BAAI/bge-m3 + hnswlib), RRF (k=60), reranker (BAAI/bge-reranker-v2-m3) |
| Metrics | Recall@5, MRR@10, nDCG@10 (graded), aggregated by language pair; a repeated chunk id scores only at its first occurrence (`src/ragbench/metrics.py`); document-cluster bootstrap and sign test (`src/ragbench/stats.py`) |
| Generation | Qwen3-4B-Instruct-2507 run locally, greedy decoding, top-5 chunks, two prompts (cite_v1, cite_refuse_v1) |
| Evaluation | LLM judge (Qwen3-8B) for faithfulness, answer relevance, context relevance and correctness, compared with 8 human-graded answers |
| Operations | Request logging (JSONL), LLM cache (SQLite), input/output validation, baseline-comparison regression check |
| Fine-tuning | LoRA and QLoRA (rank 16, hand-written training loop) |
| English pivot | Chunks and queries translated to English with Qwen3-4B-Instruct-2507, then English BM25 (chunk-first and document-first translation), glossary hints, stemming, query expansion (multi, HyDE), English reranker input |
| Service | Local FastAPI chat server (127.0.0.1) on top of the pipeline with validation, cache and logging |

## Requirements

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- NVIDIA GPU. Run on two RTX 3080 Ti 12 GB cards. Retrieval about 3 GiB, generation 7.5 GiB, QLoRA training 4.3 GiB, LoRA training 9.4 GiB; the judge model is split across two cards.
- torch is pinned to the CUDA 12.6 index (`pyproject.toml`).

## Usage

```bash
uv sync
uv run python scripts/fetch_data.py                 # download 45 Wikipedia articles (data/raw, not committed)
uv run python -m ragbench.ingest                    # clean -> data/processed/docs.jsonl
uv run python -m ragbench.chunking                  # 346 chunks
uv run python scripts/validate_eval.py              # validate the eval set
```

One experiment is one config file and one command.

```bash
uv run python experiments/run_retrieval.py configs/s1_hybrid_rrf_rerank.json
```

```bash
# Stage 1: retrieval
for c in configs/s1_*.json; do uv run python experiments/run_retrieval.py $c; done
uv run python experiments/run_hnsw_sweep.py
uv run python experiments/compare.py experiments/results/s1_*.json --by-group
uv run python experiments/analyze_s1.py

# Stages 3 and 3.5: generation, evaluation, operations
uv run python experiments/run_generation.py configs/s3_gen_cite_refuse_v1.json
uv run python experiments/run_judge.py configs/s3_judge.json s3_gen_cite_v1 s3_gen_cite_refuse_v1
uv run python experiments/analyze_judge.py
uv run python experiments/run_pipeline.py configs/s35_pipeline.json
uv run python experiments/regression.py configs/s3_gen_cite_refuse_v1.json --run

# Stage 4: fine-tuning
uv run python experiments/build_sft_data.py          # build the training set (can be skipped: data/sft is committed)
uv run python experiments/train_lora.py configs/s4_qlora_r16.json
uv run python experiments/train_lora.py configs/s4_lora_r16.json
for c in s4_gen_base4bit s4_gen_qlora_r16 s4_gen_lora_r16; do uv run python experiments/run_generation.py configs/$c.json; done
uv run python experiments/run_judge.py configs/s3_judge.json s4_gen_base4bit s4_gen_qlora_r16 s4_gen_lora_r16
uv run python experiments/analyze_s4.py

# Stage 5: English pivot (translate chunks first)
uv run python experiments/build_english_chunks.py     # translate the Korean and German chunks to English
uv run python experiments/run_retrieval.py configs/s5_bm25_en_whitespace.json

# Improvement experiments on eval set v2 (90 questions)
uv run python scripts/make_v2_configs.py && uv run python experiments/run_suite.py
uv run python experiments/analyze_v2.py
uv run python scripts/make_pool.py --depth 3 --shards 8   # pooling candidates (then experiments/eval_pooled.py after labelling)
uv run python scripts/make_v2_ft_configs.py --retrieval v2_b_rrf_en_rerank
uv run python experiments/analyze_v2_generation.py

# Local chat server (http://127.0.0.1:8000)
uv run python experiments/serve_chat.py configs/s35_pipeline.json

# Service performance (stage latency, concurrent requests)
uv run python experiments/bench_service.py configs/s6_pipeline_en.json --n 30
uv run python experiments/bench_chat_concurrency.py configs/s6_pipeline_en.json

uv run pytest -q
```

Each result JSON records the full config, package versions, git commit, model revisions, the seed (42) and per-question outputs.

## Data

- Wikipedia: 13 Korean, 16 English and 16 German articles (CC BY-SA 4.0). Sources are listed in `data/sources.csv`; the cleaned text is `data/processed/docs.jsonl`.
- 346 chunks (179 English, 124 German, 43 Korean).
- Eval set `eval/queries.jsonl`: 45 questions (15 each in ko, en, de). Gold evidence is written as document ID, evidence sentence and grade (core 2 / supporting 1) and mapped to chunks at evaluation time. The format is described in `eval/README.md` (in Korean).
- Eval set v2 `eval/queries_v2.jsonl`: 90 questions (10 per question-language x primary-language pair). Change history in `eval/README.md`, edit log in `eval/v2_review_log.json`.

## Results

### Retrieval (45 questions)

| Method | Recall@5 | MRR@10 | nDCG@10 | nDCG same-language | nDCG cross-language | Latency p50 per query |
|---|---|---|---|---|---|---|
| BM25 whitespace | 0.404 | 0.430 | 0.421 | 0.786 | 0.101 | 0.09 ms |
| BM25 morphemes | 0.411 | 0.425 | 0.410 | 0.781 | 0.086 | 0.15 ms |
| BM25 subword | 0.400 | 0.428 | 0.422 | 0.798 | 0.093 | 0.20 ms |
| dense (HNSW) | 0.511 | 0.505 | 0.510 | 0.697 | 0.345 | 7.9 ms |
| Hybrid RRF | 0.411 | 0.428 | 0.426 | 0.808 | 0.092 | 8.6 ms |
| RRF + reranker | 0.615 | 0.702 | 0.631 | 0.835 | 0.453 | 168.4 ms |

Per-language-pair tables, bootstrap confidence intervals and paired comparisons are in `experiments/results/s1_comparison.md` and `s1_analysis.md`.

HNSW (346 vectors, recall@10 against exact search, exact search p50 0.040 ms)

| ef_search | recall@10 | p50 latency |
|---|---|---|
| 16 | 0.951 | 0.020 ms |
| 64 | 1.000 | 0.039 ms |
| 128 | 1.000 | 0.056 ms |
| 256 | 1.000 | 0.075 ms |

### Generation and evaluation (45 questions)

| | cite_v1 | cite_refuse_v1 |
|---|---|---|
| Answer contains a citation | 97.8% | 91.1% |
| Gold chunk cited | 75.6% | 75.6% |
| Refusal | 0% | 8.9% |
| Faithfulness (judge) | 92.5% | 95.0% |
| Answer relevance (judge) | 97.5% | 100% |
| Context relevance (judge) | 88.9% | 88.9% |
| Correctness (judge) | 85.0% | 80.0% |
| Generation time p50 | 3.6 s | 2.9 s |

- Agreement between the judge and the 8 human-graded answers: correctness 7/7, answer relevance 7/7, faithfulness 5/7.
- Outcome classes (identical for both prompts): ok 29, generation failure 6, retrieval failure 5, correct refusal 4, over-refusal 1.

### Operations

| Feature | Result |
|---|---|
| LLM cache | 45 of 45 hits on the second pass; per-question latency p50 3212 ms to 176 ms |
| Input/output validation | 5 of 45 answers blocked |
| Regression check | 6 baselines, all PASS (identical = PASS, a metric drop above 0.02 = FAIL) |

### LoRA / QLoRA fine-tuning

The task is citation completeness: every sentence of the answer carries a valid citation. The training set has 125 examples (13 for validation), taken from the base model's own sampled answers that passed a filter (`data/sft/stats.json`).

| Condition | Sentence-level citation rate | Citation IDs valid | Faithfulness | Answer relevance | Correctness |
|---|---|---|---|---|---|
| Base bf16 | 0.857 | 0.978 | 0.925 | 0.975 | 0.850 |
| Base 4-bit | 0.636 | 0.978 | 0.976 | 0.976 | 0.780 |
| QLoRA (4-bit base) | 0.946 | 0.956 | 0.976 | 0.927 | 0.780 |
| LoRA (bf16 base) | 0.886 | 0.978 | 0.902 | 0.976 | 0.829 |

| Training cost | QLoRA | LoRA |
|---|---|---|
| Base weights | 2.5 GiB | 7.5 GiB |
| Peak GPU memory | 4.3 GiB | 9.4 GiB |
| Training time | 9.9 min | 9.7 min |
| Trainable parameters / adapter | 33.0M / 126 MB | 33.0M / 126 MB |

### Retrieval (eval set v2, 90 questions)

| Method | Recall@5 | MRR@10 | nDCG@10 | mono nDCG | cross nDCG | translate/expand time per query |
|---|---|---|---|---|---|---|
| BM25 kiwi | 0.330 | 0.405 | 0.336 | 0.788 | 0.110 | - |
| dense (HNSW) | 0.514 | 0.506 | 0.487 | 0.760 | 0.350 | - |
| RRF | 0.341 | 0.433 | 0.360 | 0.825 | 0.128 | - |
| RRF + reranker | 0.608 | 0.650 | 0.586 | 0.864 | 0.448 | - |
| English BM25 (chunk-first translation) | 0.745 | 0.768 | 0.749 | 0.702 | 0.772 | 0.60 s |
| English BM25 + glossary | 0.782 | 0.784 | 0.770 | 0.778 | 0.767 | 0.57 s |
| English BM25 + stemming | 0.781 | 0.762 | 0.756 | 0.719 | 0.774 | 0.60 s |
| English BM25 + query expansion multi | 0.720 | 0.708 | 0.688 | 0.626 | 0.719 | 1.90 s |
| English BM25 + query expansion HyDE | 0.817 | 0.767 | 0.769 | 0.771 | 0.768 | 2.67 s |
| English RRF | 0.695 | 0.647 | 0.637 | 0.784 | 0.564 | 0.60 s |
| English RRF + reranker | 0.679 | 0.700 | 0.656 | 0.876 | 0.545 | 0.60 s |
| English RRF + reranker (English chunks and English query as reranker input) | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 | 0.60 s |
| 3-way RRF (English BM25 + kiwi BM25 + dense) | 0.391 | 0.465 | 0.455 | 0.812 | 0.276 | 0.60 s |
| 3-way RRF + reranker | 0.658 | 0.684 | 0.639 | 0.869 | 0.524 | 0.60 s |

Translate/expand time is the median of the original generation seconds stored in the cache. With translation skipped for queries that look English, nDCG is 0.756.

Comparisons fixed before the runs (nDCG@10 difference A - B, 95 % interval resampling primary-evidence documents, 27 comparisons, no multiplicity correction) are in `experiments/results/v2_analysis.md`.

| A | B | difference | 95 % interval (document cluster) |
|---|---|---|---|
| English BM25 | BM25 kiwi | +0.413 | +0.307 .. +0.515 |
| English RRF + reranker | RRF + reranker | +0.069 | +0.035 .. +0.110 |
| English reranker input | English RRF + reranker | +0.239 | +0.153 .. +0.322 |
| 3-way RRF | English RRF | -0.182 | -0.255 .. -0.117 |
| glossary | English BM25 | +0.022 | -0.021 .. +0.061 |
| stemming | English BM25 | +0.007 | -0.032 .. +0.048 |
| query expansion HyDE | English BM25 | +0.020 | -0.037 .. +0.075 |
| query expansion multi | English BM25 | -0.060 | -0.125 .. +0.002 |
| dense + contextual prefix (title > section) | dense | -0.052 | -0.083 .. -0.023 |

Chunk size (256 / 384 / 512, overlap 48) and contextual prefix on the original-text pipelines, nDCG@10:

| Method | 256 | 384 | 512 | 384 + prefix |
|---|---|---|---|---|
| BM25 kiwi | 0.324 | 0.336 | 0.335 | 0.337 |
| dense | 0.495 | 0.487 | 0.473 | 0.435 |
| RRF + reranker | 0.591 | 0.586 | 0.568 | 0.565 |

Reranker candidates (30 / 50 / 100): English RRF + reranker nDCG@10 0.656 / 0.652 / 0.652. The gold chunk is inside the 30 candidates for 90/90 questions with English RRF and 73/90 with original RRF; after reranking it is in the top 5 for 75/90 and 69/90.

Pooled re-scoring (`experiments/results/v2_pooled.md`): the top 3 of 25 configurations, minus gold chunks, gave 1,054 chunks that were labelled; 97 relevant chunks were added to 45 questions. Rank correlation of the systems under original vs pooled gold: Kendall tau 0.973. Judge controls: 15/16 known gold chunks labelled >= 1, 16/16 unrelated chunks labelled 0.

### Generation and evaluation (eval set v2, 90 questions)

Prompt cite_v1, top-5 chunks (RRF + reranker), greedy. Training data excluded every v2 gold chunk as a source (86 train, 12 validation); mean ± standard deviation over 3 seeds. Training answers were selected by `sentence_coverage = 1`.

| Condition | sentence-level citation rate (selection metric) | cites gold chunk | faithfulness | correctness | answer relevance |
|---|---|---|---|---|---|
| base bf16 | 0.821 | 0.722 | 0.896 | 0.805 | 0.948 |
| base 4-bit | 0.595 | 0.711 | 0.910 | 0.769 | 0.949 |
| QLoRA (4-bit base, 3 seeds) | 0.888 ± 0.007 | 0.707 ± 0.017 | 0.914 ± 0.008 | 0.780 ± 0.021 | 0.922 ± 0.012 |
| LoRA (bf16 base, 3 seeds) | 0.889 ± 0.010 | 0.726 ± 0.013 | 0.927 ± 0.019 | 0.807 ± 0.012 | 0.944 ± 0.015 |
| QLoRA, cross-language-only training (66 examples, 1 seed) | 0.905 | 0.711 | 0.926 | 0.802 | 0.901 |
| LoRA, cross-language-only training (66 examples, 1 seed) | 0.884 | 0.722 | 0.924 | 0.797 | 0.962 |

Per-question differences between a tuned model and its own untuned base (seed average, 95 % interval by document cluster): QLoRA - base 4-bit: sentence-level citation rate +0.293 (+0.232 .. +0.347), cites gold chunk -0.004 (-0.029 .. +0.020), correctness -0.000 (-0.056 .. +0.049). LoRA - base bf16: sentence-level citation rate +0.067 (+0.036 .. +0.100), cites gold chunk +0.004 (-0.010 .. +0.023), correctness +0.013 (-0.044 .. +0.072). The full tables are in `experiments/results/v2_generation_analysis.md`.

Base bf16 model with contexts from different retrieval results:

| Contexts from | gold chunk in context | cites gold chunk | faithfulness | correctness |
|---|---|---|---|---|
| RRF + reranker | 0.767 | 0.722 | 0.896 | 0.805 |
| English RRF + reranker | 0.833 | 0.744 | 0.881 | 0.857 |
| English RRF + reranker (English reranker input) | 0.989 | 0.933 | 0.955 | 0.886 |

Difference to RRF + reranker (95 % interval by document cluster), English reranker input: gold chunk in context +0.222 (+0.120 .. +0.320), cites gold chunk +0.211 (+0.125 .. +0.292), correctness +0.105 (+0.013 .. +0.208), faithfulness +0.066 (-0.022 .. +0.151).

### Service performance (real models)

30 questions taken evenly from eval set v2 were asked one after another. The cold pass starts with empty translation and LLM caches; the warm pass asks the same questions again and is answered from the caches. Values are in ms as `p50 / p95`. The service handles one request at a time. Configs: `configs/s35_pipeline.json` (original retrieval) and `configs/s6_pipeline_en.json` (English pivot + English reranker input).

| Item | original retrieval (s35) | English pivot (s6) |
|---|---|---|
| Retrieval (query translation + search + reranking) | 184 / 192 | 740 / 1004 |
| Query translation | - | 570 / 828 |
| Reranking | 173 / 182 | 161 / 168 |
| Generation | 2521 / 6362 | 2929 / 4888 |
| Total | 2703 / 6552 | 3590 / 5866 |
| Throughput (questions/min, cold pass) | 19.3 | 14.9 |
| Generation speed (tokens/s, p50) | 29.6 | 30.1 |
| Total, cache answer (same question again) | 170 / 174 | 171 / 173 |
| Blocked by output validation | 4/30 | 1/30 |
| GPU memory (nvidia-smi, cuda:0 / cuda:1) | 2881 / 8798 MiB | 10647 / 8942 MiB |
| Retrieval model load + indexing / generator load | 18.3 s / 3.0 s | 15.3 s / 3.1 s |

Concurrent HTTP requests (every question different, no cache hit, translation and LLM caches empty at server start). Queue wait = client latency - server processing time.

| Requests | Config | Wall time | Requests/min | Client latency p50 / max | Queue wait p50 |
|---|---|---|---|---|---|
| 4 one after another | s35 | 14.0 s | 17.1 | 3.4 s / 5.9 s | 0.0 s |
| 4 one after another | s6 | 22.8 s | 10.5 | 4.6 s / 10.7 s | 0.0 s |
| 2 at once | s35 | 10.3 s | 11.7 | 6.8 s / 10.3 s | 1.7 s |
| 2 at once | s6 | 12.2 s | 9.8 | 8.8 s / 12.2 s | 2.7 s |
| 4 at once | s35 | 10.1 s | 23.7 | 5.2 s / 10.1 s | 3.4 s |
| 4 at once | s6 | 10.4 s | 23.0 | 6.2 s / 10.4 s | 3.9 s |
| 8 at once | s35 | 23.2 s | 20.7 | 15.3 s / 23.2 s | 13.1 s |
| 8 at once | s6 | 28.4 s | 16.9 | 16.4 s / 28.4 s | 11.2 s |

## Limitations

- The eval sets have 45 questions (2 to 9 per language pair) and 90 questions (10 per language pair). The corpus is Wikipedia only.
- Human grading covers 8 answers by one grader. Judge results are approximate.
- Training answers were selected by `sentence_coverage = 1`, so the sentence-level citation rate is the same metric as the selection criterion. Fine-tuning used 66 to 125 training examples and one rank (16); hyperparameters were not tuned.
- 34 of the 138 stage-4 training and validation examples used a v2 gold chunk as source, so those adapters were not used on v2; the data was rebuilt for v2 and retrained.
- Service performance uses 30 questions, and each concurrent request pattern was measured once. The server handles one request at a time.
- The English pivot uses the same model for chunks and queries. The chunk-size and contextual-prefix experiments cover the original-text pipelines only, and the chunk-size variants are excluded from pooling.

## Repository layout

```
configs/        experiment configs (one JSON per experiment)
data/           sources.csv, processed/docs.jsonl, sft/ (raw/ is not committed)
eval/           queries.jsonl, human_labels.json, baselines/, grading sheet
experiments/    run and analysis scripts, results/ (result JSON, analysis tables)
scripts/        fetch_data, show_doc, validate_eval, make_grading_sheet
src/ragbench/   config, ingest, chunking, tokenize, embedding, evalset, metrics, generation, judge,
                cache, validation, requestlog, pipeline, regression, sft, sftdata, retrieval/
tests/          unit tests
configs/v2/     eval-set-v2 experiment configs (generated by scripts/make_v2_configs.py and make_v2_ft_configs.py)
eval/pool/      pooling candidates, labels, index
eval/v2_draft/  eval set v2 drafts, review inputs and outputs
data/sft_v2*/   training data rebuilt for v2 (general, cross-language-only), data/glossary.json glossary
outputs/        trained adapters (git-ignored)
logs/           request logs and caches (git-ignored)
```

## Licenses and sources

- Documents: Wikipedia, CC BY-SA 4.0.
- Models: BAAI/bge-m3 (MIT), BAAI/bge-reranker-v2-m3 (Apache 2.0), Qwen3-4B-Instruct-2507 and Qwen3-8B (Apache 2.0).
