# bearing-rag-bench

한국어·영어·독일어 베어링·자동차 부품 기술문서를 대상으로 RAG의 검색, 생성, 평가, 운영, 파인튜닝을 구현하고 측정한 실험 저장소입니다.
LangChain, LlamaIndex 같은 프레임워크 없이 청킹, BM25, 임베딩, HNSW, RRF, 리랭킹, 지표, 캐시, 검증, LoRA 학습 루프를 직접 구현했습니다.

## 구성

| 영역 | 구현 |
|---|---|
| 청킹 | bge-m3 토큰 384개, 겹침 48, 문단·문장 경계 |
| 검색 | BM25(bm25s; 공백·kiwipiepy 형태소·서브워드 토크나이저), dense(BAAI/bge-m3 + hnswlib), RRF(k=60), 리랭커(BAAI/bge-reranker-v2-m3) |
| 지표 | Recall@5, MRR@10, nDCG@10(등급형), 언어쌍별 집계 (`src/ragbench/metrics.py`) |
| 생성 | Qwen3-4B-Instruct-2507 로컬 실행, greedy, 상위 5개 청크, 프롬프트 2종(cite_v1, cite_refuse_v1) |
| 평가 | LLM 판정(Qwen3-8B)으로 충실도·답변 관련성·컨텍스트 관련성·정확성 판정, 사람 채점 8개와 비교 |
| 운영 | 요청 로깅(JSONL), LLM 캐시(SQLite), 입출력 검증, 기준선 비교 회귀 테스트 |
| 파인튜닝 | LoRA, QLoRA(rank 16, 직접 작성한 학습 루프) |

## 요구 사항

- Python 3.12, [uv](https://docs.astral.sh/uv/)
- NVIDIA GPU. RTX 3080 Ti 12GB 2장에서 실행했습니다. 검색 약 3GiB, 생성 7.5GiB, QLoRA 학습 4.3GiB, LoRA 학습 9.4GiB, 판정 모델은 2장에 분할합니다.
- torch는 CUDA 12.6 인덱스로 고정되어 있습니다(`pyproject.toml`).

## 실행

```bash
uv sync
uv run python scripts/fetch_data.py                 # 위키백과 45건 수집 (data/raw, 커밋 안 함)
uv run python -m ragbench.ingest                    # 정제 -> data/processed/docs.jsonl
uv run python -m ragbench.chunking                  # 청크 346개
uv run python scripts/validate_eval.py              # 평가셋 검사
```

실험 1개는 설정 파일 1개와 명령 1줄입니다.

```bash
uv run python experiments/run_retrieval.py configs/s1_hybrid_rrf_rerank.json
```

```bash
# 1단계 검색
for c in configs/s1_*.json; do uv run python experiments/run_retrieval.py $c; done
uv run python experiments/run_hnsw_sweep.py
uv run python experiments/compare.py experiments/results/s1_*.json --by-group
uv run python experiments/analyze_s1.py

# 3, 3.5단계 생성, 평가, 운영
uv run python experiments/run_generation.py configs/s3_gen_cite_refuse_v1.json
uv run python experiments/run_judge.py configs/s3_judge.json s3_gen_cite_v1 s3_gen_cite_refuse_v1
uv run python experiments/analyze_judge.py
uv run python experiments/run_pipeline.py configs/s35_pipeline.json
uv run python experiments/regression.py configs/s3_gen_cite_refuse_v1.json --run

# 4단계 파인튜닝
uv run python experiments/build_sft_data.py          # 학습 데이터 생성(커밋된 data/sft로 건너뛸 수 있음)
uv run python experiments/train_lora.py configs/s4_qlora_r16.json
uv run python experiments/train_lora.py configs/s4_lora_r16.json
for c in s4_gen_base4bit s4_gen_qlora_r16 s4_gen_lora_r16; do uv run python experiments/run_generation.py configs/$c.json; done
uv run python experiments/run_judge.py configs/s3_judge.json s4_gen_base4bit s4_gen_qlora_r16 s4_gen_lora_r16
uv run python experiments/analyze_s4.py

uv run pytest -q
```

결과 JSON에는 설정 전체, 패키지 버전, git 커밋, 모델 리비전, 시드(42), 질문별 출력이 들어 있습니다.

## 데이터

- 위키백과 한국어 13건, 영어 16건, 독일어 16건(CC BY-SA 4.0). 출처 목록은 `data/sources.csv`, 정제본은 `data/processed/docs.jsonl`입니다.
- 청크 346개(영어 179, 독일어 124, 한국어 43).
- 평가셋 `eval/queries.jsonl`: 질문 45개(ko·en·de 각 15개). 정답은 문서 ID, 근거 문장, 등급(핵심 2 / 보조 1)으로 적었고 평가 시 청크로 매핑합니다. 형식은 `eval/README.md`에 있습니다.

## 결과

### 검색 (질문 45개)

| 방식 | Recall@5 | MRR@10 | nDCG@10 | 단일 언어 nDCG | 교차 언어 nDCG | 질문당 지연 p50 |
|---|---|---|---|---|---|---|
| BM25 공백 | 0.404 | 0.430 | 0.421 | 0.786 | 0.101 | 0.09 ms |
| BM25 형태소 | 0.411 | 0.425 | 0.410 | 0.781 | 0.086 | 0.15 ms |
| BM25 서브워드 | 0.400 | 0.428 | 0.422 | 0.798 | 0.093 | 0.20 ms |
| dense (HNSW) | 0.511 | 0.505 | 0.510 | 0.697 | 0.345 | 7.9 ms |
| 하이브리드 RRF | 0.411 | 0.428 | 0.426 | 0.808 | 0.092 | 8.6 ms |
| RRF + 리랭커 | 0.615 | 0.702 | 0.631 | 0.835 | 0.453 | 168.4 ms |

언어쌍별 표, 부트스트랩 신뢰구간, 쌍체 비교는 `experiments/results/s1_comparison.md`, `s1_analysis.md`에 있습니다.

HNSW (346벡터, 전수검색 대비 recall@10, 전수검색 p50 0.040 ms)

| ef_search | recall@10 | p50 지연 |
|---|---|---|
| 16 | 0.951 | 0.020 ms |
| 64 | 1.000 | 0.039 ms |
| 128 | 1.000 | 0.056 ms |
| 256 | 1.000 | 0.075 ms |

### 생성과 평가 (질문 45개)

| | cite_v1 | cite_refuse_v1 |
|---|---|---|
| 답변에 인용이 있음 | 97.8% | 91.1% |
| 정답 청크를 인용함 | 75.6% | 75.6% |
| 거절 | 0% | 8.9% |
| 충실도 (판정) | 92.5% | 95.0% |
| 답변 관련성 (판정) | 97.5% | 100% |
| 컨텍스트 관련성 (판정) | 88.9% | 88.9% |
| 정확성 (판정) | 85.0% | 80.0% |
| 생성 시간 p50 | 3.6초 | 2.9초 |

- 사람 채점 8개와 판정 모델의 일치: 정확성 7/7, 답변 관련성 7/7, 충실도 5/7.
- 결과 유형(두 프롬프트 동일): ok 29, 생성 실패 6, 검색 실패 5, 올바른 거절 4, 과잉 거절 1.

### 운영

| 기능 | 결과 |
|---|---|
| LLM 캐시 | 2회차 45건 모두 히트, 질문당 지연 p50 3212 ms에서 176 ms |
| 입출력 검증 | 45건 중 5건 차단 |
| 회귀 테스트 | 기준선 6개, 현재 모두 PASS (같으면 PASS, 지표가 0.02 넘게 하락하면 FAIL) |

### LoRA / QLoRA 파인튜닝

과제는 모든 문장에 유효한 인용을 다는 인용 완결성입니다. 학습 데이터는 125개(검증 13개)이며, 기반 모델이 샘플링한 답 중 필터를 통과한 것을 썼습니다(`data/sft/stats.json`).

| 조건 | 문장 단위 인용률 | 인용 ID 유효 | 충실도 | 답변 관련성 | 정확성 |
|---|---|---|---|---|---|
| 기반 bf16 | 0.857 | 0.978 | 0.925 | 0.975 | 0.850 |
| 기반 4비트 | 0.636 | 0.978 | 0.976 | 0.976 | 0.780 |
| QLoRA (4비트 기반) | 0.946 | 0.956 | 0.976 | 0.927 | 0.780 |
| LoRA (bf16 기반) | 0.886 | 0.978 | 0.902 | 0.976 | 0.829 |

| 학습 비용 | QLoRA | LoRA |
|---|---|---|
| 기반 가중치 | 2.5 GiB | 7.5 GiB |
| 최대 GPU 메모리 | 4.3 GiB | 9.4 GiB |
| 학습 시간 | 9.9분 | 9.7분 |
| 학습 파라미터 / 어댑터 | 33.0M / 126MB | 33.0M / 126MB |

## 한계

- 평가 질문은 45개이고 언어쌍별로는 2~9개입니다. 코퍼스는 위키백과 문서만 사용했습니다.
- 사람 채점은 답변 8개, 채점자 1명입니다. 판정 모델의 결과는 근사치입니다.
- 파인튜닝은 학습 예시 125개, 시드 1개, rank 16 하나이며 하이퍼파라미터를 튜닝하지 않았습니다.

## 저장소 구조

```
configs/        실험 설정 JSON (실험 1개 = 파일 1개)
data/           sources.csv, processed/docs.jsonl, sft/ (원문 raw/는 커밋하지 않음)
eval/           queries.jsonl, human_labels.json, baselines/, 채점표
experiments/    실행·분석 스크립트와 results/ (결과 JSON, 분석 표)
scripts/        fetch_data, show_doc, validate_eval, make_grading_sheet
src/ragbench/   config, ingest, chunking, tokenize, embedding, evalset, metrics, generation, judge,
                cache, validation, requestlog, pipeline, regression, sft, sftdata, retrieval/
tests/          단위 테스트
outputs/        학습된 어댑터 (git 제외)
logs/           요청 로그와 캐시 (git 제외)
```

## 라이선스와 출처

- 문서: 위키백과, CC BY-SA 4.0.
- 모델: BAAI/bge-m3(MIT), BAAI/bge-reranker-v2-m3(Apache 2.0), Qwen3-4B-Instruct-2507과 Qwen3-8B(Apache 2.0).
