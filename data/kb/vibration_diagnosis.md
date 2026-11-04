---
id: vibration_diagnosis
type: guide
title: "진동 스펙트럼으로 베어링 결함 찾기"
names:
  ko: ["진동 진단", "베어링 결함 주파수", "엔벨로프 분석", "BPFO", "BPFI"]
  en: ["vibration analysis", "bearing defect frequencies", "envelope analysis", "ball pass frequency"]
  de: ["Schwingungsdiagnose", "Wälzlagerdiagnose"]
related: ["failure_modes", "wheel_bearing_noise"]
verified: false
author: "AI agent draft (general engineering knowledge; standards cited by name only)"
---
# 진동 스펙트럼으로 베어링 결함 찾기

## 결함 주파수
축 회전 주파수 f_r(Hz = rpm/60), 전동체 수 n, 전동체 지름 d, 피치 지름 D, 접촉각 α일 때(외륜 고정 기준):
- **BPFO**(외륜 결함) = n/2 · f_r · (1 − d/D · cos α)
- **BPFI**(내륜 결함) = n/2 · f_r · (1 + d/D · cos α)
- **BSF**(전동체 결함, 전동체 자전) = D/(2d) · f_r · (1 − (d/D · cos α)²)
- **FTF**(케이지, 전동체 공전) = f_r/2 · (1 − d/D · cos α)
- 치수를 모를 때의 근사: BPFO ≈ 0.4 n f_r, BPFI ≈ 0.6 n f_r. 제조사 계산기나 베어링 번호 데이터베이스로 정확히 구합니다.

## 해석 규칙
- **내륜 결함**은 하중 영역을 드나들며 신호가 변조되어 BPFI 양옆에 f_r 간격의 측대파(sideband)가 생깁니다. **전동체 결함**은 BSF 양옆에 FTF 측대파.
- 초기 손상은 가속도 영역의 고주파 충격으로 나타나므로 **엔벨로프(복조) 스펙트럼**이나 충격 펄스·피크값 지표로 먼저 보이고, 속도 스펙트럼에는 뒤늦게 나타납니다.
- 손상이 진행하면 조화파가 늘고, 말기에는 결함 주파수가 광대역 잡음에 묻히며 전체 진동 레벨이 오릅니다.
- 결함 주파수가 회전 주파수의 **정수배가 아닌 것**이 베어링 결함의 특징입니다. 정수배 성분(1×, 2×)은 불평형·정렬 불량·헐거움, 기어 맞물림 주파수는 기어.

## 측정 요령
- 베어링 하우징 하중 방향(보통 수직·수평 반경 방향)에 센서를 단단히 고정(자석보다 스터드 고정), 샘플링은 관심 주파수의 2.56배 이상, 분해능은 측대파를 가를 수 있게.
- 추세(trend)가 절대값보다 중요합니다. 동일 조건에서 주기적으로 측정해 비교합니다.

## 다른 원인과 구분
- 전식 플루팅: 결함 주파수 부근에 수많은 고조파가 빗살처럼 나타남.
- 윤활 부족: 특정 주파수 없이 고주파 영역이 전반적으로 상승.
- 헐거움: 1× 조화파 다수, 때로 0.5× 분수 조화파.
