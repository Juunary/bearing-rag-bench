---
id: bearing_designation
type: guide
title: "베어링 호칭 번호 읽는 법"
names:
  ko: ["베어링 번호 읽기", "베어링 호칭 번호", "베어링 형번", "베어링 접미사 의미", "C3 의미", "2RS ZZ 차이"]
  en: ["bearing designation", "bearing number meaning", "bearing suffix", "bearing part number", "2RS vs ZZ"]
  de: ["Lagerbezeichnung", "Lager Kurzzeichen", "Nachsetzzeichen"]
related: ["bearing_selection_basics", "preload_setting", "storage_handling"]
verified: false
author: "AI agent draft (general engineering knowledge; standards cited by name only)"
---
# 베어링 호칭 번호 읽는 법

## 기본 번호(ISO 15 계열)
- 예: **6205-2RS C3**
  - `6` 형식: 6 = 깊은 홈 볼, 7 = 앵귤러 콘택트 볼, 1·2 = 자동 조심 볼(1)·구면 롤러(2), 3 = 테이퍼 롤러(ISO 355 계열 3xxxx), N/NU/NJ/NUP = 원통 롤러, NA/NK = 니들, 5 = 스러스트 볼.
  - `2` 치수 계열(폭·외경): 0·2·3·4 순으로 커짐(같은 내경에 외경·하중 용량 증가). 앞의 폭 기호가 생략된 것.
  - `05` 내경 기호: 04 이상은 **×5 mm**(05 = 25 mm, 06 = 30 mm, 12 = 60 mm). 00 = 10, 01 = 12, 02 = 15, 03 = 17 mm. 내경 ≥ 500 mm 또는 비표준은 `/` 뒤에 mm 직접 표기(62/22 = 내경 22 mm).
- 같은 내경의 6005·6205·6305·6405는 내경 25 mm가 공통이고 외경·폭·정격 하중이 순서대로 커집니다.

## 접미사
| 접미사 | 의미 |
|---|---|
| Z / ZZ(2Z) | 강판 실드 한쪽 / 양쪽, 비접촉, 고속·저마찰, 먼지만 막음 |
| RS / 2RS(2RSR, DDU, LLU) | 고무 접촉 씰 한쪽 / 양쪽, 수분·이물 차단, 속도 한계 낮음, 마찰 큼 |
| 2RZ, RSL, LLB | 비접촉 고무 씰(실드와 접촉 씰의 중간) |
| C2 / CN / C3 / C4 | 레이디얼 내부 틈새: 표준보다 작음 / 표준 / 큼 / 더 큼. 전동기·고온·억지 끼워맞춤은 C3 |
| P6, P5, P4 (ABEC 3·5·7) | 정밀도 등급, 숫자가 작을수록 정밀 |
| K | 테이퍼 보어(1:12), 어댑터 슬리브용 |
| E, EC | 강화형(전동체 수·크기 증가, 높은 정격) |
| TN9, TVP, M, J | 케이지 재질: 폴리아미드(TN9·TVP), 황동 기계가공(M), 강판 프레스(J) |
| DB / DF / DT | 앵귤러 조합: 배면 / 정면 / 병렬 |
| G, GA, GB | 범용 조합·경예압(앵귤러 콘택트, 제조사별 상이) |
| VV, DDU, LLU | 제조사별 양쪽 씰 표기 |

## 테이퍼 롤러 미터·인치 계열
- 미터 ISO 계열: 30205 = 형식 3, 치수 계열 02, 내경 25 mm. 접촉각이 큰 계열은 32xxx·33xxx.
- 인치 계열(예: LM11949/LM11910)은 내륜(cone)과 외륜(cup) 번호가 따로 있어 **쌍**으로 주문합니다.

## 주의
- 제조사마다 접미사 표기가 달라(2RS vs DDU vs LLU) 교차 참조표로 확인하며, 틈새·예압·케이지 기호가 빠진 대체품은 동일품이 아닙니다.
- 호칭 번호에 없는 정보(그리스 종류·충전량, 내열 안정화 S1 등)는 제조사 도면이나 접미사 뒤 추가 기호로 지정됩니다.
