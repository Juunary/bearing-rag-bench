# Knowledge bundle (data/kb, 12 reviewed pages) vs RAG vs hybrid: 20 questions written by a person

Generator Qwen/Qwen3-4B-Instruct-2507, prompt cite_refuse_v1, RAG retrieval `pdfth_x13_rrf_en_dense_en_rerank_en_text.json` (top 5). Grades by one person (eval/kb/labels.json); identical answers to the same question were graded once.

## 1. Per mode

| mode | subset | n | answered | 맞음 | 부분 | 틀림 | refused | 거절 적절 | 거절 부적절 | prompt tokens, mean | seconds, mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rag | all | 20 | 8 | 2 | 4 | 2 | 12 | 4 | 8 | 2188 | 0.0 |
| rag | in-scope | 16 | 8 | 2 | 4 | 2 | 8 | 0 | 8 | 2166 | 0.0 |
| rag | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2278 | 0.0 |
| bundle | all | 20 | 14 | 14 | 0 | 0 | 6 | 4 | 2 | 10081 | 4.8 |
| bundle | in-scope | 16 | 14 | 14 | 0 | 0 | 2 | 0 | 2 | 10080 | 5.4 |
| bundle | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 10082 | 2.5 |
| hybrid | all | 20 | 15 | 9 | 4 | 2 | 5 | 4 | 1 | 8237 | 2.9 |
| hybrid | in-scope | 16 | 15 | 9 | 4 | 2 | 1 | 0 | 1 | 7206 | 3.0 |
| hybrid | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 12360 | 2.5 |
| kb_first | all | 20 | 14 | 14 | 0 | 0 | 6 | 4 | 2 | 8520 | 4.3 |
| kb_first | in-scope | 16 | 14 | 14 | 0 | 0 | 2 | 0 | 2 | 10080 | 5.4 |
| kb_first | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2278 | 0.0 |
| both | all | 20 | 16 | 13 | 2 | 1 | 4 | 4 | 0 | 12121 | 5.3 |
| both | in-scope | 16 | 16 | 13 | 2 | 1 | 0 | 0 | 0 | 12099 | 5.9 |
| both | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 12211 | 2.8 |

hybrid path: answered by RAG 8, by the bundle 12 (of which refused 5).

kb_first path: answered by RAG 4, by the bundle 16 (of which refused 2).

kb_first matching (threshold 0.55): alias 10, dense 6, none 4.

| qid | scope | matched page(s) | how | best dense page (cosine) |
|---|---|---|---|---|
| K01 | in | fit_loose_creep | alias: housing fit | fit_loose_creep (0.73) |
| K02 | in | vibration_diagnosis | dense | vibration_diagnosis (0.57) |
| K03 | in | oil_seal_leak_check | dense | oil_seal_leak_check (0.74) |
| K04 | in | grease_selection | dense | grease_selection (0.62) |
| K05 | in | relubrication | alias: 재급지 주기; 급지량 | relubrication (0.71) |
| K06 | in | preload_setting | dense | preload_setting (0.65) |
| K07 | in | preload_setting | alias: 엔드 플레이 | preload_setting (0.62) |
| K08 | in | failure_modes | dense | failure_modes (0.65) |
| K09 | in | failure_modes | alias: 박리 | failure_modes (0.59) |
| K10 | in | vibration_diagnosis | alias: vibration analysis; envelope analysis; 엔벨로프 분석; BPFO | vibration_diagnosis (0.68) |
| K11 | in | oil_analysis | alias: 페로그래피 | oil_analysis (0.58) |
| K12 | in | wheel_bearing_noise | dense | wheel_bearing_noise (0.75) |
| K13 | in | driveline_torsional_damping | alias: torsional vibration; 비틀림 진동 | driveline_torsional_damping (0.60) |
| K14 | in | failure_modes | alias: 전식 | ev_reducer_bearing (0.79) |
| K15 | in | storage_handling | alias: induction heater | storage_handling (0.60) |
| K16 | in | failure_modes | alias: false brinelling; 브리넬링 | storage_handling (0.63) |
| K17 | out | - | - | vibration_diagnosis (0.54) |
| K18 | out | - | - | driveline_torsional_damping (0.50) |
| K19 | out | - | - | preload_setting (0.50) |
| K20 | out | - | - | driveline_torsional_damping (0.48) |

## 2. Per question

| qid | scope | topic | rag | bundle | hybrid | kb_first | both |
|---|---|---|---|---|---|---|---|
| K01 | in | fit_loose_creep | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K02 | in | fit_loose_creep | 맞음 | 맞음 | 맞음 via rag | 맞음 via bundle | 맞음 |
| K03 | in | oil_seal_leak_check | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K04 | in | grease_selection | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 부분 |
| K05 | in | relubrication | 거절 (부적절) | 거절 (부적절) | 거절 (부적절) via bundle | 거절 (부적절) via bundle | 맞음 |
| K06 | in | preload_setting | 부분 | 맞음 | 부분 via rag | 맞음 via bundle | 틀림 |
| K07 | in | preload_setting | 부분 | 맞음 | 부분 via rag | 맞음 via bundle | 맞음 |
| K08 | in | failure_modes | 틀림 | 맞음 | 틀림 via rag | 맞음 via bundle | 맞음 |
| K09 | in | failure_modes | 부분 | 맞음 | 부분 via rag | 맞음 via bundle | 맞음 |
| K10 | in | vibration_diagnosis | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K11 | in | oil_analysis | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K12 | in | wheel_bearing_noise | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K13 | in | driveline_torsional_damping | 틀림 | 맞음 | 틀림 via rag | 맞음 via bundle | 부분 |
| K14 | in | ev_reducer_bearing | 거절 (부적절) | 맞음 | 맞음 via bundle | 맞음 via bundle | 맞음 |
| K15 | in | storage_handling | 부분 | 거절 (부적절) | 부분 via rag | 거절 (부적절) via bundle | 맞음 |
| K16 | in | storage_handling | 맞음 | 맞음 | 맞음 via rag | 맞음 via bundle | 맞음 |
| K17 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle | 거절 (적절) via rag | 거절 (적절) |
| K18 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle | 거절 (적절) via rag | 거절 (적절) |
| K19 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle | 거절 (적절) via rag | 거절 (적절) |
| K20 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle | 거절 (적절) via rag | 거절 (적절) |

## 3. Blind items -> modes

| item | qid | modes | grade | note |
|---|---|---|---|---|
| K01 | K18 | rag, bundle, hybrid, kb_first, both | 거절 (적절) | 주제 밖 질문(자동차 브레이크 패드)이므로 거절이 맞음 |
| K02 | K12 | rag | 거절 (부적절) | 제공된 문서(휠 베어링 소음)에 주행 테스트 구분 방법이 있음 |
| K03 | K05 | rag, bundle, hybrid, kb_first | 거절 (부적절) | 제공된 문서(재급지 주기)에 계산식과 기준이 명시되어 있음 |
| K04 | K15 | bundle, kb_first | 거절 (부적절) | 제공된 문서(베어링 보관/취급)에 가열 조립 온도와 주의사항이 있음 |
| K05 | K06 | rag, hybrid | 부분 | 과도한 예압의 부작용 등 원론적 설명은 있으나, 구체적인 확인 방법이 부족함 |
| K06 | K04 | rag | 거절 (부적절) | 제공된 문서(그리스 선정)에 150도 이상 고온용 그리스(PFPE/PTFE) 내용이 있음 |
| K07 | K06 | bundle, kb_first | 맞음 | 스페이서 폭 및 유니버설 매칭 쌍을 이용한 예압 설정법을 정확히 설명함 |
| K08 | K09 | bundle, kb_first, both | 맞음 | 과하중, 윤활 부족, 오염 입자 등 피로 박리의 초기 원인을 잘 짚음 |
| K09 | K12 | bundle, hybrid, kb_first | 맞음 | 선회 시험과 노면 변화에 따른 휠 베어링과 타이어 소음 구분법을 정확히 서술함 |
| K10 | K20 | rag, bundle, hybrid, kb_first, both | 거절 (적절) | 주제 밖 질문(디젤 DPF 재생)이므로 거절이 맞음 |
| K11 | K13 | bundle, kb_first | 맞음 | 동흡진기(튜닝 매스 댐퍼)와 고무 커플링을 정확히 지적함 |
| K12 | K03 | rag | 거절 (부적절) | 제공된 문서(오일 씰 누유 점검)에 마모 홈, 표면 거칠기 등 축 점검 사항이 있음 |
| K13 | K01 | bundle, hybrid, kb_first | 맞음 | O링 홈, 축 방향 조임(클램프), 하우징 고정핀 등 크리프 대책을 정확히 제시함 |
| K14 | K02 | bundle, kb_first | 맞음 | 수분 침투 부식 및 프레팅(미동 마모)으로 인한 산화철 가루 현상을 잘 설명함 |
| K15 | K07 | rag, hybrid | 부분 | 예압 과다로 인한 마찰 및 발열 부작용은 지적했으나, 기계 번역 톤(웨이크)이 부자연스러움 |
| K16 | K09 | rag, hybrid | 부분 | 응력 및 재질 경화 등 학술적 설명은 있으나, 실무적인 원인(유막 부족 등)이 다소 누락됨 |
| K17 | K03 | bundle, hybrid, kb_first, both | 맞음 | 립 접촉부 마모 홈(wear groove) 확인을 정확히 지적함 |
| K18 | K14 | rag | 거절 (부적절) | 제공된 문서(전기차 감속기 베어링)에 고속 회전 및 전식(EDM) 방지 요구 사항이 있음 |
| K19 | K14 | bundle, hybrid, kb_first | 맞음 | 구동 모터의 초고속 회전 및 인버터 PWM 스위칭으로 인한 방전 현상을 명확하게 서술함 |
| K20 | K15 | rag, hybrid | 부분 | 적정 온도(80~100도)는 맞으나 '스테인', '클라스' 등 원문 오역과 문맥 훼손이 있음 |
| K21 | K08 | bundle, kb_first | 맞음 | Fluting 자국을 인버터 스위칭에 의한 전식(Electrical erosion)으로 정확히 진단함 |
| K22 | K02 | rag, hybrid | 맞음 | 프레팅(Fretting)으로 인한 붉은색 산화철 가루 발생을 잘 설명함 (코카오 가루 오타 제외) |
| K23 | K11 | rag | 거절 (부적절) | 제공된 문서(오일 분석)에 띠/리본 모양의 절삭 입자(연마 마모) 내용이 있음 |
| K24 | K16 | bundle, kb_first | 맞음 | 진동이 없는 곳에 보관해야 한다는 핵심 원칙을 적절히 답변함 |
| K25 | K10 | rag | 거절 (부적절) | 제공된 문서(진동 스펙트럼)에 고주파 충격파 탐지를 위한 엔벨로프 분석 이유가 있음 |
| K26 | K19 | rag, bundle, hybrid, kb_first, both | 거절 (적절) | 주제 밖 질문(유압 펌프 캐비테이션)이므로 거절이 맞음 |
| K27 | K16 | rag, hybrid | 맞음 | 진동 최소화 및 고정을 통한 거짓 브리넬링 방지 수칙을 올바르게 설명함 |
| K28 | K07 | bundle, kb_first | 맞음 | 예압 과다로 인한 마찰 발열과 윤활 파괴, 조기 피로 위험을 정확히 서술함 |
| K29 | K04 | bundle, hybrid, kb_first | 맞음 | PFPE 기유와 PTFE 증주제 조합의 고온용 특수 그리스를 명확히 추천함 |
| K30 | K01 | rag | 거절 (부적절) | 제공된 문서(헐거운 끼워맞춤)에 크리프 방지 대책이 상세히 기재되어 있음 |
| K31 | K10 | bundle, hybrid, kb_first | 맞음 | 초기 결함 시 발생하는 고주파 충격 신호를 엔벨로프 스펙트럼으로 잡는 원리를 잘 설명함 |
| K32 | K17 | rag, bundle, hybrid, kb_first, both | 거절 (적절) | 주제 밖 질문(V벨트 장력 측정)이므로 거절이 맞음 |
| K33 | K13 | rag, hybrid | 틀림 | 비틀림 진동 저감 댐퍼를 물었으나 유니버설 조인트의 니들 롤러 베어링을 엉뚱하게 설명함 |
| K34 | K11 | bundle, hybrid, kb_first | 맞음 | 띠 모양 마모 입자를 절삭 마모(Abrasive wear)로 정확하게 진단함 |
| K35 | K08 | rag, hybrid | 틀림 | 톱니바퀴 규칙 자국(Fluting)은 전식이나 프레팅 마모로 잘못 진단함 |
| K36 | K10 | both | 맞음 | 초기 결함에 의한 고주파 충격파를 탐지하기 위한 엔벨로프 분석의 원리를 정확히 설명함 |
| K37 | K04 | both | 부분 | PFPE + PTFE 증주제 추천은 맞으나, 실리콘 기유는 본문에서 '저하중' 용으로 분류되었음에도 고하중 환경에 추천하여 일부 오류가 있음 |
| K38 | K08 | both | 맞음 | 인버터 고속 스위칭으로 인한 방전 현상(전식, Fluting)을 명확하게 연결함 |
| K39 | K02 | both | 맞음 | 진동으로 인한 프레팅 부식(미동 마모)과 붉은색 산화철 가루 발생 원리를 정확히 짚어냄 |
| K40 | K14 | both | 맞음 | 고속 회전에 따른 원심력/온도 상승과 인버터 스위칭에 따른 전식 위험을 모두 정확히 설명함 |
| K41 | K16 | both | 맞음 | 거짓 브리넬링 방지를 위해 진동이 없는 곳에 보관해야 한다는 핵심 원칙을 제대로 답변함 |
| K42 | K07 | both | 맞음 | 예압 과다로 인한 마찰 및 발열 증가, 조기 피로 등 발생할 수 있는 문제를 명확히 설명함 |
| K43 | K11 | both | 맞음 | 띠 모양 마모 입자를 절삭 마모(연마 마모)로 정확히 추정함 |
| K44 | K15 | both | 맞음 | 적정 온도 80~100도, 최대 120도 상한, 탈자(Demagnetize) 필수 등 주의사항을 정확히 서술함 |
| K45 | K12 | both | 맞음 | 선회 시 하중 이동에 따른 소음 변화(휠 베어링)와 노면 변화에 따른 소음(타이어) 구분법을 완벽히 요약함 |
| K46 | K13 | both | 부분 | 튜닝 매스 댐퍼와 고무 커플링 언급은 맞으나, 전륜구동용인 CV 조인트 댐퍼를 후륜구동 부품으로 앞세워 설명하여 섞임 현상이 있음 |
| K47 | K05 | both | 맞음 | 온도 보정 계수 및 급지량 공식(G ≈ 0.005 × D × B)을 기준에 맞게 정확히 제시함 |
| K48 | K01 | both | 맞음 | 축 방향 조임(클램프), 하우징 고정핀 등 올바른 크리프 방지 기구들을 제시함 |
| K49 | K06 | both | 틀림 | 앵귤러 콘택트 볼 베어링의 예압 방식(매칭 쌍, 스페이서) 대신 테이퍼 롤러 베어링의 조립·설정 방법(엔드플레이 측정, 토크 조임)을 엉뚱하게 설명함 |
