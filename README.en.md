# bearing-rag-bench

[한국어](README.md) | English

An experiment repository that implements and measures RAG retrieval, generation, evaluation, operations and fine-tuning on Korean, English and German technical documents about bearings and automotive parts.
No RAG framework (LangChain, LlamaIndex) is used. Chunking, BM25, embeddings, HNSW, RRF, reranking, metrics, caching, validation and the LoRA training loop are implemented directly.

## Components

| Area | Implementation |
|---|---|
| Chunking | 384 bge-m3 tokens, 48 overlap, paragraph and sentence boundaries |
| Retrieval | BM25 (bm25s; whitespace, kiwipiepy morphemes, subword tokenizers), dense (BAAI/bge-m3 + hnswlib), RRF (k=60), reranker (BAAI/bge-reranker-v2-m3) |
| Metrics | Recall@5, MRR@10, nDCG@10 (graded), aggregated by language pair (`src/ragbench/metrics.py`) |
| Generation | Qwen3-4B-Instruct-2507 run locally, greedy decoding, top-5 chunks, two prompts (cite_v1, cite_refuse_v1) |
| Evaluation | LLM judge (Qwen3-8B) for faithfulness, answer relevance, context relevance and correctness, compared with 8 human-graded answers |
| Operations | Request logging (JSONL), LLM cache (SQLite), input/output validation, baseline-comparison regression check |
| Fine-tuning | LoRA and QLoRA (rank 16, hand-written training loop) |

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

uv run pytest -q
```

Each result JSON records the full config, package versions, git commit, model revisions, the seed (42) and per-question outputs.

## Data

- Wikipedia: 13 Korean, 16 English and 16 German articles (CC BY-SA 4.0). Sources are listed in `data/sources.csv`; the cleaned text is `data/processed/docs.jsonl`.
- 346 chunks (179 English, 124 German, 43 Korean).
- Eval set `eval/queries.jsonl`: 45 questions (15 each in ko, en, de). Gold evidence is written as document ID, evidence sentence and grade (core 2 / supporting 1) and mapped to chunks at evaluation time. The format is described in `eval/README.md` (in Korean).

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

## Limitations

- The eval set has 45 questions, 2 to 9 per language pair. The corpus is Wikipedia only.
- Human grading covers 8 answers by one grader. Judge results are approximate.
- Fine-tuning used 125 training examples, one seed and one rank (16); hyperparameters were not tuned.

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
outputs/        trained adapters (git-ignored)
logs/           request logs and caches (git-ignored)
```

## Licenses and sources

- Documents: Wikipedia, CC BY-SA 4.0.
- Models: BAAI/bge-m3 (MIT), BAAI/bge-reranker-v2-m3 (Apache 2.0), Qwen3-4B-Instruct-2507 and Qwen3-8B (Apache 2.0).
