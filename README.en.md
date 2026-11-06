# bearing-rag-bench

## [https://juunary.github.io/bearing-rag-bench/](https://juunary.github.io/bearing-rag-bench/)

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
| Evaluation | LLM judge (Qwen3-8B) for faithfulness, answer relevance, context relevance and correctness, compared with human grades (8 in round 1, 27 in round 2) |
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
uv run python experiments/serve_chat.py   # default configs/s7_pipeline_kb.json (wiki + PDF + knowledge bundle); configs/s6_pipeline_en.json = wiki only
uv run python scripts/answer_questions.py --config configs/s7_pipeline_kb.json --questions eval/kb/questions.jsonl eval/human_round2/user_questions.jsonl --out eval/service/s7_answers.json   # check a serving config

# Service performance (stage latency, concurrent requests)
uv run python experiments/bench_service.py configs/s6_pipeline_en.json --n 30
uv run python experiments/bench_chat_concurrency.py configs/s6_pipeline_en.json

# External framework comparison (LlamaIndex, Haystack, AutoRAG; separate environment comparison/.venv)
uv run python comparison/prepare_data.py                     # export the same 346 chunks and 90 questions as framework input
cd comparison && uv sync && uv run python run_frameworks.py all && uv run python make_autorag_data.py
uv run python run_autorag.py && uv run python collect_autorag.py && cd ..
uv run python experiments/run_generation.py configs/cmp/v2g_cmp_ar.json   # li and hs likewise (then run_judge.py)
uv run python experiments/analyze_comparison.py

# PDF corpus (needs a pdf-editor checkout with pnpm build)
uv run python scripts/build_pdf_docs.py --pdf-editor /path/to/pdf-editor
uv run python -m ragbench.chunking --corpus wiki_pdf   # Wikipedia + PDF chunks
uv run python experiments/build_english_chunks.py --corpus wiki_pdf
uv run python scripts/apply_pdf_review.py && uv run python scripts/validate_eval.py eval/queries_pdf.jsonl --corpus=wiki_pdf
uv run python scripts/make_pdf_configs.py && uv run python experiments/run_suite.py --glob 'configs/pdf/*.json'
uv run python experiments/analyze_pdf.py
uv run python -m ragbench.chunking --corpus wiki_pdf --table-header   # chunks with repeated table caption and header rows (configs/pdf/pdfth_*)
uv run python experiments/run_generation.py configs/pdfgen/pdfg_x13_rrf_en_dense_en_rerank_en_text.json   # answers to the PDF questions (then run_judge.py)
uv run python experiments/analyze_pdf_generation.py
uv run python scripts/export_site_data.py           # trace page data (docs/data/)
uv run python scripts/make_pdf_configs.py && uv run python experiments/run_suite.py --glob 'configs/pdf/*_c_*.json'   # concept-mediated retrieval
uv run python experiments/analyze_concepts.py
uv run python experiments/run_kb.py && uv run python experiments/analyze_kb.py   # knowledge bundle: rag / bundle / hybrid
uv run python scripts/make_model_configs.py && uv run python experiments/run_suite.py --glob 'configs/modelswap/*.json' && uv run python experiments/analyze_models.py   # model swap
uv run python experiments/run_dci.py --variant v2 && uv run python experiments/analyze_dci.py   # grep/read agent

# Judge of another model family (Granite 3.3 8B)
uv run python experiments/run_judge.py configs/s3_judge_granite.json v2g_base_bf16 v2g_ret_x2_rerank_en_text
uv run python experiments/analyze_judge_agreement.py

uv run pytest -q
```

Each result JSON records the full config, package versions, git commit, model revisions, the seed (42) and per-question outputs.

## Data

- Wikipedia: 13 Korean, 16 English and 16 German articles (CC BY-SA 4.0). Sources are listed in `data/sources.csv`; the cleaned text is `data/processed/docs.jsonl`.
- 346 chunks (179 English, 124 German, 43 Korean).
- Eval set `eval/queries.jsonl`: 45 questions (15 each in ko, en, de). Gold evidence is written as document ID, evidence sentence and grade (core 2 / supporting 1) and mapped to chunks at evaluation time. The format is described in `eval/README.md` (in Korean).
- Eval set v2 `eval/queries_v2.jsonl`: 90 questions (10 per question-language x primary-language pair). Change history in `eval/README.md`, edit log in `eval/v2_review_log.json`.
- 6 PDF documents (`data/pdf_sources.json`): 3 English NASA technical reports (public domain), 2 German Leibniz Universität Hannover dissertations (CC BY 3.0 DE) and 1 innoTRAC article (CC BY 4.0). Only public domain, CC0, CC BY, CC BY-SA and KOGL Type 1 were allowed; no Korean document passed. The PDFs are not committed (downloaded and checked by sha256); the text extracted with the layout reconstruction of pdf-editor (https://github.com/Juunary/pdf-editor) is in `data/processed/docs_pdf.jsonl`. Page headers and footers, text inside figures and table-of-contents lines are dropped, and a table becomes one line per row `| cell | cell |`. Wikipedia + PDF gives 903 chunks (`chunking.corpus = "wiki_pdf"`).
- PDF eval set `eval/queries_pdf.jsonl`: 48 questions (8 per question language ko/en/de x document language en/de pair; evidence: 26 body text, 15 table, 7 caption). Writing and review in `eval/README.md`, edit log in `eval/pdf_review_log.json`.

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
| dense top 30 + reranker (no BM25, no RRF) | 0.660 | 0.689 | 0.642 | 0.873 | 0.527 | - |
| dense top 30 + reranker (English input) | 0.784 | 0.829 | 0.778 | 0.894 | 0.720 | 0.60 s |
| English dense (translated chunks embedded, English query) | 0.782 | 0.766 | 0.738 | 0.689 | 0.763 | 0.60 s |
| English dense + reranker (English input) | 0.897 | 0.934 | 0.891 | 0.891 | 0.892 | 0.60 s |
| RRF (English BM25 + English dense) | 0.813 | 0.789 | 0.782 | 0.704 | 0.821 | 0.60 s |
| RRF (English BM25 + English dense) + reranker (English input) | 0.897 | 0.934 | 0.893 | 0.891 | 0.894 | 0.60 s |

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

Dense candidates and embeddings of the translated chunks (nDCG@10 difference, document-cluster 95% interval; these pairs were added after the results above were known): dense top 30 + reranker - RRF + reranker +0.056 (+0.025 .. +0.094); the gold chunk is inside the 30 candidates for 81/90 questions with dense and 73/90 with original RRF. English dense - dense +0.252 (+0.164 .. +0.336), RRF (English BM25 + English dense) - English RRF +0.144 (+0.059 .. +0.230), English dense + reranker (English input) - English RRF + reranker (English input) -0.003 (-0.019 .. +0.014), RRF (English BM25 + English dense) + reranker (English input) - same baseline -0.002 (-0.015 .. +0.013).

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

Judge comparison (`experiments/results/judge_agreement.md`): Granite 3.3 8B Instruct (IBM, Apache 2.0) judged the same 10 answer sets with the same prompts. Granite's YES rate is higher than Qwen3-8B's on every set (correctness +0.06 .. +0.14); agreement between the judges is 0.82 .. 0.90 on correctness, Cohen's kappa 0.24 .. 0.48. Against the 8 human-graded answers: correctness Qwen 7/7, Granite 6/7; faithfulness 5/7 for both.

Human review round 2 (`experiments/results/human_round2.md`, sample and grades in `eval/human_round2/`): one grader checked 23 questions and 27 answers among items whose question and gold sentences are in Korean or English. The answers were drawn by the correctness verdicts of the two judges: 11 where they disagree, 12 where both say YES, 4 where both say NO (out of 173 distinct answers, identical answers to the same question merged); weighted values use these stratum sizes.

| item | result |
|---|---|
| 23 questions | answerable from the gold sentences 23, wording copied from the gold sentence 0, realism high 18 / medium 3 / low 2 |
| human correctness | correct 18, partial 4, wrong 5 |
| agreement with the human (partial = wrong) | Qwen 14/27 (kappa 0.05, weighted 0.707), Granite 17/27 (kappa 0.06, weighted 0.729) |
| weighted correct rate | human 0.733 (95% CI 0.502 .. 0.949), Qwen 0.903, Granite 0.970 |
| judge correct rate - human (95% CI) | Qwen -0.041 .. +0.403, Granite +0.021 .. +0.467 |
| faithfulness, 10 answers | Qwen 8/10, Granite 6/10 agree |
| answer relevance, 27 answers | both 27/27 agree |

Of 10 questions the grader wrote without looking at the documents (`eval/human_round2/labels.json`), 5 are refused as unanswered by the best PDF-corpus retrieval (table headers repeated) with cite_refuse_v1 (`eval/human_round2/user_questions_answers.json`). The same grader graded them from practical knowledge:

| item | result |
|---|---|
| correctness of the 5 answers | correct 4, partial 1 (D03: describes EP grease as a lubricant for above 200 °C) |
| 5 refusals | appropriate 3 (drive-shaft torsional damping, EV reducer bearings, telling wheel-bearing noise from tyre noise), inappropriate 2 |
| inappropriate D05 (shaft-side causes of oil-seal leakage) | 5 chunks with statements on shaft surface finish, runout, eccentricity and lead are not in the generator context (top 5) (below) |
| inappropriate D10 (loose housing fit) | a chunk on fit tolerances is in the top 5, but a keyword search (creep, fretting, loose fit, ...) finds no chunk on the effects of a loose fit such as creep or fretting |

D05 retrieval trace (`experiments/results/d05_retrieval_trace.md`, `experiments/trace_retrieval.py`): the query is translated as "When oil leakage persists in an oil seal, what other shaft-side defect factors should be checked besides lip wear?", while the corpus documents say "radial shaft seal" and "opposing running surface".

| chunk | English BM25 rank | English dense rank | RRF rank | reranker rank |
|---|---|---|---|---|
| luh-diss-pelzer-2022#19 (runout, eccentricity) | 9 | 27 | 10 | 7 (outside the top 5) |
| de_wellendichtring#0 (shaft surface finish) | 35 | 115 | 57 (outside the 30 candidates) | - |
| luh-diss-pelzer-2022#28, #40, #43 | 64 .. 361 | 134 .. 330 | outside 50 | - |

Answers to the original question with only the context changed (`experiments/results/d05_answer_variants.md`, `experiments/answer_variants.py`): the served top 10 (with #19) is answered; the top 5 of the query with "oil seal" replaced by "radial shaft seal" (with #19) and of the query that also replaces "shaft-side defect factors" with "defects of the shaft surface" (with #19 and de_wellendichtring#0) are answered; the query translated with glossary hints ("oil seal (radial shaft seal)", #19 in the top 5) is refused. The query variants were written by an AI agent after seeing the target chunks, and the answers were not graded.

| Comparison (correctness, document-cluster 95% interval) | Qwen3-8B judge | Granite judge |
|---|---|---|
| English RRF + reranker (English input) - RRF + reranker | +0.105 (+0.013 .. +0.208) | +0.066 (+0.000 .. +0.137) |
| English RRF + reranker - RRF + reranker | +0.052 (+0.000 .. +0.114) | +0.000 (-0.037 .. +0.039) |
| English RRF + reranker (English input) - AutoRAG best pipeline | +0.086 (+0.012 .. +0.162) | +0.049 (+0.011 .. +0.104) |
| LoRA (seed 42) - base bf16 | +0.013 (-0.043 .. +0.076) | +0.013 (+0.000 .. +0.045) |
| QLoRA (seed 42) - base 4-bit | +0.013 (-0.045 .. +0.068) | +0.013 (-0.044 .. +0.071) |
| AutoRAG - LlamaIndex | +0.025 (-0.035 .. +0.089) | -0.013 (-0.056 .. +0.028) |

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

The chat server (`experiments/serve_chat.py`) lets the query translator use the generator's model, so Qwen3-4B is loaded once. For s6 the GPU memory after three queries is 2730 MiB on cuda:0 and 8782 MiB on cuda:1, and the translations of 30 v2 queries were identical to the stored cache. The table above and the one below were measured before this sharing (translator as a separate copy on cuda:0).

Since 2026-11-05 the serving config is `configs/s7_pipeline_kb.json`: the Wikipedia + PDF corpus (table headers repeated), English BM25 + English dense RRF + reranker on English text, plus the **knowledge bundle (kb_first)** (`src/ragbench/kb.py`). When a question matches one of the 24 reviewed guide pages (`data/kb/`; alias match, otherwise dense cosine 0.55 or more), retrieval is skipped and the matched pages plus their `related` pages form the context (`kb_context: "matched"`, the kb_matched mode of round 2 above); the response and the request log carry the path (`kb` / `rag`) and the matched pages. On 50 human-written practical questions (`eval/service/s7_answers.json`, `scripts/answer_questions.py`) 41 take the bundle path and 9 retrieval; the 13 blocked answers are the 8 out-of-scope questions (all refused on the retrieval path) and 5 bundle refusals (K14, K15, K51, K65, K68). The "service" set of the trace page shows these 50 paths. The bundle path uses 3.9 pages and 3,407 prompt tokens on average and generates in about 1.5 .. 6 s.

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

### External framework comparison (eval set v2, 90 questions)

LlamaIndex 0.14.25, Haystack 3.4.1 and AutoRAG 0.3.27 ran in a separate environment under `comparison/` (Python 3.11). Every system indexes this repository's 346 chunks under the same chunk ids and returns a chunk-id ranking for the same 90 questions. Embedding is bge-m3, the reranker is bge-reranker-v2-m3, and generation is Qwen3-4B-Instruct-2507 (cite_v1, top 5) for all of them; scoring uses only this repository's metrics (`ragbench.metrics`) and the same judge (Qwen3-8B), no framework metric. The framework rows use no translation.

| System | R@5 | MRR@10 | nDCG@10 | mono | cross |
|---|---|---|---|---|---|
| This repo: BM25 whitespace | 0.313 | 0.394 | 0.328 | 0.772 | 0.106 |
| LlamaIndex: BM25 | 0.323 | 0.379 | 0.323 | 0.755 | 0.107 |
| Haystack: BM25 | 0.322 | 0.380 | 0.315 | 0.761 | 0.091 |
| AutoRAG: BM25 (ko_kiwi, best of its search) | 0.333 | 0.400 | 0.333 | 0.791 | 0.104 |
| This repo: dense bge-m3 | 0.514 | 0.506 | 0.487 | 0.760 | 0.350 |
| LlamaIndex: vector | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| Haystack: dense | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| AutoRAG: vector | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| This repo: RRF | 0.341 | 0.433 | 0.360 | 0.825 | 0.128 |
| LlamaIndex: hybrid (reciprocal rerank fusion) | 0.434 | 0.471 | 0.444 | 0.811 | 0.261 |
| Haystack: hybrid (RRF) | 0.419 | 0.470 | 0.425 | 0.821 | 0.227 |
| AutoRAG: hybrid RRF | 0.397 | 0.441 | 0.407 | 0.817 | 0.203 |
| This repo: RRF + reranker | 0.608 | 0.650 | 0.586 | 0.864 | 0.448 |
| LlamaIndex: hybrid + reranker | 0.617 | 0.654 | 0.592 | 0.863 | 0.456 |
| Haystack: hybrid + reranker | 0.612 | 0.659 | 0.591 | 0.860 | 0.456 |
| AutoRAG: best pipeline of its search (30 dense candidates + reranker) | 0.660 | 0.689 | 0.642 | 0.873 | 0.527 |
| This repo: English RRF + reranker (reranker reads English) | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 |

The AutoRAG search (`comparison/autorag_retrieval.yaml`) ran 3 BM25 tokenizers, 4 hybrid modules (RRF and three convex-combination normalizations) and 3 rerankers. In the hybrid node, the module chosen by AutoRAG's own metrics is convex combination (mm) with weight 1.0, which equals the dense result. Per-module results and the per-language-pair table are in `experiments/results/cmp_analysis.md`. The same structure (dense top 30 + reranker) run with this repository's code gives nDCG@10 0.642, equal to AutoRAG; the top-10 order is identical for 78/90 questions.

Paired nDCG@10 differences (A - B, document-cluster 95% interval): LlamaIndex hybrid + reranker - this repo RRF + reranker +0.005 (-0.001 .. +0.018), Haystack +0.004 (-0.015 .. +0.027), AutoRAG best pipeline +0.056 (+0.025 .. +0.094). This repo English RRF + reranker (reranker reads English) - AutoRAG best pipeline +0.253 (+0.169 .. +0.333), - LlamaIndex +0.303 (+0.214 .. +0.385), - Haystack +0.304 (+0.217 .. +0.387).

Top 5 of each system's retrieval fed to the same base bf16 model:

| Context source | gold chunk in context | cites gold chunk | faithfulness | correctness | answer relevance |
|---|---|---|---|---|---|
| LlamaIndex hybrid + reranker | 0.778 | 0.733 | 0.911 | 0.797 | 0.937 |
| Haystack hybrid + reranker | 0.778 | 0.733 | 0.912 | 0.812 | 0.950 |
| AutoRAG best pipeline | 0.811 | 0.744 | 0.915 | 0.817 | 0.951 |
| This repo: English RRF + reranker | 0.833 | 0.744 | 0.881 | 0.857 | 0.929 |
| This repo: English RRF + reranker (reranker reads English) | 0.989 | 0.933 | 0.955 | 0.886 | 0.977 |

This repo English RRF + reranker (reranker reads English) - AutoRAG best pipeline (document-cluster 95% interval): gold chunk in context +0.178 (+0.077 .. +0.277), cites gold chunk +0.189 (+0.106 .. +0.267), faithfulness +0.049 (-0.025 .. +0.127), correctness +0.086 (+0.012 .. +0.162). AutoRAG - LlamaIndex and AutoRAG - Haystack include 0 in all four metrics (gold chunk in context has a lower bound of +0.000).

### PDF documents (Wikipedia + PDF, 903 chunks, 48 PDF questions)

| Method | R@5 | MRR@10 | nDCG@10 | mono | cross | text (26) | table (15) | caption (7) |
|---|---|---|---|---|---|---|---|---|
| BM25 kiwi | 0.300 | 0.352 | 0.308 | 0.693 | 0.116 | 0.299 | 0.377 | 0.197 |
| dense | 0.592 | 0.532 | 0.526 | 0.555 | 0.511 | 0.655 | 0.396 | 0.325 |
| RRF + reranker | 0.649 | 0.654 | 0.632 | 0.735 | 0.580 | 0.721 | 0.552 | 0.473 |
| dense top 30 + reranker | 0.664 | 0.666 | 0.632 | 0.730 | 0.582 | 0.731 | 0.521 | 0.500 |
| English BM25 | 0.667 | 0.712 | 0.668 | 0.681 | 0.661 | 0.710 | 0.649 | 0.550 |
| English dense | 0.685 | 0.601 | 0.596 | 0.585 | 0.602 | 0.687 | 0.521 | 0.418 |
| English RRF + reranker | 0.705 | 0.683 | 0.670 | 0.730 | 0.640 | 0.748 | 0.595 | 0.540 |
| English RRF + reranker (English input) | 0.841 | 0.781 | 0.755 | 0.763 | 0.750 | 0.835 | 0.657 | 0.664 |
| English dense + reranker (English input) | 0.795 | 0.733 | 0.708 | 0.742 | 0.692 | 0.799 | 0.578 | 0.650 |
| RRF (English BM25 + English dense) + reranker (English input) | 0.856 | 0.785 | 0.774 | 0.763 | 0.780 | 0.835 | 0.680 | 0.748 |

For the 5 questions whose answer is a table row with the column headers in another chunk, nDCG@10 is 0.155 .. 0.433 depending on the setting. Question-level 95% intervals (only 6 primary documents, so the document-cluster intervals are only in `experiments/results/pdf_analysis.md`): English RRF + reranker (English input) - RRF + reranker +0.123 (+0.034 .. +0.218), English BM25 - BM25 kiwi +0.359 (+0.240 .. +0.482), English dense - dense +0.070 (+0.012 .. +0.131), English dense + reranker (English input) - English RRF + reranker (English input) -0.046 (-0.100 .. +0.001), dense top 30 + reranker - RRF + reranker -0.000 (-0.023 .. +0.021). The per-language-pair table is in `pdf_analysis.md`.

Repeated table caption and header rows (`chunking.table_header`): a chunk that starts inside a table gets that table's caption and header row (the second row too when the first has empty cells) in front (41 of 903 chunks). Gold mapping keeps the original offsets.

| Method | nDCG@10 | headers repeated | diff (question-level 95% CI) | table (15) | headers repeated | header in another chunk (5) | headers repeated |
|---|---|---|---|---|---|---|---|
| RRF + reranker | 0.632 | 0.661 | +0.029 (+0.008 .. +0.055) | 0.552 | 0.642 | 0.420 | 0.551 |
| dense | 0.526 | 0.585 | +0.059 (+0.022 .. +0.105) | 0.396 | 0.562 | 0.155 | 0.557 |
| English RRF + reranker (English input) | 0.755 | 0.819 | +0.065 (+0.022 .. +0.118) | 0.657 | 0.864 | 0.316 | 0.706 |
| RRF (English BM25 + English dense) + reranker (English input) | 0.774 | 0.831 | +0.057 (+0.020 .. +0.103) | 0.680 | 0.864 | 0.360 | 0.706 |

All 10 settings are in section 5 of `pdf_analysis.md`. Only table questions change rank (9 in the best setting).

Answers to the PDF questions (base bf16 Qwen3-4B, cite_v1, top 5, top 10 in the last row; judges Qwen3-8B / Granite 3.3 8B, refusals not judged):

| Context source | gold chunk in context | cites gold chunk | faithfulness | correctness | answer relevance |
|---|---|---|---|---|---|
| RRF + reranker | 0.750 | 0.708 | 0.829 / 0.951 | 0.732 / 0.805 | 0.951 / 0.976 |
| RRF (English BM25 + English dense) + reranker (English input) | 0.917 | 0.875 | 0.978 / 0.978 | 0.889 / 0.956 | 0.978 / 0.978 |
| same retrieval + repeated table headers | 0.938 | 0.917 | 0.913 / 0.978 | 0.891 / 0.978 | 0.978 / 1.000 |
| same retrieval + repeated table headers, top 10 | 0.979 | 0.938 | 0.936 / 0.957 | 0.957 / 0.957 | 0.957 / 1.000 |

Best retrieval - RRF + reranker (question-level 95% interval): cites gold chunk +0.167 (+0.042 .. +0.312), correctness Qwen +0.150 (+0.025 .. +0.275), Granite +0.150 (+0.025 .. +0.300), faithfulness Qwen +0.150 (+0.050 .. +0.275), Granite +0.025 (-0.050 .. +0.100). Repeated table headers - best retrieval: cites gold chunk +0.042 (+0.000 .. +0.104), correctness Qwen +0.000 (-0.067 .. +0.067), Granite +0.022 (-0.044 .. +0.111), faithfulness Qwen -0.067 (-0.156 .. +0.000). Correctness by evidence kind is in `experiments/results/pdf_generation_analysis.md`.

Top 10 - top 5 (repeated table headers, question-level 95% interval): gold chunk in context +0.042 (+0.000 .. +0.104), correctness Qwen +0.067 (-0.044 .. +0.178), Granite -0.022 (-0.111 .. +0.044), faithfulness Qwen +0.022 (-0.067 .. +0.111), Granite -0.022 (-0.067 .. +0.000), sentence coverage -0.161 (-0.239 .. -0.083). The median prompt grows from 2253 to 4395 tokens. With the serving prompt (cite_refuse_v1, not judged) the same comparison gives 1 refusal instead of 3 out of 48, 1 instead of 2 refusals with a gold chunk in the prompt, and sentence coverage 0.686 instead of 0.816 (-0.131, -0.233 .. -0.023). Answering the grader's own 10 questions with the top 10 (`eval/human_round2/user_questions_answers_k10.json`, same first 5 chunks): D05 is answered citing luh-diss-pelzer-2022#19, and D07, graded correct with the top 5, is refused, so there are still 5 refusals. The top-10 answers were not graded by a person.

Searching the 90 v2 questions again on the corpus with the 557 PDF chunks changes nDCG@10 by -0.013 .. -0.040 depending on the setting (English RRF + reranker (English input) 0.895 → 0.865, document-cluster interval -0.065 .. -0.003), and 28 .. 37 questions get a PDF chunk in their top 5. The v2 gold has no PDF chunk, so a relevant PDF chunk counts as a miss.

### Concept-mediated retrieval (26 concept pages; 48 PDF questions, 90 v2 questions, 10 human-written questions)

Concept pages (`data/concepts/*.md`, OKF-style Markdown: aliases in ko/en/de, related concepts, a 2-4 sentence English description) are matched to the question (aliases first, otherwise the top dense match with cosine 0.55 or more), the chunks mentioning the matched concepts are ranked by cosine to the translated query, and the result is attached to the best retrieval (English RRF + reranker on English text) in three ways: pool (reranker pool 30 + 10 concept candidates), pool_query (pool + the canonical names of the matched concepts appended to the reranker query), rrf_query (a third RRF leg only for matched questions + the query augmentation). Concept-to-chunk links are built mechanically from alias occurrences (`src/ragbench/retrieval/concept.py`), and unmatched questions keep exactly the baseline retrieval (verified with an empty bundle: identical ranks, scores and pools on all 48 questions). The pages were written by an AI agent from the glossary and the document titles and reviewed by a person (`data/concepts_review.md`).

| setting | PDF nDCG@10 | diff (document-cluster 95% interval) | v2 nDCG@10 | diff | matched questions (PDF / v2) |
|---|---|---|---|---|---|
| best retrieval | 0.831 | - | 0.869 | - | - |
| + pool | 0.831 | +0.000 (0/0/48) | 0.869 | +0.000 (0/0/90) | 43 / 65 |
| + pool, 30 candidates | 0.830 | -0.001 (-0.004 .. +0.000) | 0.879 | +0.010 (-0.002 .. +0.038) | 43 / 65 |
| + pool_query | 0.765 | -0.066 (-0.111 .. -0.027) | 0.859 | -0.010 (-0.042 .. +0.021) | 43 / 65 |
| + rrf_query | 0.768 | -0.064 (-0.105 .. -0.027) | 0.860 | -0.009 (-0.041 .. +0.022) | 43 / 65 |

pool added 1.1 .. 1.3 candidates per question, but only 2 (PDF) and 7 (v2) of them reached the top 10 and one was a gold chunk, so the metrics did not change. With 30 concept candidates, 10.4 .. 11.0 chunks per question are added and 20 (PDF) / 32 (v2, 4 gold) reach the top 10, but the nDCG differences include zero on both sets (v2: 1 better, 3 worse), p50 latency grows by about 80 ms, and the D05 chunks still do not reach the pool. The query augmentation lowered the reranker ranks of matched questions (of 43 matched PDF questions, 2 better, 18 worse). The 10 human-written questions (cite_refuse_v1) are refused 5 times under every variant. With pool_query and rrf_query, D05 is answered because `luh-diss-pelzer-2022#19` moves from rank 7 to 3 (the answer was not graded), but the other 4 related chunks (`de_wellendichtring#0`, ...) still do not reach the pool, and D07, answered correctly with the top 5, is refused under both. Details are in `experiments/results/concept_analysis.md`.

### Curated knowledge bundle: RAG, whole bundle, hybrid (20 practical questions)

12 practical guide pages (`data/kb/*.md`, Korean, 9,638 body tokens: loose fits, oil seal leakage checks, grease selection, relubrication, preload setting, failure modes, vibration diagnosis, oil analysis, wheel bearing noise, driveline torsional damping, EV reducer bearings, storage and handling) were written by an AI agent from general engineering knowledge and reviewed by a person after the questions were written (`data/kb_review.md`, approved without changes). The 20 questions (`eval/kb/questions.jsonl`) were written by the same person from the topic list before seeing the pages; 16 are within the topics and 4 outside (brake pads, V-belts, hydraulic pumps, DPF). Three modes: `rag` (the serving pipeline: best PDF-corpus retrieval + cite_refuse_v1, top 5), `bundle` (no retrieval, all 12 pages as the context), `hybrid` (bundle only when rag is blocked), plus `kb_first` and `both` below. Same generator, prompt and output validation; the answers were graded blind by the same person (`experiments/results/kb_analysis.md`).

| mode | in-scope 16: correct / partial / wrong / refused | out-of-scope 4: refused | prompt tokens, mean | generation, mean |
|---|---|---|---|---|
| rag | 2 / 4 / 2 / 8 | 4 (all appropriate) | 2,188 | 3.4 s |
| bundle | 14 / 0 / 0 / 2 | 4 (all appropriate) | 10,081 | 4.8 s |
| hybrid | 9 / 4 / 2 / 1 | 4 (all appropriate) | 8,237 | 6.3 s |
| kb_first | 14 / 0 / 0 / 2 | 4 (all appropriate) | 8,520 | 4.3 s |
| both | 13 / 2 / 1 / 0 | 4 (all appropriate) | 12,121 | 5.3 s |

All 8 rag refusals were questions the bundle answers (graded inappropriate), and only 2 of its 8 answers were correct. bundle answered 14 in-scope questions correctly and refused all 4 out-of-scope ones; its 2 refusals are an answer cut at 256 tokens before any citation (K05) and a refusal although the page covers the question (K15). hybrid passed the 12 rag refusals to the bundle and got 11 right, but the 6 answers that rag gave without refusing (partial or wrong) stayed; the 2 wrong ones answered a torsional-vibration question with needle roller bearings and diagnosed electrical fluting as fretting. bundle costs 4.6 times the prompt tokens of rag.

Two more modes target the weakness of hybrid (a wrong rag answer that is not a refusal never reaches the bundle). `kb_first` answers from the bundle when the question matches a bundle page (alias match, otherwise the best dense match with cosine 0.55 or more; the threshold was fixed before the run), else from rag. All 16 in-scope questions matched (10 by alias, 6 by dense) and none of the 4 out-of-scope ones, so its results equal bundle (14 / 0 / 0 / 2); the margin is thin, though (best out-of-scope cosine 0.54, lowest in-scope match 0.57). `both` puts the 12 pages and the 5 rag chunks in one context: it answered all 16 in-scope questions (including K05 and K15, which bundle refused) and refused all out-of-scope ones, but has 13 correct instead of 14, one wrong answer (tapered-roller adjustment for an angular-contact preload question) and two partial ones, at 5.5 times the tokens of rag.

#### Round 2: 24 pages, 20 new questions, matched pages only (`kb_matched`)

12 more pages (bearing type selection, lubrication method, shaft misalignment, operating temperature, machine bearing noise, electric motor bearings, gearbox bearing failures, wheel hub bearing replacement, CV joints and boots, seat repair, reuse assessment, designations) were added by the same procedure (AI draft -> sealed commit -> 20 questions written by a person -> review and approval, `data/kb_review.md`, round 2). The new questions `eval/kb/questions2.jsonl` (K50-K69) have 16 within the new topics and 4 outside (A/C clutch, injector washer, hydraulic cylinder seal, V-belt). The prompt with all 24 pages is 20,148 tokens and does not fit one 12 GB GPU, so the generator was split over two GPUs (`experiments/run_kb.py --gen-device auto`); `kb_matched` (the kb_first decision with only the matched pages and their `related` pages, 3-5 pages, usable in serving) was added, and the three modes were graded blind by the same person (`eval/kb2/`, `experiments/results/kb2_analysis.md`).

| mode | 16 in-scope: correct / partial / wrong / refused | 4 out-of-scope: refused | prompt tokens, mean (in-scope) | generation, mean (in-scope) |
|---|---|---|---|---|
| rag | 5 / 1 / 1 / 9 (appropriate 1, inappropriate 8) | 4 (all appropriate) | 2,242 | (cached) |
| kb_first (all 24 pages) | 8 / 1 / 3 / 4 (appropriate 1, inappropriate 3) | 4 (all appropriate) | 20,147 | 10.7 s |
| kb_matched (3-5 pages) | 11 / 1 / 1 / 3 (appropriate 1, inappropriate 2) | 4 (all appropriate) | 3,737 | 5.4 s |

The decision matched all 16 in-scope questions (alias 4, dense 12) and none of the 4 out-of-scope ones, but the gap between the lowest in-scope cosine 0.55 (K54, K65) and the highest out-of-scope 0.53 is narrower than in round 1. Three questions matched a page other than the assigned topic (K53 -> vibration diagnosis, K65 -> designations, K67 -> failure modes) and the `related` pages filled the context. With all 24 pages the result is worse than round 1 (12 pages, 14 / 0 / 0 / 2): K56 and K61 are blocked (invalid citation, no citation) and K60 is wrong, while all three are correct with the matched pages only. Questions both bundle modes got wrong or refused: K50 (lower bearing of a vertical motor, both wrong), K54 (2RS1 described as a one-sided seal, both partial), K65 (C vs C0, not on the pages, both refused; rag correct), K68 (pressing a 2nd-generation wheel bearing, both refused; rag correct); on K51 (soft foot measurement) all pages gave a wrong answer and the matched pages a refusal. rag answered 5 of the 16 new in-scope questions correctly (round 1: 2) and 8 of its 9 refusals were questions the bundle answers.

### Model swap: 2026 embedding and reranker models (one at a time)

One model was replaced in the best pipelines (`scripts/make_model_configs.py`; prompts, pooling and dtype follow the model cards: Qwen3-Embedding with last-token pooling and an instruction prefix, EmbeddingGemma 2 with mean pooling and `task: search result | query:` / `title: none | text:`, Qwen3-Reranker scored as P(yes) from the yes/no logits, all bf16). Baselines: English RRF + reranker on English text (x2) for v2, English BM25 + English dense RRF + reranker on English text (x13, table-header chunks) for PDF. Differences are nDCG@10 with document-cluster 95% intervals (`experiments/results/model_swap.md`).

| swap | v2 90 nDCG@10 (diff) | PDF 48 nDCG@10 (diff) | query p50 (v2 / PDF) |
|---|---|---|---|
| baseline bge-m3 / bge-reranker-v2-m3 | 0.895 | 0.831 | 184 / 196 ms |
| embedding → Qwen3-Embedding-0.6B | 0.878 (-0.017, -0.043 .. +0.004) | 0.816 (-0.015, -0.046 .. +0.000) | 196 / 213 ms |
| embedding → EmbeddingGemma 2 | 0.890 (-0.005, -0.013 .. +0.002) | 0.832 (+0.001, +0.000 .. +0.002) | 201 / 222 ms |
| reranker → Qwen3-Reranker-0.6B | 0.854 (-0.040, -0.072 .. -0.010) | 0.850 (+0.018, -0.036 .. +0.070) | 660 / 570 ms |
| reranker → Qwen3-Reranker-4B | 0.901 (+0.006, -0.030 .. +0.041) | 0.896 (+0.065, -0.004 .. +0.130) | 3,688 / 2,969 ms |

The embedding swaps are indistinguishable or slightly worse on both sets. Qwen3-Reranker-0.6B is clearly worse on v2 (26 worse, 13 better); Qwen3-Reranker-4B gives +0.065 on PDF (R@5 0.882 → 0.931, cross-language 0.842 → 0.920) with an interval touching zero and no difference on v2. The 4B reranker takes about 3 s to score 30 candidates, 15 .. 19 times the baseline, and needs 8 GiB more GPU memory (bf16). The default models were not changed.

### Direct corpus interaction (DCI): a grep/read agent (the 20 questions RAG refused)

Instead of one top-k retrieval step, the same generator (Qwen3-4B, greedy) searched the corpus itself with `grep` (original text and English translation of the 903 chunks, up to 10 hits), `read` (chunk text + translation) and `answer` (citing read chunks, or NO_ANSWER) (`experiments/run_dci.py`; the direct corpus interaction of arXiv 2605.05242 and the OKF folder mode). Budget 8 calls; output validation as in the pipeline, with the read chunks as the allowed citations. Questions: everything the serving pipeline (cite_refuse_v1) refused: 5 human-written, 12 practical (4 outside the bundle topics), 3 PDF questions with gold chunks. v1 uses regex grep; v2 an all-terms grep (every term, any order) and a prompt asking for one or two key terms per search (`experiments/results/dci_analysis.md`).

| variant | human 5 | practical 12 (in 8 / out 4) | PDF 3: answered / gold read | per question: calls · tokens · seconds |
|---|---|---|---|---|
| v1 | answered 0 | answered 2 / refused 4 | 1 / 0 | 7.2 · 4,700 · 9 s |
| v2 | answered 2 | answered 5 / refused 4 | 1 / 0 | 6.2 · 7,800 · 12 s |

In v1 the 4B model searched with sentence-long regexes ("oil seal.*lip wear.*shaft") and read almost nothing. The 7 v2 answers were graded by a person: 1 correct, 4 partial, 2 wrong (the knowledge bundle answered the same 6 practical questions correctly). D05 (oil seal) still did not reach the relevant chunks in v2 (only `en_radial_shaft_seal#0` was read), and in both variants none of the 3 PDF questions had its gold chunk read. The 4 out-of-scope questions were refused by both variants.

## Limitations

- The eval sets have 45 questions (2 to 9 per language pair) and 90 questions (10 per language pair) on the Wikipedia corpus. The PDF documents are evaluated only in a separate corpus (Wikipedia + PDF) with 48 PDF questions.
- Of 10 practical questions the grader wrote without looking at the documents, 5 were refused (grader: appropriate 3, inappropriate 2); the corpus (Wikipedia, NASA reports, theses) has little on maintenance, diagnosis and design practice. These 10 answers were not graded by the judges.
- Human grading covers 35 answers (8 in round 1, 27 in round 2) by one grader; round 2 covers Korean and English items only. In round 2 the judges' correct rate is higher than the human grade (weighted difference Qwen +0.17, Granite +0.24) and their kappa with the human is below 0.1. Judge results are approximate, and differences between conditions were not checked against human grades. The second judge (Granite) says YES more often and the two judges agree with low kappa (correctness 0.24 .. 0.48). Granite's verdict line was cut off by the 80-token limit for about 30 answers per result set; those were asked again once with three times the limit.
- Training answers were selected by `sentence_coverage = 1`, so the sentence-level citation rate is the same metric as the selection criterion. Fine-tuning used 66 to 125 training examples and one rank (16); hyperparameters were not tuned.
- 34 of the 138 stage-4 training and validation examples used a v2 gold chunk as source, so those adapters were not used on v2; the data was rebuilt for v2 and retrained.
- Service performance uses 30 questions, and each concurrent request pattern was measured once. The server handles one request at a time.
- The English pivot uses the same model for chunks and queries. The chunk-size and contextual-prefix experiments cover the original-text pipelines only, and the chunk-size variants are excluded from pooling.
- The framework comparison feeds this repository's 346 chunks to every system; each framework's document loader, chunker and any translation (pivot) feature are not compared. The framework rows have no English pivot.
- LlamaIndex and Haystack have one hybrid + reranker configuration each, without parameter search. The AutoRAG search is limited to 11 modules of the retrieval and reranking nodes; query expansion, prompt and generation nodes were not searched. The generation comparison uses the best configuration of each system and one judge model.
- Table-header repetition treats the first table row (and the second when the first has empty cells) as the header, and uses as caption only one of the 1-2 paragraphs before the table that starts with TABLE/Table/Tabelle. Where an equation was detected as a table, its lines are repeated as a header too. Chunks with a header reach up to 508 tokens.
- The PDF corpus has no Korean document (Korean is used only as a question language) and has 6 documents and 48 questions (8 per language pair). The PDF questions were written by an AI agent and reviewed by two other AI agents, not by a human. The extracted text contains tables that were not detected as tables (two NASA TMs), tables whose multi-line cells were split into rows, and reference lists, symbol lists and a CV left in the dissertations because their headings were not detected.
- The concept pages were written by an AI agent that knew the D05 failure analysis (oil seal vs radial shaft seal), so the 10 human-written questions are not a fair test of the seal pages; the conclusions rest on the 48 PDF and 90 v2 questions. The dense matching threshold 0.55 is an untuned estimate, and only two concept candidate counts (10, 30) were tried.
- The knowledge bundle experiment has two rounds of 20 questions (12 and 24 pages) and one grader; the pages were written by an AI agent and approved by a person on reading, not checked against manufacturer data or standard texts. Bundle answers cite the summary pages, not original documents. The kb_first matching threshold is an untuned fixed value, and the margin on 20 questions is narrow.
- The model swap uses one configuration per model (the model card's default prompt and pooling); query instructions and Matryoshka dimensions were not explored. Latencies were measured while the GPUs were shared with another user.
- The DCI experiment has 20 questions, 2 variants and an 8-call budget with a one-line JSON tool protocol. The search strategy was steered only through the prompt (v2); other models or tool designs (summaries first, document-level reads) were not tried.
- The paired intervals in the comparison were chosen after seeing the numbers and have no multiplicity correction. Latency is not compared across systems (this repository's English-pivot rows include translation, AutoRAG's is its own batch time).

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
comparison/     external framework comparison (separate environment): prepare_data, run_frameworks, run_autorag, collect_autorag
configs/cmp/    generation configs that take the frameworks' retrieval results
data/pdf_sources.json, data/processed/docs_pdf.jsonl   PDF sources (license evidence, sha256) and extracted text
scripts/build_pdf_docs.py, scripts/pdf_layout_export.mjs   PDF download, layout export and document building
eval/queries_pdf.jsonl, eval/pdf_draft/   PDF eval set, drafts and review inputs/outputs
configs/pdf/    retrieval configs on the Wikipedia + PDF corpus (written by scripts/make_pdf_configs.py)
configs/pdfgen/ generation configs for the PDF questions
eval/human_round2/   human review round 2: sample, sheet, grades, answers to the grader's own questions (scripts/make_human_round2.py, render_human_round2.py, answer_user_questions.py)
data/concepts/       26 concept pages (OKF-style Markdown), data/concepts_review.md human review record
data/kb/             24 practical guide pages (reviewed by a person, data/kb_review.md), eval/kb/ 2 x 20 questions, round-1 answers and grades, eval/kb2/ round-2 answers and grades (experiments/run_kb.py, analyze_kb.py)
configs/modelswap/      model swap configs (scripts/make_model_configs.py), analysis experiments/analyze_models.py
src/ragbench/kb.py, eval/service/   serving-side knowledge bundle (kb_first) and the serving config's answers (scripts/answer_questions.py)
eval/dci/            DCI agent results, trajectories, grades (experiments/run_dci.py, analyze_dci.py)
src/ragbench/concepts.py, retrieval/concept.py   concept loader and matcher, concept candidate retriever (experiments/analyze_concepts.py)
docs/           pipeline trace page (GitHub Pages, master branch docs/), data built by scripts/export_site_data.py
outputs/        trained adapters (git-ignored)
logs/           request logs and caches (git-ignored)
```

## Licenses and sources

- Documents: Wikipedia, CC BY-SA 4.0.
- PDF documents: NASA NTRS technical reports TP-2013-215305/REV1, TM-2017-219545, TM-2015-218895 (US Government works, public domain); Stuhler (2024) and Pelzer (2022), dissertations, Leibniz Universität Hannover (CC BY 3.0 DE, doi:10.15488/17341, doi:10.15488/11718); Katzer, Bankwitz, Hübler, innoTRAC Journal 1 (2020) 140-148 (CC BY 4.0). The extracted text keeps the license of its source.
- PDF layout extraction: pdf-editor (AGPL-3.0); its code is not copied into this repository but imported at run time.
- Models: BAAI/bge-m3 (MIT), BAAI/bge-reranker-v2-m3 (Apache 2.0), Qwen3-4B-Instruct-2507 and Qwen3-8B (Apache 2.0), ibm-granite/granite-3.3-8b-instruct (Apache 2.0).
