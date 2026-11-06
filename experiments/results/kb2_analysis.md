# Knowledge bundle (data/kb, 24 reviewed pages) vs RAG: 20 questions written by a person (questions2.jsonl)

Generator Qwen/Qwen3-4B-Instruct-2507, prompt cite_refuse_v1, RAG retrieval `pdfth_x13_rrf_en_dense_en_rerank_en_text.json` (top 5). Grades by one person (eval/kb2/labels.json); identical answers to the same question were graded once.

## 1. Per mode

| mode | subset | n | answered | 맞음 | 부분 | 틀림 | refused | 거절 적절 | 거절 부적절 | prompt tokens, mean | seconds, mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rag | all | 20 | 7 | 5 | 1 | 1 | 13 | 5 | 8 | 2253 | 0.0 |
| rag | in-scope | 16 | 7 | 5 | 1 | 1 | 9 | 1 | 8 | 2242 | 0.0 |
| rag | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2299 | 0.0 |
| kb_first | all | 20 | 12 | 8 | 1 | 3 | 8 | 5 | 3 | 16577 | 8.5 |
| kb_first | in-scope | 16 | 12 | 8 | 1 | 3 | 4 | 1 | 3 | 20147 | 10.7 |
| kb_first | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2299 | 0.0 |
| kb_matched | all | 20 | 13 | 11 | 1 | 1 | 7 | 5 | 2 | 3449 | 4.3 |
| kb_matched | in-scope | 16 | 13 | 11 | 1 | 1 | 3 | 1 | 2 | 3737 | 5.4 |
| kb_matched | out-of-scope | 4 | 0 | 0 | 0 | 0 | 4 | 4 | 0 | 2299 | 0.0 |

kb_first path: answered by RAG 4, by the bundle 16 (of which refused 4).

kb_matched path: answered by RAG 4, by the bundle 16 (of which refused 3).

kb_first matching (threshold 0.55): alias 4, dense 12, none 4.

| qid | scope | matched page(s) | how | best dense page (cosine) |
|---|---|---|---|---|
| K50 | in | bearing_selection_basics | dense | bearing_selection_basics (0.61) |
| K51 | in | shaft_misalignment | alias: laser alignment; soft foot; 축 정렬; 소프트 풋 | shaft_misalignment (0.58) |
| K52 | in | lubrication_method_choice | alias: oil mist; 오일 미스트 | lubrication_method_choice (0.60) |
| K53 | in | vibration_diagnosis | dense | vibration_diagnosis (0.63) |
| K54 | in | bearing_designation | dense | bearing_designation (0.55) |
| K55 | out | - | - | oil_seal_leak_check (0.53) |
| K56 | in | bearing_temperature | alias: bearing temperature; 베어링 온도 | bearing_temperature (0.67) |
| K57 | in | cv_joint_boot_service | dense | cv_joint_boot_service (0.73) |
| K58 | in | wheel_hub_bearing_replacement | dense | wheel_hub_bearing_replacement (0.62) |
| K59 | out | - | - | oil_seal_leak_check (0.50) |
| K60 | in | bearing_reuse_assessment | dense | bearing_reuse_assessment (0.67) |
| K61 | in | gearbox_bearing_failure | dense | gearbox_bearing_failure (0.61) |
| K62 | in | shaft_seat_repair | dense | shaft_seat_repair (0.57) |
| K63 | out | - | - | preload_setting (0.48) |
| K64 | in | bearing_noise_diagnosis | dense | bearing_noise_diagnosis (0.61) |
| K65 | in | bearing_designation | dense | bearing_designation (0.55) |
| K66 | out | - | - | wheel_hub_bearing_replacement (0.53) |
| K67 | in | failure_modes | alias: 전식 | ev_reducer_bearing (0.63) |
| K68 | in | wheel_hub_bearing_replacement | dense | wheel_hub_bearing_replacement (0.63) |
| K69 | in | lubrication_method_choice | dense | lubrication_method_choice (0.69) |

## 2. Per question

| qid | scope | topic | rag | kb_first | kb_matched |
|---|---|---|---|---|---|
| K50 | in | bearing_selection_basics | 거절 (부적절) | 틀림 via bundle | 틀림 via bundle |
| K51 | in | shaft_misalignment | 거절 (부적절) | 틀림 via bundle | 거절 (부적절) via bundle |
| K52 | in | lubrication_method_choice | 거절 (부적절) | 맞음 via bundle | 맞음 via bundle |
| K53 | in | shaft_misalignment | 거절 (부적절) | 맞음 via bundle | 맞음 via bundle |
| K54 | in | bearing_designation | 거절 (부적절) | 부분 via bundle | 부분 via bundle |
| K55 | out | - | 거절 (적절) | 거절 (적절) via rag | 거절 (적절) via rag |
| K56 | in | bearing_temperature | 맞음 | 거절 (부적절) via bundle | 맞음 via bundle |
| K57 | in | cv_joint_boot_service | 맞음 | 맞음 via bundle | 맞음 via bundle |
| K58 | in | wheel_hub_bearing_replacement | 맞음 | 맞음 via bundle | 맞음 via bundle |
| K59 | out | - | 거절 (적절) | 거절 (적절) via rag | 거절 (적절) via rag |
| K60 | in | bearing_reuse_assessment | 거절 (부적절) | 틀림 via bundle | 맞음 via bundle |
| K61 | in | gearbox_bearing_failure | 맞음 | 거절 (부적절) via bundle | 맞음 via bundle |
| K62 | in | shaft_seat_repair | 거절 (부적절) | 맞음 via bundle | 맞음 via bundle |
| K63 | out | - | 거절 (적절) | 거절 (적절) via rag | 거절 (적절) via rag |
| K64 | in | bearing_noise_diagnosis | 틀림 | 맞음 via bundle | 맞음 via bundle |
| K65 | in | bearing_selection_basics | 맞음 | 거절 (부적절) via bundle | 거절 (부적절) via bundle |
| K66 | out | - | 거절 (적절) | 거절 (적절) via rag | 거절 (적절) via rag |
| K67 | in | electric_motor_bearing | 부분 | 맞음 via bundle | 맞음 via bundle |
| K68 | in | wheel_hub_bearing_replacement | 거절 (적절) | 거절 (적절) via bundle | 거절 (적절) via bundle |
| K69 | in | lubrication_method_choice | 거절 (부적절) | 맞음 via bundle | 맞음 via bundle |

## 3. Blind items -> modes

| item | qid | modes | grade | note |
|---|---|---|---|---|
| M01 | K64 | rag | 틀림 | 소음 원인 진단, 틀림 - 주요 원인인 윤활 부족 누락 |
| M02 | K50 | kb_matched | 틀림 | 설계 변경 적절성, 틀림 |
| M03 | K67 | rag | 부분 | 전식 방지 부가 조치, 부분 - 구체적 조치 누락 |
| M04 | K60 | kb_first | 틀림 | 베어링 재사용 여부, 틀림 |
| M05 | K57 | rag | 맞음 | 조인트 교체 범위, 맞음 |
| M06 | K68 | rag, kb_first, kb_matched | 거절 (적절) | 프레스 작업 이유, 적절 |
| M07 | K62 | kb_first | 맞음 | 축혈부 고정제 사용 조립 안전성, 맞음 |
| M08 | K67 | kb_first | 맞음 | 전식 방지 부가 조치, 맞음 |
| M09 | K54 | rag | 거절 (부적절) | 각인 기호 의미, 부적절 |
| M10 | K65 | kb_first, kb_matched | 거절 (부적절) | 정격하중 차이 및 L10 수명 적용 값, 부적절 |
| M11 | K57 | kb_first | 맞음 | 조인트 교체 범위, 맞음 |
| M12 | K67 | kb_matched | 맞음 | 전식 방지 부가 조치, 맞음 |
| M13 | K54 | kb_first | 부분 | 2RS1 의미, 틀림 - 양쪽 씰을 한쪽이라고 명시; C3 의미, 맞음 |
| M14 | K53 | rag | 거절 (부적절) | 결함 원인 진단, 부적절 |
| M15 | K69 | rag | 거절 (부적절) | 오일 수위 위치, 부적절 |
| M16 | K60 | rag | 거절 (부적절) | 베어링 재사용 여부, 부적절 |
| M17 | K56 | kb_first | 거절 (부적절) | 온도 급상승 원인 및 조치, 부적절 |
| M18 | K53 | kb_matched | 맞음 | 결함 원인 진단, 맞음 |
| M19 | K62 | kb_matched | 맞음 | 축혈부 고정제 사용 조립 안전성, 맞음 |
| M20 | K52 | kb_first | 맞음 | 유리한 윤활 방식, 맞음 |
| M21 | K64 | kb_first | 맞음 | 소음 원인 진단, 맞음 |
| M22 | K53 | kb_first | 맞음 | 결함 원인 진단, 맞음 |
| M23 | K51 | rag, kb_matched | 거절 (부적절) | 소프트 풋 측정 방법, 부적절 |
| M24 | K52 | kb_matched | 맞음 | 유리한 윤활 방식, 맞음 |
| M25 | K58 | kb_first | 맞음 | 프레스 작업 이유, 맞음 |
| M26 | K56 | rag | 맞음 | 온도 급상승 원인 및 조치, 맞음 |
| M27 | K56 | kb_matched | 맞음 | 온도 급상승 원인 및 조치, 맞음 |
| M28 | K61 | kb_matched | 맞음 | 오일 오염 원인 및 조치, 맞음 |
| M29 | K52 | rag | 거절 (부적절) | 유리한 윤활 방식, 부적절 |
| M30 | K58 | rag | 맞음 | 프레스 작업 이유, 맞음 |
| M31 | K60 | kb_matched | 맞음 | 베어링 재사용 여부, 맞음 |
| M32 | K61 | rag | 맞음 | 오일 오염 원인 및 조치, 맞음 |
| M33 | K69 | kb_first | 맞음 | 오일 수위 위치, 맞음 |
| M34 | K65 | rag | 맞음 | 정격하중 차이 및 L10 수명 적용 값, 맞음 |
| M35 | K61 | kb_first | 거절 (부적절) | 오일 오염 원인 및 조치, 부적절 |
| M36 | K51 | kb_first | 틀림 | 소프트 풋 측정 방법, 틀림 - 볼트는 한 번에 하나씩 풀며 확인해야 함 |
| M37 | K63 | rag, kb_first, kb_matched | 거절 (적절) | 팽창 행정 현상, 적절 |
| M38 | K50 | rag | 거절 (부적절) | 설계 변경 적절성, 부적절 |
| M39 | K59 | rag, kb_first, kb_matched | 거절 (적절) | 오일 오염 증상, 적절 |
| M40 | K55 | rag, kb_first, kb_matched | 거절 (적절) | 릴레이 및 퓨즈 점검 방법, 적절 |
| M41 | K50 | kb_first | 틀림 | 설계 변경 적절성 근거, 틀림 - 답변 논리에 모순이 있음 |
| M42 | K64 | kb_matched | 맞음 | 소음 원인 진단, 맞음 |
| M43 | K62 | rag | 거절 (부적절) | 축혈부 고정제 사용 조립 안전성, 부적절 |
| M44 | K58 | kb_matched | 맞음 | 프레스 작업 이유, 맞음 |
| M45 | K57 | kb_matched | 맞음 | 조인트 교체 범위, 맞음 |
| M46 | K54 | kb_matched | 부분 | 2RS1 의미, 틀림 - 양쪽 씰을 한쪽이라고 명시; C3 의미, 맞음 |
| M47 | K66 | rag, kb_first, kb_matched | 거절 (적절) | 벨트 슬립 원인, 적절 |
| M48 | K69 | kb_matched | 맞음 | 오일 수위 위치, 맞음 |
