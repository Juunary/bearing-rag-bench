---
id: electric_motor_bearing
type: guide
title: "전동기(모터) 베어링의 선정·윤활·고장"
names:
  ko: ["전동기 베어링", "모터 베어링 교체", "모터 베어링 윤활", "인버터 구동 모터 베어링", "모터 베어링 고장"]
  en: ["electric motor bearing", "motor bearing replacement", "motor bearing lubrication", "VFD motor bearing", "inverter-driven motor bearing"]
  de: ["Motorlager", "Elektromotor Lager", "Umrichterbetrieb Lagerströme"]
related: ["ev_reducer_bearing", "bearing_temperature", "relubrication", "failure_modes"]
verified: false
author: "AI agent draft (general engineering knowledge; standards cited by name only)"
---
# 전동기(모터) 베어링의 선정·윤활·고장

## 일반 구성
- 소형~중형 유도전동기는 양쪽에 **깊은 홈 볼 베어링**(구동측 DE가 조금 큼), 벨트 구동처럼 레이디얼 하중이 큰 경우 구동측에 원통 롤러 베어링을 씁니다.
- 내부 틈새는 권선 열로 내륜이 외륜보다 뜨거워지므로 **C3**가 표준입니다. 틈새 CN을 쓰면 운전 중 틈새가 없어져 과열합니다.
- 한쪽(보통 비구동측)은 스프링 와셔(웨이브 와셔)로 예압을 주어 축 방향 덜걱거림·소음을 없애고, 다른 쪽에서 열팽창을 흡수합니다.

## 윤활
- 프레임 160 이하 소형은 밀봉 베어링(2RS·ZZ)으로 수명 윤활, 그 이상은 그리스 니플과 배출구(릴리프)가 있어 재급지합니다.
- 전동기용 그리스는 **폴리우레아** 또는 리튬 콤플렉스 기반, 기유 점도 ISO VG 100 전후가 일반적입니다. 서로 다른 증주제의 그리스를 섞으면 연화·분리되므로 종류를 바꿀 때는 세척합니다.
- 재급지량은 제조사 표(베어링 외경·폭 기준) 또는 G = 0.005 × D × B(g, D·B는 mm)로 계산하고, 운전 중에 배출구를 열고 주입합니다.

## 인버터(VFD) 구동 시 축전류
- PWM 전압의 공통 모드 성분이 축에 전압을 유도해 윤활막을 뚫고 방전(EDM)하면 궤도에 **플루팅**(빨래판 무늬)과 회색 무광 흔적이 생기고, 수개월 내 소음·진동이 급증합니다.
- 대책: 축 접지 브러시·접지 링, 비구동측 **절연 베어링**(세라믹 코팅 또는 하이브리드) + 구동측 접지, 공통 모드 필터, 케이블 차폐·접지 개선. 한쪽만 절연하면 순환 전류는 막지만 접지 전류는 남으므로 접지 수단과 조합합니다.

## 흔한 고장 원인(발생 빈도 순)
1. 윤활 불량(과충전·부족·오염·그리스 혼합).
2. 벨트 과장력 또는 정렬 불량으로 인한 과하중.
3. 축전류(플루팅).
4. 조립 손상(타격 압입)과 진동 수송 중 거짓 브리넬링.
5. 수분·오염 침입(옥외·세척 공정).
