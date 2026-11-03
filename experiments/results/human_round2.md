# Human review, round 2

## A. Question review

| eval set | n | evidence | wording | realism |
|---|---|---|---|---|
| v2 | 11 | 충분 11 | 자연 11 | 낮음 1, 높음 9, 보통 1 |
| pdf | 12 | 충분 12 | 자연 12 | 낮음 1, 높음 9, 보통 2 |
| all | 23 | 충분 23 | 자연 23 | 낮음 2, 높음 18, 보통 3 |

Notes:
- A02 (q056): 실무보다는 역사적 사실을 묻는 퀴즈에 가깝습니다.
- A05 (q005): 번역투 느낌이 있으나 직역 형태라 자연스러운 범주로 볼 수 있습니다.
- A06 (q030): 설명문 일부를 발췌해 묻는 스무고개/퀴즈 형태에 가깝습니다.
- A08 (q072): 설계 기초 지식 확인용으로 적합합니다.
- A14 (pdf009): 특정 규격 번호를 묻는 질문으로 실무 활용도는 높으나 단편적입니다.
- A17 (pdf017): 비용 절감(Rework)과 관련된 현실적인 실무 질문입니다.
- A20 (pdf010): 문서 내 특정 그림 번호(Figure 27)와 출처를 묻는 형태로 독해 테스트에 가깝습니다.

## B. Answer grading: correctness

Human grades: {'맞음': 18, '부분': 4, '틀림': 5}. Pool (distinct answers) by judge stratum: {'disagree': 14, 'both_yes': 155, 'both_no': 4}; sampled: {'both_yes': 12, 'disagree': 11, 'both_no': 4}.

| judge | partial as | n | agree | agreement | kappa | reweighted agreement | human YES (reweighted) | judge YES (reweighted) |
|---|---|---|---|---|---|---|---|---|
| Qwen3-8B | NO | 27 | 14 | 0.519 | 0.05 | 0.707 | 0.733 | 0.903 |
| Qwen3-8B | excluded | 23 | 13 | 0.565 | 0.19 | 0.837 | 0.877 | 0.893 |
| Granite | NO | 27 | 17 | 0.630 | 0.06 | 0.729 | 0.733 | 0.970 |
| Granite | excluded | 23 | 16 | 0.696 | 0.04 | 0.864 | 0.877 | 0.972 |

Stratified bootstrap (partial as NO, 10000 draws): human YES (reweighted) 95% CI 0.502 .. 0.949; Qwen3-8B YES - human YES -0.041 .. +0.403; Granite YES - human YES +0.021 .. +0.467.

By stratum (partial as NO):

| stratum | n | human YES | Qwen3-8B agrees | Granite agrees |
|---|---|---|---|---|
| disagree | 11 | 6 | 4 | 7 |
| both_yes | 12 | 9 | 9 | 9 |
| both_no | 4 | 3 | 1 | 1 |

## B. Faithfulness and answer relevance

| dimension | judge | n | agree | kappa |
|---|---|---|---|---|
| faithfulness | Qwen3-8B | 10 | 8 | 0.55 |
| faithfulness | Granite | 10 | 6 | 0.00 |
| answer_relevance | Qwen3-8B | 27 | 27 | nan |
| answer_relevance | Granite | 27 | 27 | nan |

## B. Items

| item | qid | stratum | conditions | human | Qwen3-8B | Granite | faithfulness human / Qwen / Granite |
|---|---|---|---|---|---|---|---|
| B01 | q067 | both_yes | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li, v2g_ret_b_rrf_en_rerank | 맞음 | YES | YES |  |
| B02 | q003 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 부분 | NO | YES |  |
| B03 | q057 | both_yes | v2g_lora_s42 | 맞음 | YES | YES | 예 / YES / YES |
| B04 | q019 | both_yes | v2g_qlora_s42 | 맞음 | YES | YES |  |
| B05 | q023 | disagree | v2g_cmp_ar, v2g_ret_x2_rerank_en_text | 맞음 | NO | YES |  |
| B06 | pdf009 | disagree | pdfg_x13_rrf_en_dense_en_rerank_en_text | 부분 | YES | NO |  |
| B07 | q070 | disagree | v2g_base_4bit | 맞음 | NO | YES | 예 / YES / YES |
| B08 | pdf016 | both_no | pdfg_b_rrf_rerank | 틀림 | NO | NO | 아니오 / NO / YES |
| B09 | q054 | both_yes | v2g_base_bf16, v2g_cmp_ar, v2g_cmp_hs, v2g_cmp_li, v2g_ret_b_rrf_en_rerank | 맞음 | YES | YES | 예 / YES / YES |
| B10 | q069 | both_yes | v2g_cmp_ar | 맞음 | YES | YES |  |
| B11 | q069 | both_yes | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 맞음 | YES | YES |  |
| B12 | q003 | disagree | v2g_lora_s42 | 맞음 | NO | YES | 예 / YES / YES |
| B13 | q005 | disagree | v2g_lora_s42 | 틀림 | NO | YES | 아니오 / YES / YES |
| B14 | q005 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 틀림 | NO | YES | 아니오 / NO / YES |
| B15 | q019 | both_yes | v2g_ret_x2_rerank_en_text | 맞음 | YES | YES |  |
| B16 | q005 | disagree | v2g_qlora_s42 | 틀림 | NO | YES | 아니오 / YES / YES |
| B17 | pdf007 | both_yes | pdfg_b_rrf_rerank | 틀림 | YES | YES |  |
| B18 | q070 | both_no | v2g_qlora_s42 | 맞음 | NO | NO |  |
| B19 | q069 | both_yes | v2g_qlora_s42 | 부분 | YES | YES |  |
| B20 | q003 | disagree | v2g_cmp_ar | 맞음 | NO | YES |  |
| B21 | q057 | both_no | v2g_cmp_ar | 맞음 | NO | NO |  |
| B22 | q060 | disagree | v2g_base_4bit | 맞음 | NO | YES | 예 / YES / YES |
| B23 | q070 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 맞음 | NO | YES |  |
| B24 | q059 | both_yes | v2g_ret_x2_rerank_en_text | 부분 | YES | YES |  |
| B25 | q057 | both_no | v2g_ret_x2_rerank_en_text | 맞음 | NO | NO | 예 / YES / YES |
| B26 | pdf023 | both_yes | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | 맞음 | YES | YES |  |
| B27 | q055 | both_yes | v2g_ret_x2_rerank_en_text | 맞음 | YES | YES |  |

## D. The grader's own questions

Answered 5: 맞음 4, 부분 1. Refused 5: 부적절 2, 적절 3.

| qid | outcome | human | related chunks (in top 5 / in candidates) | note |
|---|---|---|---|---|
| D01 | answered | 맞음 |  | 앵귤러 콘택트 베어링의 고속 회전 및 복합 하중(축/반경) 지지 특성을 실무 지식에 맞게 잘 설명했습니다. |
| D02 | refused | 적절 |  | 비틀림 진동을 잡기 위한 댐퍼나 듀얼 매스 플라이휠 등의 장치는 기계/자동차 NVH 전문 영역이라 일반적인 구동축 개요 문서에는 없을 수 있습니다. |
| D03 | answered | 부분 |  | 고체 윤활제(그래파이트 등)를 언급한 부분은 맞지만, EP(극압) 그리스는 고하중/충격용이지 그 자체로 200도 이상의 고온 내성을 의미하지는 않으므로 설명이 부정확합니다(고온용은 우레아계, 불소계 등을 사용). |
| D04 | answered | 맞음 |  | 윤활유 내 철분 분석(Ferrography) 및 입자 분석은 대표적인 엔진 베어링 비분해 상태 진단법입니다. |
| D05 | refused | 부적절 | de_wellendichtring#0 (no / no); luh-diss-pelzer-2022#19 (no / no); luh-diss-pelzer-2022#28 (no / no); luh-diss-pelzer-2022#40 (no / no); luh-diss-pelzer-2022#43 (no / no) | 오일 씰(Radial shaft seal)의 누유 원인으로 샤프트 표면의 조도, 스크래치, 런아웃, 마모 궤적(Wear track) 등은 씰링 메커니즘을 다루는 문서나 학위논문에 반드시 등장하는 기초 지식입니다. |
| D06 | answered | 맞음 |  |  |
| D07 | answered | 맞음 |  | 구름 베어링의 점/선 접촉으로 인한 브리넬링 취약성과 플레인 베어링의 면 접촉 하중 분산 특성을 정확히 짚었습니다. |
| D08 | refused | 적절 |  | 전기차 감속기의 초고속 회전 대응 및 전식(Electrical erosion) 방지 기술은 최신 실무/연구 트렌드이므로, 고전적인 베어링 문헌이나 일반 문서에서는 찾기 어렵습니다. |
| D09 | refused | 적절 |  | 코너링 시 하중 이동에 따른 소음 변화 확인 등은 정비소 현장의 실무 노하우에 가까워 학술 논문이나 백과사전에서 다루기 어렵습니다. |
| D10 | refused | 부적절 | en_ball_bearing#15 (yes / yes) | 하우징 공차가 헐거울 때 발생하는 외륜의 헛돔(크리프, Creep 현상)과 프레팅 마모는 베어링 끼워맞춤 및 고장 원인을 다루는 기초 문헌에 필수적으로 언급되는 내용입니다. |
