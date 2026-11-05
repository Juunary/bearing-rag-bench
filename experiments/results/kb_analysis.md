# Knowledge bundle (data/kb, 12 reviewed pages) vs RAG vs hybrid: 20 questions written by a person

Generator Qwen/Qwen3-4B-Instruct-2507, prompt cite_refuse_v1, RAG retrieval `pdfth_x13_rrf_en_dense_en_rerank_en_text.json` (top 5). Grades by one person (eval/kb/labels.json); identical answers to the same question were graded once.

## 1. Per mode

| mode | subset | n | answered | 맞음 | 부분 | 틀림 | refused | 거절 적절 | 거절 부적절 | prompt tokens, mean | seconds, mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rag | all | 20 | 8 | 2 | 4 | 2 | 12 | 4 | 8 | 2188 | 3.4 |
| rag | in-scope | 16 | 8 | 2 | 4 | 2 | 8 | 0 | 8 | 2166 | 4.2 |
| rag | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2278 | 0.5 |
| bundle | all | 20 | 14 | 14 | 0 | 0 | 6 | 4 | 2 | 10081 | 4.8 |
| bundle | in-scope | 16 | 14 | 14 | 0 | 0 | 2 | 0 | 2 | 10080 | 5.4 |
| bundle | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 10082 | 2.5 |
| hybrid | all | 20 | 15 | 9 | 4 | 2 | 5 | 4 | 1 | 8237 | 6.3 |
| hybrid | in-scope | 16 | 15 | 9 | 4 | 2 | 1 | 0 | 1 | 7206 | 7.2 |
| hybrid | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 12360 | 3.0 |

Hybrid path: answered by RAG 8, fell back to the bundle 12 (of which refused again 5).

## 2. Per question

| qid | scope | topic | rag | bundle | hybrid |
|---|---|---|---|---|---|
| K01 | in | fit_loose_creep | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K02 | in | fit_loose_creep | 맞음 | 맞음 | 맞음 via rag |
| K03 | in | oil_seal_leak_check | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K04 | in | grease_selection | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K05 | in | relubrication | 거절 (부적절) | 거절 (부적절) | 거절 (부적절) via bundle |
| K06 | in | preload_setting | 부분 | 맞음 | 부분 via rag |
| K07 | in | preload_setting | 부분 | 맞음 | 부분 via rag |
| K08 | in | failure_modes | 틀림 | 맞음 | 틀림 via rag |
| K09 | in | failure_modes | 부분 | 맞음 | 부분 via rag |
| K10 | in | vibration_diagnosis | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K11 | in | oil_analysis | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K12 | in | wheel_bearing_noise | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K13 | in | driveline_torsional_damping | 틀림 | 맞음 | 틀림 via rag |
| K14 | in | ev_reducer_bearing | 거절 (부적절) | 맞음 | 맞음 via bundle |
| K15 | in | storage_handling | 부분 | 거절 (부적절) | 부분 via rag |
| K16 | in | storage_handling | 맞음 | 맞음 | 맞음 via rag |
| K17 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle |
| K18 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle |
| K19 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle |
| K20 | out | - | 거절 (적절) | 거절 (적절) | 거절 (적절) via bundle |

## 3. Blind items -> modes

| item | qid | modes | grade | note |
|---|---|---|---|---|
| K01 | K18 | rag, bundle, hybrid | 거절 (적절) | 주제 밖 질문(자동차 브레이크 패드)이므로 거절이 맞음 |
| K02 | K12 | rag | 거절 (부적절) | 제공된 문서(휠 베어링 소음)에 주행 테스트 구분 방법이 있음 |
| K03 | K05 | rag, bundle, hybrid | 거절 (부적절) | 제공된 문서(재급지 주기)에 계산식과 기준이 명시되어 있음 |
| K04 | K15 | bundle | 거절 (부적절) | 제공된 문서(베어링 보관/취급)에 가열 조립 온도와 주의사항이 있음 |
| K05 | K06 | rag, hybrid | 부분 | 과도한 예압의 부작용 등 원론적 설명은 있으나, 구체적인 확인 방법이 부족함 |
| K06 | K04 | rag | 거절 (부적절) | 제공된 문서(그리스 선정)에 150도 이상 고온용 그리스(PFPE/PTFE) 내용이 있음 |
| K07 | K06 | bundle | 맞음 | 스페이서 폭 및 유니버설 매칭 쌍을 이용한 예압 설정법을 정확히 설명함 |
| K08 | K09 | bundle | 맞음 | 과하중, 윤활 부족, 오염 입자 등 피로 박리의 초기 원인을 잘 짚음 |
| K09 | K12 | bundle, hybrid | 맞음 | 선회 시험과 노면 변화에 따른 휠 베어링과 타이어 소음 구분법을 정확히 서술함 |
| K10 | K20 | rag, bundle, hybrid | 거절 (적절) | 주제 밖 질문(디젤 DPF 재생)이므로 거절이 맞음 |
| K11 | K13 | bundle | 맞음 | 동흡진기(튜닝 매스 댐퍼)와 고무 커플링을 정확히 지적함 |
| K12 | K03 | rag | 거절 (부적절) | 제공된 문서(오일 씰 누유 점검)에 마모 홈, 표면 거칠기 등 축 점검 사항이 있음 |
| K13 | K01 | bundle, hybrid | 맞음 | O링 홈, 축 방향 조임(클램프), 하우징 고정핀 등 크리프 대책을 정확히 제시함 |
| K14 | K02 | bundle | 맞음 | 수분 침투 부식 및 프레팅(미동 마모)으로 인한 산화철 가루 현상을 잘 설명함 |
| K15 | K07 | rag, hybrid | 부분 | 예압 과다로 인한 마찰 및 발열 부작용은 지적했으나, 기계 번역 톤(웨이크)이 부자연스러움 |
| K16 | K09 | rag, hybrid | 부분 | 응력 및 재질 경화 등 학술적 설명은 있으나, 실무적인 원인(유막 부족 등)이 다소 누락됨 |
| K17 | K03 | bundle, hybrid | 맞음 | 립 접촉부 마모 홈(wear groove) 확인을 정확히 지적함 |
| K18 | K14 | rag | 거절 (부적절) | 제공된 문서(전기차 감속기 베어링)에 고속 회전 및 전식(EDM) 방지 요구 사항이 있음 |
| K19 | K14 | bundle, hybrid | 맞음 | 구동 모터의 초고속 회전 및 인버터 PWM 스위칭으로 인한 방전 현상을 명확하게 서술함 |
| K20 | K15 | rag, hybrid | 부분 | 적정 온도(80~100도)는 맞으나 '스테인', '클라스' 등 원문 오역과 문맥 훼손이 있음 |
| K21 | K08 | bundle | 맞음 | Fluting 자국을 인버터 스위칭에 의한 전식(Electrical erosion)으로 정확히 진단함 |
| K22 | K02 | rag, hybrid | 맞음 | 프레팅(Fretting)으로 인한 붉은색 산화철 가루 발생을 잘 설명함 (코카오 가루 오타 제외) |
| K23 | K11 | rag | 거절 (부적절) | 제공된 문서(오일 분석)에 띠/리본 모양의 절삭 입자(연마 마모) 내용이 있음 |
| K24 | K16 | bundle | 맞음 | 진동이 없는 곳에 보관해야 한다는 핵심 원칙을 적절히 답변함 |
| K25 | K10 | rag | 거절 (부적절) | 제공된 문서(진동 스펙트럼)에 고주파 충격파 탐지를 위한 엔벨로프 분석 이유가 있음 |
| K26 | K19 | rag, bundle, hybrid | 거절 (적절) | 주제 밖 질문(유압 펌프 캐비테이션)이므로 거절이 맞음 |
| K27 | K16 | rag, hybrid | 맞음 | 진동 최소화 및 고정을 통한 거짓 브리넬링 방지 수칙을 올바르게 설명함 |
| K28 | K07 | bundle | 맞음 | 예압 과다로 인한 마찰 발열과 윤활 파괴, 조기 피로 위험을 정확히 서술함 |
| K29 | K04 | bundle, hybrid | 맞음 | PFPE 기유와 PTFE 증주제 조합의 고온용 특수 그리스를 명확히 추천함 |
| K30 | K01 | rag | 거절 (부적절) | 제공된 문서(헐거운 끼워맞춤)에 크리프 방지 대책이 상세히 기재되어 있음 |
| K31 | K10 | bundle, hybrid | 맞음 | 초기 결함 시 발생하는 고주파 충격 신호를 엔벨로프 스펙트럼으로 잡는 원리를 잘 설명함 |
| K32 | K17 | rag, bundle, hybrid | 거절 (적절) | 주제 밖 질문(V벨트 장력 측정)이므로 거절이 맞음 |
| K33 | K13 | rag, hybrid | 틀림 | 비틀림 진동 저감 댐퍼를 물었으나 유니버설 조인트의 니들 롤러 베어링을 엉뚱하게 설명함 |
| K34 | K11 | bundle, hybrid | 맞음 | 띠 모양 마모 입자를 절삭 마모(Abrasive wear)로 정확하게 진단함 |
| K35 | K08 | rag, hybrid | 틀림 | 톱니바퀴 규칙 자국(Fluting)은 전식이나 프레팅 마모로 잘못 진단함 |
