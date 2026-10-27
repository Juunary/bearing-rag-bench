# bearing-rag-bench

한국어 | [English](README.en.md)

한국어·영어·독일어 베어링·자동차 부품 기술문서를 대상으로 RAG의 검색, 생성, 평가, 운영, 파인튜닝을 구현하고 측정한 실험 저장소입니다.
LangChain, LlamaIndex 같은 프레임워크 없이 청킹, BM25, 임베딩, HNSW, RRF, 리랭킹, 지표, 캐시, 검증, LoRA 학습 루프를 직접 구현했습니다.

## 구성

| 영역 | 구현 |
|---|---|
| 청킹 | bge-m3 토큰 384개, 겹침 48, 문단·문장 경계 |
| 검색 | BM25(bm25s; 공백·kiwipiepy 형태소·서브워드 토크나이저), dense(BAAI/bge-m3 + hnswlib), RRF(k=60), 리랭커(BAAI/bge-reranker-v2-m3) |
| 지표 | Recall@5, MRR@10, nDCG@10(등급형), 언어쌍별 집계, 중복 청크 ID는 첫 등장만 점수 (`src/ragbench/metrics.py`); 문서 군집 부트스트랩·부호 검정 (`src/ragbench/stats.py`) |
| 생성 | Qwen3-4B-Instruct-2507 로컬 실행, greedy, 상위 5개 청크, 프롬프트 2종(cite_v1, cite_refuse_v1) |
| 평가 | LLM 판정(Qwen3-8B)으로 충실도·답변 관련성·컨텍스트 관련성·정확성 판정, 사람 채점 8개와 비교 |
| 운영 | 요청 로깅(JSONL), LLM 캐시(SQLite), 입출력 검증, 기준선 비교 회귀 테스트 |
| 파인튜닝 | LoRA, QLoRA(rank 16, 직접 작성한 학습 루프) |
| 영어 피벗 | Qwen3-4B-Instruct-2507로 청크와 질의를 영어로 번역해 영어 BM25 (청킹 후 번역, 문서 먼저 번역), 용어집 힌트, 어간 추출, 질의 확장(multi, HyDE), 리랭커 영어 입력 |
| 서비스 | FastAPI 로컬 채팅 서버(127.0.0.1) 위에 검증·캐시·로그가 있는 파이프라인 |

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

# 5단계 영어 피벗 (청크 번역 후 실험)
uv run python experiments/build_english_chunks.py     # 한국어·독일어 청크를 영어로 번역
uv run python experiments/run_retrieval.py configs/s5_bm25_en_whitespace.json

# 평가셋 v2(질문 90개) 개선 실험
uv run python scripts/make_v2_configs.py && uv run python experiments/run_suite.py
uv run python experiments/analyze_v2.py
uv run python scripts/make_pool.py --depth 3 --shards 8   # 풀링 후보 (라벨 후 experiments/eval_pooled.py)
uv run python scripts/make_v2_ft_configs.py --retrieval v2_b_rrf_en_rerank
uv run python experiments/analyze_v2_generation.py

# 로컬 채팅 서버 (http://127.0.0.1:8000)
uv run python experiments/serve_chat.py configs/s35_pipeline.json

# 서비스 성능 (단계별 지연, 동시 요청)
uv run python experiments/bench_service.py configs/s6_pipeline_en.json --n 30
uv run python experiments/bench_chat_concurrency.py configs/s6_pipeline_en.json

# 외부 프레임워크 비교 (LlamaIndex, Haystack, AutoRAG; 별도 환경 comparison/.venv)
uv run python comparison/prepare_data.py                     # 같은 346 청크·90문항을 프레임워크 입력으로 내보냄
cd comparison && uv sync && uv run python run_frameworks.py all && uv run python make_autorag_data.py
uv run python run_autorag.py && uv run python collect_autorag.py && cd ..
uv run python experiments/run_generation.py configs/cmp/v2g_cmp_ar.json   # li, hs도 같은 방식 (이후 run_judge.py)
uv run python experiments/analyze_comparison.py

uv run pytest -q
```

결과 JSON에는 설정 전체, 패키지 버전, git 커밋, 모델 리비전, 시드(42), 질문별 출력이 들어 있습니다.

## 데이터

- 위키백과 한국어 13건, 영어 16건, 독일어 16건(CC BY-SA 4.0). 출처 목록은 `data/sources.csv`, 정제본은 `data/processed/docs.jsonl`입니다.
- 청크 346개(영어 179, 독일어 124, 한국어 43).
- 평가셋 `eval/queries.jsonl`: 질문 45개(ko·en·de 각 15개). 정답은 문서 ID, 근거 문장, 등급(핵심 2 / 보조 1)으로 적었고 평가 시 청크로 매핑합니다. 형식은 `eval/README.md`에 있습니다.
- 평가셋 v2 `eval/queries_v2.jsonl`: 질문 90개(질문 언어 x 주 근거 언어 9개 쌍마다 10개). 변경 이력은 `eval/README.md`, 수정 기록은 `eval/v2_review_log.json`에 있습니다.

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

### 검색 (평가셋 v2, 질문 90개)

| 방식 | Recall@5 | MRR@10 | nDCG@10 | 단일 언어 nDCG | 교차 언어 nDCG | 질문당 번역·확장 시간 |
|---|---|---|---|---|---|---|
| BM25 kiwi | 0.330 | 0.405 | 0.336 | 0.788 | 0.110 | - |
| dense (HNSW) | 0.514 | 0.506 | 0.487 | 0.760 | 0.350 | - |
| RRF | 0.341 | 0.433 | 0.360 | 0.825 | 0.128 | - |
| RRF + 리랭커 | 0.608 | 0.650 | 0.586 | 0.864 | 0.448 | - |
| 영어 BM25 (청킹 후 번역) | 0.745 | 0.768 | 0.749 | 0.702 | 0.772 | 0.60 s |
| 영어 BM25 + 용어집 | 0.782 | 0.784 | 0.770 | 0.778 | 0.767 | 0.57 s |
| 영어 BM25 + 어간 추출 | 0.781 | 0.762 | 0.756 | 0.719 | 0.774 | 0.60 s |
| 영어 BM25 + 질의 확장 multi | 0.720 | 0.708 | 0.688 | 0.626 | 0.719 | 1.90 s |
| 영어 BM25 + 질의 확장 HyDE | 0.817 | 0.767 | 0.769 | 0.771 | 0.768 | 2.67 s |
| 영어 RRF | 0.695 | 0.647 | 0.637 | 0.784 | 0.564 | 0.60 s |
| 영어 RRF + 리랭커 | 0.679 | 0.700 | 0.656 | 0.876 | 0.545 | 0.60 s |
| 영어 RRF + 리랭커(영어 청크·영어 질의 입력) | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 | 0.60 s |
| 3중 RRF(영어 BM25 + kiwi BM25 + dense) | 0.391 | 0.465 | 0.455 | 0.812 | 0.276 | 0.60 s |
| 3중 RRF + 리랭커 | 0.658 | 0.684 | 0.639 | 0.869 | 0.524 | 0.60 s |

번역·확장 시간은 캐시에 저장된 원래 생성 시간의 중앙값입니다. 질의 번역을 건너뛰는 설정(영어로 보이는 질문)은 nDCG 0.756입니다.

사전에 정한 비교(nDCG@10 차이 A - B, 주 근거 문서 단위 95% 구간, 27개 비교, 다중 비교 보정 없음)는 `experiments/results/v2_analysis.md`에 있습니다.

| A | B | 차이 | 95% 구간(문서 군집) |
|---|---|---|---|
| 영어 BM25 | BM25 kiwi | +0.413 | +0.307 .. +0.515 |
| 영어 RRF + 리랭커 | RRF + 리랭커 | +0.069 | +0.035 .. +0.110 |
| 리랭커 영어 입력 | 영어 RRF + 리랭커 | +0.239 | +0.153 .. +0.322 |
| 3중 RRF | 영어 RRF | -0.182 | -0.255 .. -0.117 |
| 용어집 | 영어 BM25 | +0.022 | -0.021 .. +0.061 |
| 어간 추출 | 영어 BM25 | +0.007 | -0.032 .. +0.048 |
| 질의 확장 HyDE | 영어 BM25 | +0.020 | -0.037 .. +0.075 |
| 질의 확장 multi | 영어 BM25 | -0.060 | -0.125 .. +0.002 |
| dense + 맥락 접두사(제목 > 절) | dense | -0.052 | -0.083 .. -0.023 |

원문 텍스트 파이프라인의 청크 크기(256 / 384 / 512, 겹침 48)와 맥락 접두사 nDCG@10:

| 방식 | 256 | 384 | 512 | 384 + 접두사 |
|---|---|---|---|---|
| BM25 kiwi | 0.324 | 0.336 | 0.335 | 0.337 |
| dense | 0.495 | 0.487 | 0.473 | 0.435 |
| RRF + 리랭커 | 0.591 | 0.586 | 0.568 | 0.565 |

리랭커 후보 수(30 / 50 / 100): 영어 RRF + 리랭커 nDCG@10 0.656 / 0.652 / 0.652. 후보 30개 안에 정답 청크가 있는 질문은 영어 RRF 90/90, 원문 RRF 73/90이고, 리랭커 후 상위 5에 정답이 남은 질문은 각각 75/90, 69/90입니다.

풀링 재채점(`experiments/results/v2_pooled.md`): 25개 설정의 상위 3개 중 gold가 아닌 청크 1,054개에 라벨을 붙여 정답 청크 97개를 45개 질문에 추가했고, 원래 gold와 풀링 gold의 시스템 순서 상관은 Kendall tau 0.973입니다. 라벨 대조군은 정답 청크 15/16개가 1 이상, 무관한 청크 16/16개가 0이었습니다.

### 생성과 평가 (평가셋 v2, 질문 90개)

프롬프트 cite_v1, 상위 5개 청크(RRF + 리랭커), greedy. 학습은 v2 정답 청크를 출처에서 제외한 데이터(학습 86개, 검증 12개)로 했고 시드 3개의 평균 ± 표준편차입니다. 학습 답변은 `sentence_coverage = 1`로 골랐습니다.

| 조건 | 문장 단위 인용률(선택 기준) | 정답 청크 인용 | 충실도 | 정확성 | 답변 관련성 |
|---|---|---|---|---|---|
| 기반 bf16 | 0.821 | 0.722 | 0.896 | 0.805 | 0.948 |
| 기반 4비트 | 0.595 | 0.711 | 0.910 | 0.769 | 0.949 |
| QLoRA (4비트 기반, 3시드) | 0.888 ± 0.007 | 0.707 ± 0.017 | 0.914 ± 0.008 | 0.780 ± 0.021 | 0.922 ± 0.012 |
| LoRA (bf16 기반, 3시드) | 0.889 ± 0.010 | 0.726 ± 0.013 | 0.927 ± 0.019 | 0.807 ± 0.012 | 0.944 ± 0.015 |
| QLoRA, 교차 언어 전용 학습(66개, 1시드) | 0.905 | 0.711 | 0.926 | 0.802 | 0.901 |
| LoRA, 교차 언어 전용 학습(66개, 1시드) | 0.884 | 0.722 | 0.924 | 0.797 | 0.962 |

학습 모델과 자기 기반 모델의 질문별 차이(시드 평균, 문서 군집 95% 구간): QLoRA - 기반 4비트는 문장 단위 인용률 +0.293(+0.232 .. +0.347), 정답 청크 인용 -0.004(-0.029 .. +0.020), 정확성 -0.000(-0.056 .. +0.049). LoRA - 기반 bf16은 문장 단위 인용률 +0.067(+0.036 .. +0.100), 정답 청크 인용 +0.004(-0.010 .. +0.023), 정확성 +0.013(-0.044 .. +0.072). 전체 표는 `experiments/results/v2_generation_analysis.md`에 있습니다.

기반 bf16 모델에 주는 검색 결과별 비교:

| 컨텍스트 출처 | 정답 청크가 컨텍스트에 있음 | 정답 청크 인용 | 충실도 | 정확성 |
|---|---|---|---|---|
| RRF + 리랭커 | 0.767 | 0.722 | 0.896 | 0.805 |
| 영어 RRF + 리랭커 | 0.833 | 0.744 | 0.881 | 0.857 |
| 영어 RRF + 리랭커(리랭커 영어 입력) | 0.989 | 0.933 | 0.955 | 0.886 |

RRF + 리랭커 대비 차이(문서 군집 95% 구간), 리랭커 영어 입력: 정답 청크가 컨텍스트에 있음 +0.222(+0.120 .. +0.320), 정답 청크 인용 +0.211(+0.125 .. +0.292), 정확성 +0.105(+0.013 .. +0.208), 충실도 +0.066(-0.022 .. +0.151).

### 서비스 성능 (실제 모델)

평가셋 v2에서 고르게 뽑은 질문 30개를 하나씩 물었습니다. 차가운 회차는 번역 캐시와 LLM 캐시가 빈 상태이고, 따뜻한 회차는 같은 질문을 캐시로 응답합니다. 단위는 ms이며 `p50 / p95`로 적었습니다. 서비스는 한 번에 요청 하나를 처리합니다. 설정은 `configs/s35_pipeline.json`(원문 검색)과 `configs/s6_pipeline_en.json`(영어 피벗 + 리랭커 영어 입력)입니다.

| 항목 | 원문 검색 (s35) | 영어 피벗 (s6) |
|---|---|---|
| 검색 (질의 번역 + 검색 + 리랭킹) | 184 / 192 | 740 / 1004 |
| 질의 번역 | - | 570 / 828 |
| 리랭킹 | 173 / 182 | 161 / 168 |
| 생성 | 2521 / 6362 | 2929 / 4888 |
| 전체 | 2703 / 6552 | 3590 / 5866 |
| 처리량 (질문/분, 차가운 회차) | 19.3 | 14.9 |
| 생성 속도 (토큰/초, p50) | 29.6 | 30.1 |
| 전체, 캐시 응답 (같은 질문 재요청) | 170 / 174 | 171 / 173 |
| 출력 검증 차단 | 4/30 | 1/30 |
| GPU 메모리 (nvidia-smi, cuda:0 / cuda:1) | 2881 / 8798 MiB | 10647 / 8942 MiB |
| 검색 모델 로드 + 인덱싱 / 생성 모델 로드 | 18.3 s / 3.0 s | 15.3 s / 3.1 s |

HTTP 동시 요청(질문은 모두 다르고 캐시 히트 없음, 서버 시작 시 번역 캐시와 LLM 캐시가 빈 상태). 대기 시간 = 클라이언트 지연 - 서버 처리 시간입니다.

| 요청 방식 | 설정 | 전체 시간 | 요청/분 | 클라이언트 지연 p50 / 최대 | 대기 p50 |
|---|---|---|---|---|---|
| 차례로 4개 | s35 | 14.0 s | 17.1 | 3.4 s / 5.9 s | 0.0 s |
| 차례로 4개 | s6 | 22.8 s | 10.5 | 4.6 s / 10.7 s | 0.0 s |
| 동시 2개 | s35 | 10.3 s | 11.7 | 6.8 s / 10.3 s | 1.7 s |
| 동시 2개 | s6 | 12.2 s | 9.8 | 8.8 s / 12.2 s | 2.7 s |
| 동시 4개 | s35 | 10.1 s | 23.7 | 5.2 s / 10.1 s | 3.4 s |
| 동시 4개 | s6 | 10.4 s | 23.0 | 6.2 s / 10.4 s | 3.9 s |
| 동시 8개 | s35 | 23.2 s | 20.7 | 15.3 s / 23.2 s | 13.1 s |
| 동시 8개 | s6 | 28.4 s | 16.9 | 16.4 s / 28.4 s | 11.2 s |

### 외부 프레임워크 비교 (평가셋 v2, 질문 90개)

LlamaIndex 0.14.25, Haystack 3.4.1, AutoRAG 0.3.27을 `comparison/`의 별도 환경(Python 3.11)에서 실행했습니다. 모든 시스템이 이 저장소의 청크 346개를 같은 청크 ID로 색인하고, 같은 질문 90개에 청크 ID 순위를 반환합니다. 임베딩은 bge-m3, 리랭커는 bge-reranker-v2-m3, 생성은 Qwen3-4B-Instruct-2507(cite_v1, 상위 5개)로 같고, 채점은 프레임워크 지표 없이 이 저장소의 지표(`ragbench.metrics`)와 같은 판정 모델(Qwen3-8B)로만 했습니다. 프레임워크 행은 번역을 쓰지 않습니다.

| 시스템 | R@5 | MRR@10 | nDCG@10 | 단일 언어 | 교차 언어 |
|---|---|---|---|---|---|
| 이 저장소: BM25 공백 | 0.313 | 0.394 | 0.328 | 0.772 | 0.106 |
| LlamaIndex: BM25 | 0.323 | 0.379 | 0.323 | 0.755 | 0.107 |
| Haystack: BM25 | 0.322 | 0.380 | 0.315 | 0.761 | 0.091 |
| AutoRAG: BM25 (ko_kiwi, 탐색 중 최고) | 0.333 | 0.400 | 0.333 | 0.791 | 0.104 |
| 이 저장소: 밀집 bge-m3 | 0.514 | 0.506 | 0.487 | 0.760 | 0.350 |
| LlamaIndex: 벡터 | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| Haystack: 밀집 | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| AutoRAG: 벡터 | 0.514 | 0.506 | 0.486 | 0.760 | 0.350 |
| 이 저장소: RRF | 0.341 | 0.433 | 0.360 | 0.825 | 0.128 |
| LlamaIndex: 하이브리드(reciprocal rerank fusion) | 0.434 | 0.471 | 0.444 | 0.811 | 0.261 |
| Haystack: 하이브리드(RRF) | 0.419 | 0.470 | 0.425 | 0.821 | 0.227 |
| AutoRAG: 하이브리드 RRF | 0.397 | 0.441 | 0.407 | 0.817 | 0.203 |
| 이 저장소: RRF + 리랭커 | 0.608 | 0.650 | 0.586 | 0.864 | 0.448 |
| LlamaIndex: 하이브리드 + 리랭커 | 0.617 | 0.654 | 0.592 | 0.863 | 0.456 |
| Haystack: 하이브리드 + 리랭커 | 0.612 | 0.659 | 0.591 | 0.860 | 0.456 |
| AutoRAG: 탐색 최고 파이프라인(밀집 후보 30개 + 리랭커) | 0.660 | 0.689 | 0.642 | 0.873 | 0.527 |
| 이 저장소: 영어 RRF + 리랭커(리랭커 영어 입력) | 0.892 | 0.933 | 0.895 | 0.903 | 0.891 |

AutoRAG 탐색(`comparison/autorag_retrieval.yaml`)은 BM25 토크나이저 3종, 하이브리드 4종(RRF, convex combination 정규화 3종), 리랭커 3종을 돌렸고, 하이브리드 단계에서 AutoRAG 자체 지표로 고른 모듈은 convex combination(mm)에 가중치 1.0이어서 밀집 결과와 같습니다. 모듈별 전체 결과와 언어쌍별 표는 `experiments/results/cmp_analysis.md`에 있습니다.

nDCG@10 쌍체 비교(A - B, 문서 군집 95% 구간): LlamaIndex 하이브리드 + 리랭커 - 이 저장소 RRF + 리랭커 +0.005(-0.001 .. +0.018), Haystack +0.004(-0.015 .. +0.027), AutoRAG 최고 파이프라인 +0.056(+0.025 .. +0.094). 이 저장소 영어 RRF + 리랭커(리랭커 영어 입력) - AutoRAG 최고 파이프라인 +0.253(+0.169 .. +0.333), - LlamaIndex +0.303(+0.214 .. +0.385), - Haystack +0.304(+0.217 .. +0.387).

각 시스템의 검색 결과 상위 5개를 같은 기반 bf16 모델에 주었을 때:

| 컨텍스트 출처 | 정답 청크가 컨텍스트에 있음 | 정답 청크 인용 | 충실도 | 정확성 | 답변 관련성 |
|---|---|---|---|---|---|
| LlamaIndex 하이브리드 + 리랭커 | 0.778 | 0.733 | 0.911 | 0.797 | 0.937 |
| Haystack 하이브리드 + 리랭커 | 0.778 | 0.733 | 0.912 | 0.812 | 0.950 |
| AutoRAG 최고 파이프라인 | 0.811 | 0.744 | 0.915 | 0.817 | 0.951 |
| 이 저장소: 영어 RRF + 리랭커 | 0.833 | 0.744 | 0.881 | 0.857 | 0.929 |
| 이 저장소: 영어 RRF + 리랭커(리랭커 영어 입력) | 0.989 | 0.933 | 0.955 | 0.886 | 0.977 |

이 저장소 영어 RRF + 리랭커(리랭커 영어 입력) - AutoRAG 최고 파이프라인(문서 군집 95% 구간): 정답 청크가 컨텍스트에 있음 +0.178(+0.077 .. +0.277), 정답 청크 인용 +0.189(+0.106 .. +0.267), 충실도 +0.049(-0.025 .. +0.127), 정확성 +0.086(+0.012 .. +0.162). AutoRAG - LlamaIndex, AutoRAG - Haystack은 네 지표 모두 구간이 0을 포함합니다(정답 청크가 컨텍스트에 있음은 하한 +0.000).

## 한계

- 평가 질문은 45개(언어쌍별 2~9개)와 90개(언어쌍별 10개)입니다. 코퍼스는 위키백과 문서만 사용했습니다.
- 사람 채점은 답변 8개, 채점자 1명입니다. 판정 모델의 결과는 근사치입니다.
- 학습 답변은 `sentence_coverage = 1`로 골랐으므로 문장 단위 인용률은 선택 기준과 같은 지표입니다. 파인튜닝은 학습 예시 66~125개, rank 16 하나이며 하이퍼파라미터를 튜닝하지 않았습니다.
- 4단계의 학습·검증 데이터 138개 중 34개가 v2 정답 청크를 출처로 썼기 때문에, 그 어댑터는 v2 평가에 쓰지 않았고 v2 기준으로 데이터를 다시 만들어 학습했습니다.
- 서비스 성능은 질문 30개, 동시 요청은 요청 방식마다 1회 측정입니다. 서버는 한 번에 요청 하나를 처리합니다.
- 영어 피벗은 같은 모델이 청크와 질의를 번역합니다. 청크 크기·맥락 접두사 실험은 원문 텍스트 파이프라인만 대상이고, 청크 크기 변형은 풀링에서 제외했습니다.
- 프레임워크 비교는 이 저장소의 청크 346개를 모든 시스템에 같게 넣은 결과이며, 각 프레임워크의 문서 로더·청커와 번역(피벗) 기능은 비교하지 않았습니다. 프레임워크 행에는 영어 피벗이 없습니다.
- LlamaIndex·Haystack는 하이브리드 + 리랭커 구성 1개씩이고 파라미터 탐색을 하지 않았습니다. AutoRAG 탐색은 검색·리랭킹 노드의 모듈 11개로 한정했고 질의 확장, 프롬프트, 생성 노드는 탐색하지 않았습니다. 생성 비교는 시스템마다 최고 구성 1개, 판정 모델 1종입니다.
- 비교표의 쌍체 구간은 수치를 본 뒤 비교 쌍을 정했고 다중 비교 보정이 없습니다. 지연은 시스템 사이에 비교하지 않았습니다(이 저장소 영어 피벗 행은 번역 포함, AutoRAG는 자체 배치 시간).

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
configs/v2/     평가셋 v2 실험 설정 (scripts/make_v2_configs.py, make_v2_ft_configs.py가 생성)
eval/pool/      풀링 후보, 라벨, 인덱스
eval/v2_draft/  평가셋 v2 초안, 검수 입력·출력
data/sft_v2*/   v2 기준 학습 데이터(일반, 교차 언어 전용), data/glossary.json 용어집
comparison/     외부 프레임워크 비교(별도 환경): prepare_data, run_frameworks, run_autorag, collect_autorag
configs/cmp/    프레임워크 검색 결과를 받는 생성 설정
outputs/        학습된 어댑터 (git 제외)
logs/           요청 로그와 캐시 (git 제외)
```

## 라이선스와 출처

- 문서: 위키백과, CC BY-SA 4.0.
- 모델: BAAI/bge-m3(MIT), BAAI/bge-reranker-v2-m3(Apache 2.0), Qwen3-4B-Instruct-2507과 Qwen3-8B(Apache 2.0).
