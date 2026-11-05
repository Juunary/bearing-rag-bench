# Direct corpus interaction: a grep/read agent on the 20 questions the serving pipeline refused

Generator Qwen/Qwen3-4B-Instruct-2507 (greedy), tool budget 8 calls. v1: regex grep, terse prompt; v2: all-terms grep (every term must occur, any order) and a prompt asking for one or two key terms per search.

## 1. Outcomes

| variant | set | n | answered | calls, mean | tokens, mean | seconds, mean | malformed outputs | gold read / cited (PDF) |
|---|---|---|---|---|---|---|---|---|
| v1 | D | 5 | 0 | 8.0 | 4292 | 9 | 0 | - |
| v1 | K | 12 | 2 | 7.0 | 4882 | 9 | 5 | - |
| v1 | PDF | 3 | 1 | 6.3 | 8587 | 9 | 2 | 0 / 0 |
| v2 | D | 5 | 2 | 6.0 | 7729 | 13 | 3 | - |
| v2 | K | 12 | 5 | 6.4 | 7780 | 12 | 5 | - |
| v2 | PDF | 3 | 1 | 5.7 | 8034 | 10 | 2 | 0 / 0 |

## 2. v2 answers: human grade, and the knowledge bundle's grade on the same K questions

| qid | set | scope | DCI v2 | DCI grade | bundle grade | chunks read |
|---|---|---|---|---|---|---|
| D02 | D | in | answered | 틀림 | - | en_cv_joint#0 |
| D05 | D | in | blocked (invalid_citation) | - | - | en_radial_shaft_seal#0 |
| D08 | D | in | blocked (invalid_citation) | - | - | - |
| D09 | D | in | blocked (invalid_citation) | - | - | - |
| D10 | D | in | answered | 맞음 | - | de_waelzlager#30 |
| K01 | K | in | blocked (invalid_citation) | - | 맞음 | de_materialermuedung#1, en_plain_bearing#6, de_schmierfett#0 |
| K03 | K | in | answered | 틀림 | 맞음 | luh-diss-pelzer-2022#13 |
| K04 | K | in | answered | 부분 | 맞음 | de_schmierfett#15 |
| K05 | K | in | blocked (refusal_text) | - | 거절 (부적절) | de_waelzlager#7 |
| K10 | K | in | answered | 부분 | 맞음 | luh-diss-stuhler-2024#49, luh-diss-stuhler-2024#57 |
| K11 | K | in | blocked (invalid_citation) | - | 맞음 | - |
| K12 | K | in | answered | 부분 | 맞음 | en_fretting#2, de_waelzlager#0 |
| K14 | K | in | answered | 부분 | 맞음 | en_bearing_mechanical#12, luh-diss-stuhler-2024#46, luh-diss-stuhler-2024#67 |
| K17 | K | out | blocked (refusal_text) | - | 거절 (적절) | luh-diss-pelzer-2022#91 |
| K18 | K | out | blocked (invalid_citation) | - | 거절 (적절) | - |
| K19 | K | out | blocked (invalid_citation) | - | 거절 (적절) | - |
| K20 | K | out | blocked (invalid_citation) | - | 거절 (적절) | - |

Notes from the grader:

- V201 (K03): 틀림 — 누유 메커니즘을 엉뚱하게 추론했으며 립 마모 홈(Wear groove) 등 핵심 점검 사항을 전혀 제시하지 못함
- V202 (K04): 부분 — 고온/EP 그리스가 필요하다는 원론적인 답변은 했으나, 150도 이상 극고온 환경에 적합한 PFPE/PTFE 등 구체적인 증주제 종류를 특정하지 못함
- V203 (K10): 부분 — 노이즈 환경에서 진동 신호의 진폭 변화(고주파 충격파)를 탐지한다는 원리 설명은 맞으나, 결함이 '진동 신호의 허브에서 발생한다'는 어색한 기계 번역 투가 있음
- V204 (D02): 틀림 — CV 조인트는 각도 변화 시 속도 변동을 없애는 것이지, 비틀림 진동(Torsional vibration) 댐핑 부품(튜닝 매스 댐퍼, 듀얼 매스 플라이휠 등)이 아님
- V205 (K14): 부분 — PWM 신호로 인한 베어링 전류(전식) 위험은 잘 설명했으나, 구동 모터 자체의 초고속 회전(최대 20,000rpm 이상) 조건에 대한 서술이 누락됨
- V206 (K12): 부분 — 주행 속도 조절에 따른 소음 변화 관찰을 지적한 점은 맞으나, 선회(하중 이동) 테스트나 타이어-노면 소음 구분 테스트 등 실무적인 핵심 구분법이 빠짐
- V207 (D10): 맞음 — 헐거운 공차로 인해 외륜 고정이 안 되어(크리프 발생) 진동이 증가하고 마모/수명 감소로 이어지는 인과관계를 정확히 서술함

## 3. Search patterns on D05 (oil seal leakage)

- v1: `oil seal.*lip wear.*shaft`; `oil seal.*leak.*shaft.*defect`; `oil seal.*leak.*shaft.*failure`; `oil seal.*seal.*shaft.*damage`; `oil seal.*leak.*shaft.*condition`; `oil seal.*leak.*shaft.*defect`; `oil seal.*leak.*shaft.*wear`; `oil seal.*leak.*shaft.*misalignment` -> read nothing, blocked (invalid_citation)
- v2: `oil seal lip wear`; `shaft surface wear`; `shaft surface wear` -> read ['en_radial_shaft_seal#0'], blocked (invalid_citation)
