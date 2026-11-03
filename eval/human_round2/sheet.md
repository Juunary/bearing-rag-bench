# 사람 검수 2차

조건과 판정 모델 결과는 넣지 않았습니다. 같은 질문이 여러 번 나오면 답변이 서로 다른 것입니다.

## 답 형식 (한 항목에 한 줄)

```
A01 | 근거: 충분 | 표현: 자연 | 현실성: 높음 | 메모: (선택)
B01 | 정확성: 맞음 | 관련성: 예
B03 | 정확성: 부분 | 관련성: 예 | 충실도: 아니오      <- (충실도 포함) 항목만
D01 | (직접 쓴 질문)
```

- A 근거: `충분` = 정답 문장만으로 질문에 답할 수 있음 / `부족` = 정답 문장에 답이 일부만 있음 / `불일치` = 정답 문장이 질문과 맞지 않음
- A 표현: `복사` = 질문이 정답 문장 표현을 거의 그대로 옮김(번역 포함) / `자연` = 그렇지 않음
- A 현실성: `높음` / `보통` / `낮음` = 실제 업무에서 사람이 할 법한 질문인가
- B 정확성: `맞음` = 질문이 묻는 사실이 기준 문장과 일치 / `부분` = 일부만 맞거나 틀린 내용이 섞임 / `틀림`
- B 관련성: `예` = 질문이 묻는 것을 다루려고 함(맞는지는 따지지 않음) / `아니오`
- B 충실도: `예` = 답변의 모든 사실 진술이 아래 인용 청크에 있음 / `아니오` = 청크에 없는 내용이 있음
- D: 문서를 보지 않고, 실제 업무에서 물을 법한 베어링·자동차 부품 질문 10개(한국어 또는 영어). 정답 표시는 다음 차례에 합니다.

## A. 질문 검수

**A01** 질문: 볼 베어링에 케이지를 달지 않으면 어떤 일이 생기나요?

정답 문장:
- (핵심) 케이지가 없으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다.
- (보조) Without the cage, the balls would eventually drift out of position during operation, causing the bearing to fail.

**A02** 질문: 사용 가능한 최초의 케이지형 롤러 베어링을 만든 사람은 어떤 직업이었고, 언제 발명했나요?

정답 문장:
- (핵심) 최초의 실용적인 갇힌 롤러 베어링은 1740년대 중반에 시계학자 존 해리슨이 발명하였다.
- (보조) The first practical caged-roller bearing was invented in the mid-1740s by horologist John Harrison for his H3 marine timekeeper.

**A03** 질문: 고속 회전용 볼 베어링에 세라믹 볼을 쓰는 이유 중 하나인 밀도는 강철과 비교해 어느 정도인가요?

정답 문장:
- (핵심) 질화 규소와 같은 세라믹은 낮은 밀도(강철의 40%) 때문에 이러한 응용 분야에서 정기적으로 사용된다.
- (보조) Ceramics such as silicon nitride are now regularly used in such applications due to their low density (40% of steel).

**A04** 질문: 오일 씰에 쓰는 고무 compound의 경도는 보통 쇼어 A로 몇 정도인가요?

정답 문장:
- (핵심) In order to resist wear, the compounds' durometer (hardness) is typically 70 to 85 Shore A (medium-hard, between that of an automobile tire and a leather belt).

**A05** 질문: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요?

정답 문장:
- (핵심) There are three usual limits to the lifetime or load capacity of a bearing: abrasion, fatigue and pressure-induced welding.
- (보조) Although there are many other apparent causes of bearing failure, most can be reduced to these three.

**A06** 질문: Which bearing type avoids metal contact through a fluid film and runs quietly for long, but struggles at low temperature and stops turning if the oil leaks out?

정답 문장:
- (핵심) 유체베어링(fluid bearing) - 금속간에 유체가 존재하여 금속간 마찰이 없어 소음이 적고 수명이 길지만 저온에서 정상작동을 보장하기 힘들고, 기름이 유출되면 더 이상 회전이 불가능하고, 중력 현상으로 인한 금속마찰이 있을 수 있다.

**A07** 질문: What is the advantage of a sleeve bearing over a ball bearing in case fans, and what happens to its life at high rotation speed?

정답 문장:
- (핵심) 슬리브베어링 (sleeve bearing) - 볼베어링 방식에 비해 낮은 소음이 장점이나, 비교적 낮은 내구성(내열성 및 수명)이 단점이다.
- (보조) 높은 회전속도에서는 고발열로 인해 수명이 급격하게 단축되므로 높은 회전 속도와 내구성을 요구하지 않는 케이스 팬으로 채용된다.

**A08** 질문: What is the term for the stress range a structure can withstand regardless of the number of load cycles?

정답 문장:
- (핵심) 하중 반복횟수와 관계없이 구조물이 견딜 수 있는 응력 범위가 일정한 값을 갖는 응력 범위를 피로한도(fatigue limit)라고 한다.
- (핵심) called a fatigue limit or endurance limit.
- (보조) For some materials, like steel and titanium, there is a theoretical value for stress amplitude below which the material will not fail for any number of cycles, called a fatigue limit or endurance limit.

**A09** 질문: Which constant-velocity joint improves on the Rzeppa six-ball cage design by confining the balls to elliptical tracks?

정답 문장:
- (핵심) The Birfield joint is a type of constant-velocity joint based on the Rzeppa joint but confines the travel of the six balls using elliptical tracks.

**A10** 질문: Where are plain bushings favored over roller bearings to avoid dents from impact loads?

정답 문장:
- (핵심) Babbitt bearings or bronze bushings are often used instead of roller bearings in applications where such loads exist, such as in automotive crankshafts or pulley sheaves, to decrease the possibility of brinelling by distributing the force over a very large surface area.

**A11** 질문: What does it mean when a grease is called shear-thinning?

정답 문장:
- (핵심) Greases are usually shear-thinning or pseudo-plastic fluids, which means that the viscosity of the fluid is reduced under shear stress.
- (보조) A common feature of greases is that they possess high initial viscosities which, upon the application of shear, drop to give the effect of an oil-lubricated bearing of approximately the same viscosity as the base oil used in the grease.
- (보조) This change in viscosity is called shear thinning.

**A12** 질문: 상용 터보프롭 기어박스의 현장 수명 데이터와 비교하면, Lundberg-Palmgren 방식은 기어박스의 L10 수명을 몇 배나 낮게 예측했나요?

정답 문장:
- (핵심) The field data suggest that the L10 life of the gearbox was under predicted by a factor of 7.56 (Ref. 22).
- (핵심) The field data suggest that the L10 life of the gearbox was underpredicted by a factor of 7.56 (Ref. 94).
- (참고 답) 약 7.56배 과소 예측했습니다(현장 L10 5627 h, 예측 774 h).

**A13** 질문: 피로한도를 두지 않는 Lundberg-Palmgren 모델에서 최대 헤르츠 응력을 1379 MPa에서 2068 MPa로 올리면 상대 수명은 얼마로 줄어드나요?

정답 문장:
- (핵심) | 0 (0), Lundberg-Palmgren (Ref. 9) | 1 | 0.134 | 0.026 |
- (참고 답) 1379 MPa 기준 1에 대해 2068 MPa에서 0.026입니다(1724 MPa에서는 0.134).

**A14** 질문: 구름 베어링 크기별 형상·재료 계수 fcm 대표값은 ANSI/ABMA의 몇 번 규격에 나오나요?

정답 문장:
- (핵심) TABLE I.—REPRESENTATIVE VALUES OF ROLLING-ELEMENT BEARING GEOMETRY AND MATERIAL COEFFICIENT fcm IN ANSI/ABMA STANDARDSa 9 AND 11 FOR REPRESENTATIVE ROLLING-ELEMENT BEARING SIZES [From Ref. 18.]
- (보조) Representative values of fcm are given in Table I from the ANSI/ABMA standards (Refs. 13 and 14).
- (보조) aStandards 9 and 11 are found in Refs. 13 and 14, respectively.
- (참고 답) ANSI/ABMA 규격 9와 11입니다(Ref. 18 인용).

**A15** 질문: 210 사이즈 원통 롤러 베어링에 기준 하중 29,190 N을 걸었을 때, 에어로스페이스 롤러 프로파일(평탄부 8 mm + 곡률 반경 크라운)에서 내륜 최대 헤르츠 응력은 얼마인가요?

정답 문장:
- (핵심) The reference load produces an inner-ring maximum Hertz stress of 2240 MPa (325 ksi) with the aerospace profile.
- (참고 답) 2240 MPa(325 ksi)입니다(기준 하중 29,190 N).

**A16** 질문: 진공유도용해-진공아크재용해(VIM–VAR)로 만든 AISI M-50 베어링강에 적용하는 수명계수는 재료, 공정, 최종 값이 각각 얼마인가요?

정답 문장:
- (핵심) | VIM–VARc AISI M–50 | 2 | 6 | 12 |
- (보조) TABLE XI.—LIFE FACTORS FOR BEARING STEELS AND STEEL PROCESSING [From Ref. 18.]
- (보조) |  | Material | Process | Resultant |
- (참고 답) 재료 계수 2, 공정 계수 6, 최종(합성) 수명계수 12입니다.

**A17** 질문: 베어링을 새로 사는 대신 재가공(rework)해서 다시 쓰면 신품 대비 비용을 얼마나 아낄 수 있나요?

정답 문장:
- (핵심) According to Zaretsky and Branzai (Ref. 20), the potential cost savings from bearing rework varies from 53 to 82 percent that of new bearings depending on the cost, size, and complexity of the bearing.
- (참고 답) 베어링의 가격·크기·복잡도에 따라 신품 대비 53~82%를 절감할 수 있습니다.

**A18** 질문: Out of the roughly 224,000 airline engine bearings that came back for repair, how many had to be scrapped because of spalling fatigue?

정답 문장:
- (핵심) Of the 224,000 bearings reported in Table IV(c), 1,977 bearings or ~0.88 percent (<1 percent) were rejected for fatigue.
- (핵심) Of the ~224,000 commercial engine bearings removed from service for rework, 1,977 or 0.88 percent were rejected because of fatigue.
- (핵심) (3) Of the ~224,000 commercial engine bearings removed from service for rework, 1,977 or
- (참고 답) 1,977 bearings, about 0.88 percent.

**A19** 질문: For a medium-series ball bearing, what is the outer-race to inner-race life ratio Lo/Li for Hertz stress-life exponents of 9 and 12?

정답 문장:
- (핵심) | Medium | .25 | 8.36 | 16.96 |
- (보조) Assuming cos  = 1 and fi = fo = 0.52, values of Lo/Li were calculated from Equa-tion (71) for n = 9 and 12 and are summarized in Table VI.
- (보조) | Ball bearing series | Bearing envelope size,a d cos β d e | Outer- to inner-race life ratio, X = Lo/Li |  |
- (참고 답) Lo/Li = 8.36 for n = 9 and 16.96 for n = 12 (envelope size 0.25).

**A20** 질문: In the NASA review of rolling-element bearing life prediction, which figure shows Wöhler-type stress-cycle curves with an endurance limit, and which source is it credited to?

정답 문장:
- (핵심) Figure 27.—Stress-life (S-N) curves illustrating concept of fatigue limit (Ref. 102).
- (보조) The classic Wohler curve illustrated in Figure 27(b) intro-duces the concept of a fatigue limit, where the stress-life relation is that of Equation (A1) until the stress reaches the value of the fatigue limit τf, at approximately 106 to 107 stress cycles; here the life is considered infinite.
- (참고 답) Figure 27, stress-life (S-N) curves illustrating the concept of fatigue limit, from Ref. 102.

**A21** 질문: Sugiura et al. ran rolling contact tests on fully crowned rollers with several crown radii. How much shorter was life because of edge loading than the central contact stress alone would suggest?

정답 문장:
- (핵심) They found that the effect of higher edge stresses resulted in an approximate 30 percent reduction in life when compared to the effect of the stress at the center of the contact area.
- (참고 답) About a 30 percent reduction in life.

**A22** 질문: How much compressive residual stress does AMS 6278 (VIM-VAR M50 NiL) have from heat treatment, and what is its theoretical relative life at a maximum Hertz stress of 1.4 GPa compared with AISI M-50?

정답 문장:
- (핵심) | AMS 6278 (VIM–VAR M50 NiL) | 0.4 (58) | 381 |
- (참고 답) 0.4 GPa (58 ksi) compressive residual stress and a relative life of 381 (AISI M-50 without residual stress = 1).

**A23** 질문: If I size a cylindrical roller bearing with Zaretsky's life equation and the rollers have an aerospace-type or chamfered end relief, which load exponent should I use, and how does it differ from uncrowned and fully crowned rollers?

정답 문장:
- (핵심) 3. Using the Zaretsky life model, the load-life exponent p is reduced from 5.0 for flat rollers to 4.6 for either aerospace or chamfered rollers and to 4.3 for fully-crowned rollers.
- (보조) An aerospace profile reduces the load-life exponent to p = 4.6.
- (보조) For an aerospace profile and chamfered rollers, p = 4.6.
- (보조) With the Zaretsky model, the load-life exponent p = 5.0 for a flat profile.
- (보조) The full crown reduces the exponent further, to p = 4.3.
- (보조) For the Zaretsky model with fully crowned rollers p = 4.3.
- (참고 답) p = 4.6 for aerospace or chamfered rollers, versus 5.0 for flat rollers and 4.3 for fully crowned rollers.

## B. 답변 채점

**B01** 질문: Why did bearings cut directly into the machine body become less common after the 19th century?

기준 문장:
- (핵심) Integral bearings were very common in 19th-century machinery but became progressively less common as interchangeable manufacture became popular.
- (보조) Integral bearings are not as common because bushings are easier to accommodate and can be replaced if necessary.

답변: Integral plain bearings became less common after the 19th century because bushings were easier to accommodate and could be replaced if necessary, whereas integral bearings could not be replaced and were more prone to failure when worn out [en_plain_bearing#1]. As interchangeable manufacture became popular, the ability to replace components became more important, leading to a shift away from integral bearings [en_plain_bearing#1].

**B02** 질문: 볼 베어링에 케이지를 달지 않으면 어떤 일이 생기나요?

기준 문장:
- (핵심) 케이지가 없으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다.
- (보조) Without the cage, the balls would eventually drift out of position during operation, causing the bearing to fail.

답변: 볼 베어링에 케이지를 달지 않으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다 [ko_ball_bearing#4]. 또한 케이지가 없으면 접선 위치는 두 개의 볼록한 표면이 서로 미끄러지면서 안정화되며, 이는 볼에 흠집이 생기고 마찰이 증가할 수 있다 [ko_ball_bearing#8].

**B03** (충실도 포함) 질문: 마모량이 하중, 미끄럼 거리, 경도와 어떤 비례 관계인지 알려주세요. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 어떻게 되나요?

기준 문장:
- (핵심) 마모의 진행 과정에 대하여 가장 단순한 고체간 미끄럼인 경우에 마모량는 하중 및 거리에 각각 비례하고 굳기 에 반비례한다고 하며, 다음과 같은 관계식으로 된다.
- (보조) The mass involved in wear is proportional to the distance traveled in the rubbing between the surfaces.
- (보조) The mass involved in wear is proportional to the applied load.
- (보조) The mass involved in wear is inversely proportional to the hardness of the less hard material.

답변: 마모량은 하중과 미끄럼 거리에 각각 비례하고, 경도에 반비례한다 [ko_wear#0]. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 2 × (1/2) = 1배로 유지된다 [ko_wear#0].

> [ko_wear#0] 기계공학에서 마모(磨耗)는 2개의 고체가 서로 접촉하면서 이동하고 있을 때, 그들 미끄럼 면에서부터 마찰에 의해서 물질이 이탈하고, 대체로 표면에 대하여 바람직하지 못한 영향을 주는 현상이다. 따라서 그 다뤄지는 범위는 매우 넓어지고, 다음과 같은 것이 있다.  재봉틀기름 등을 사용하며, 보통으로 생기는 정상마모(正常磨耗), 샌드페이퍼·모래 등에 의한 거칫거림마모, 고속·고하중하(高荷重下)에서 생기는 융착마모(融著磨耗), 장시간의 이용에 의해서 표면이 피로하여 생기는 얼룩마모, 물 등의 부식작용에 의한 부식마모, 이동거리가 0.5mm 정도인 미소이동 때 생기는 미동마모, 미끄럼면이 산화되어 있는 상태인 산화마모 등이 있다. 마모의 진행 과정에 대하여 가장 단순한 고체간 미끄럼인 경우에 마모량는 하중 및 거리에 각각 비례하고 굳기 에 반비례한다고 하며, 다음과 같은 관계식으로 된다. 는 비례정수이다. 는 미끄럼 조건에 따라서 정해지는 것이며, 동일한 마모기구가 성립하는 범위 내에서 유효하다. 가령 하중을 바꿈으로써, 정상마모로부터 산화마모로 바뀌면, 그에 상응하는 가 정해진다.

**B04** 질문: What does it mean when a grease is called shear-thinning?

기준 문장:
- (핵심) Greases are usually shear-thinning or pseudo-plastic fluids, which means that the viscosity of the fluid is reduced under shear stress.
- (보조) A common feature of greases is that they possess high initial viscosities which, upon the application of shear, drop to give the effect of an oil-lubricated bearing of approximately the same viscosity as the base oil used in the grease.
- (보조) This change in viscosity is called shear thinning.

답변: When a grease is called shear-thinning, it means that its viscosity decreases under the application of shear stress [en_grease#0]. This reduction in viscosity allows the grease to behave like a liquid lubricant with a viscosity similar to the base oil when subjected to mechanical force [en_grease#1]. The property is characteristic of true greases, which are typically pseudo-plastic fluids [en_grease#0].

**B05** 질문: What is the advantage of a sleeve bearing over a ball bearing in case fans, and what happens to its life at high rotation speed?

기준 문장:
- (핵심) 슬리브베어링 (sleeve bearing) - 볼베어링 방식에 비해 낮은 소음이 장점이나, 비교적 낮은 내구성(내열성 및 수명)이 단점이다.
- (보조) 높은 회전속도에서는 고발열로 인해 수명이 급격하게 단축되므로 높은 회전 속도와 내구성을 요구하지 않는 케이스 팬으로 채용된다.

답변: The advantage of a sleeve bearing over a ball bearing in case fans is that it has lower noise [ko_bearing#3]. At high rotation speed, the sleeve bearing experiences high friction and heat generation, which causes its life to be drastically shortened [ko_bearing#3].

**B06** 질문: 구름 베어링 크기별 형상·재료 계수 fcm 대표값은 ANSI/ABMA의 몇 번 규격에 나오나요?

기준 문장:
- (핵심) TABLE I.—REPRESENTATIVE VALUES OF ROLLING-ELEMENT BEARING GEOMETRY AND MATERIAL COEFFICIENT fcm IN ANSI/ABMA STANDARDSa 9 AND 11 FOR REPRESENTATIVE ROLLING-ELEMENT BEARING SIZES [From Ref. 18.]
- (보조) Representative values of fcm are given in Table I from the ANSI/ABMA standards (Refs. 13 and 14).
- (보조) aStandards 9 and 11 are found in Refs. 13 and 14, respectively.

답변: 구름 베어링 크기별 형상·재료 계수 fcm 대표값은 ANSI/ABMA의 9번 및 11번 규격에 나오나요 [nasa-tp-2013-215305-rev1#38].

**B07** (충실도 포함) 질문: What fraction of the world's total energy expenditure is caused by friction and wear in the transport, manufacturing, power generation and residential sectors?

기준 문장:
- (핵심) 전 세계 총 에너지 지출의 약 20%는 운송, 제조, 발전 및 주거 부문에서 마찰과 마모의 영향으로 인해 발생한다.
- (핵심) Approximately 20% of the world's energy (2012) is consumed by friction and wear in the transportation, manufacturing, power generation, and residential sectors.

답변: Approximately 23% of the world's total energy expenditure is caused by tribological contacts, of which 20% is due to friction and 3% to remanufacturing worn parts and spare equipment due to wear [en_tribology#3]. This includes the transport, manufacturing, power generation, and residential sectors [en_tribology#0]. The fraction attributed specifically to friction is 20% of global energy consumption [en_tribology#0]. Therefore, friction alone accounts for about 20% of the world's energy consumption in these sectors [en_tribology#0].

> [en_tribology#3] Despite considerable research since the Jost Report, the global impact of friction and wear on energy consumption, economic expenditure, and carbon dioxide emissions are still considerable. In 2017, Kenneth Holmberg and Ali Erdemir attempted to quantify their impact worldwide. They considered the four main energy consuming sectors: transport, manufacturing, power generation, and residential. The following were concluded:  In total, ~23% of the world's energy consumption originates from tribological contacts. Of that, 20% is to overcome friction and 3% to remanufacture worn parts and spare equipment due to wear and wear-related. By friction reduction and wear protection, energy losses in machinery could lower total energy consumption. The largest short term energy savings are envisioned in transport (25%) and in power generation (20%) while the potential savings in the manufacturing and residential sectors are estimated to be ~10%. In the longer term, savings would be 55%, 40%, 25%, and 20%, respectively. Implementing advanced tribological technologies can also reduce global carbon dioxide emissions by as much as 1460 million tons of carbon dioxide equivalent (MtCO2) and result in 450000 million euros cost savings in the short term. In the long term, the reduction could be as large as 3140 MtCO2 and the cost savings 970000 million euros. Classical tribology covering such applications as ball bearings, gear drives, clutches, brakes, etc. was developed in the context of mechanical engineering. It also embrace micro- and nanotechnology as well as aspects of biology and medicine.

> [en_tribology#0] Tribology is the science and engineering of understanding friction, lubrication and wear phenomena for interacting surfaces in relative motion. It is highly interdisciplinary, drawing on many academic fields, including physics, chemistry, materials science, mathematics, biology and engineering. The fundamental objects of study in tribology are tribosystems, which are physical systems of contacting surfaces. Subfields of tribology include biotribology, nanotribology and space tribology. It is also related to other areas such as the coupling of corrosion and tribology in tribocorrosion and the contact mechanics of how surfaces in contact deform. Approximately 20% of the world's energy (2012) is consumed by friction and wear in the transportation, manufacturing, power generation, and residential sectors.  The word tribology derives from the Greek root τριβ- of the verb τρίβω, tribo, "I rub" in classic Greek, and the suffix -logy from -λογία, -logia "study of", "knowledge of". Peter Jost coined the word in 1966, in the eponymous report which highlighted the cost of friction, wear and corrosion to the UK economy.  Despite the relatively recent naming of the field of tribology, quantitative studies of friction can be traced as far back as 1493, when Leonardo da Vinci first noted the two fundamental 'laws' of friction. According to Leonardo, frictional resistance was the same for two different objects of the same weight but making contact over different widths and lengths. He also observed that the force needed to overcome friction doubles as weight doubles.

**B08** (충실도 포함) 질문: In the service life analysis built on the Naval Air Rework Facility removal data, which cause for removal gives the shortest bearing life?

기준 문장:
- (핵심) From Table III, “corrosion pitting” is the lowest lived failure mode.

답변: Rolling-element fatigue gives the shortest bearing life in the service life analysis built on the Naval Air Rework Facility removal data. This is because eliminating rolling-element fatigue as a cause for removal increases the L10 service life by approximately 3 percent, indicating that fatigue-related failures occur earlier and reduce the overall service life. The data show that 0.88 percent of bearings were removed due to fatigue out of ~224,000 total bearings, and at 5,000 hours, 97 percent of bearings would be removed for cause, suggesting a significant impact on life. [nasa-tm-2017-219545#3] [nasa-tm-2017-219545#34]

> [nasa-tm-2017-219545#3] Today, bearing fatigue probably accounts for less than 5 percent of bearings removed from service for cause. A bearing service life prediction methodology and tutorial indexed to eight probable causes for bearing removal, including fatigue, are presented, which incorporate strict series reliability; Weibull statistical analysis; available published field data from the Naval Air Rework Facility; and ~224,000 rolling-element bearings removed for rework from commercial aircraft engines. Bearing service life, Lserv, can be benchmarked and calculated to the bearing fatigue life, L10, as follows: L serv = X 1 m L 10 , where X is the number of bearings removed from service because of fatigue divided by the total of all bearings removed from service regardless of cause and m is the Weibull modulus of the bearings removed from service. The most conservative bearing L10 service life calculation is obtained assuming an exponential distribution where m = 1.1. Of the ~224,000 commercial engine bearings removed from service for rework, 1,977 or 0.88 percent were rejected because of fatigue. From the Naval Air Rework Facility bearing data, eliminating rolling-element fatigue as a cause for removal, the L10 service life of these bearings would increase by approximately 3 percent.  In the first edition of his book, Ball and Roller Bearing Engineering, Palmgren (Ref. 1) defines “The Term (Bearing) LIFE” as follows: “No bearing gives an unlimited length of service. If a ball or roller bearing is exposed to moisture or dirt, it may be rendered unserviceable due to rust (corrosion) or wear, after a period of service which obviously cannot be predicted.

> [nasa-tm-2017-219545#34] The following results were obtained: (1) Bearing service life, Lserv, can be benchmarked and calculated to the bearing L10 fatigue life as follows: L = X 1 m L serv 10 where Lserv is the service life at a 90 percent reliability or a 10 percent probability for bearing removal; X is a fractional percent calculated by taking the number of bearings removed from service because of fatigue divided by the number of all bearings removed from service regardless of cause; m is the Weibull modulus of all the bearings removed from service; and L10 is the bearing calculated life based on rolling-element fatigue at a 90 percent reliability or a 10 percent probability of a fatigue failure. (2) The most conservative bearing L10 service life calculation is obtained assuming an exponential distribution where m = 1.1. (3) Of the ~224,000 commercial engine bearings removed from service for rework, 1,977 or 0.88 percent were rejected because of fatigue. (4) From the Naval Air Rework Facility bearing data, eliminating rolling-element fatigue as a cause for removal, the L10 service life of these bearings would increase by approximately 3 percent. At 5,000 h or the bearing L10 fatigue life, 97 percent of the bearings would be removed from service for cause.

**B09** (충실도 포함) 질문: 앵귤러 콘택트 볼 베어링에서 접촉각을 키우면 어느 방향 하중을 더 잘 견디게 되나요?

기준 문장:
- (핵심) 접촉각이 클수록(일반적으로 10~45도 범위) 지지되는 축 하중은 높지만 반경 하중은 낮아진다.
- (보조) The larger the contact angle (typically in the range 10 to 45 degrees), the higher the axial load supported, but the lower the radial load.

답변: 앵귤러 콘택트 볼 베어링에서 접촉각이 클수록 지지되는 축 하중은 높지만 반경 하중은 낮아진다 [ko_ball_bearing#2]. 따라서 접촉각을 키우면 축 방향 하중을 더 잘 견디게 된다 [ko_ball_bearing#2].

> [ko_ball_bearing#2] 접촉각이 클수록(일반적으로 10~45도 범위) 지지되는 축 하중은 높지만 반경 하중은 낮아진다. 터빈, 제트 엔진 및 치과 장비와 같은 고속 응용 분야에서는 볼에 의해 생성되는 원심력이 내륜 및 외륜의 접촉각을 변경한다. 질화 규소와 같은 세라믹은 낮은 밀도(강철의 40%) 때문에 이러한 응용 분야에서 정기적으로 사용된다. 이러한 재료는 원심력을 크게 줄이고 고온 환경에서도 잘 작동한다. 또한 유리나 도자기처럼 균열되거나 부서지지 않고 베어링 강과 유사한 방식으로 마모되는 경향이 있다. 대부분의 자전거는 헤드셋에 앵귤러 콘택트 베어링을 사용하는데, 이는 이러한 베어링에 가해지는 힘이 반경 방향과 축 방향 모두에 있기 때문이다.  축방향 또는 스러스트 볼 베어링은 나란히 놓인 레이스를 사용한다. 축방향 하중은 베어링을 통해 직접 전달되는 반면, 반경 방향 하중은 잘 지지되지 않고 레이스를 분리시키는 경향이 있어 더 큰 반경 방향 하중은 베어링을 손상시킬 가능성이 높다.  딥 그루브 레이디얼 베어링에서 레이스 치수는 그 안에 들어 있는 볼의 치수와 가깝다. 딥 그루브 베어링은 얕은 그루브보다 더 높은 하중을 지지한다.

**B10** 질문: How often should the grease be changed in a 100 mm bearing compared with a 40 mm one?

기준 문장:
- (핵심) 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.
- (핵심) Time between grease replacements decreases very strongly with diameter of bearing: for a 40 mm bearing, grease should be replaced every 5000 working hours, while for a 100 mm bearing it should be replaced every 500 working hours.

답변: The grease in a 100 mm bearing should be changed every 500 working hours, while for a 40 mm bearing it should be changed every 5000 working hours. [en_ball_bearing#13] This means the grease replacement interval for a 100 mm bearing is 10 times shorter than for a 40 mm bearing. [ko_ball_bearing#15] The time between grease replacements decreases very strongly with the diameter of the bearing. [en_grease#14]

**B11** 질문: How often should the grease be changed in a 100 mm bearing compared with a 40 mm one?

기준 문장:
- (핵심) 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.
- (핵심) Time between grease replacements decreases very strongly with diameter of bearing: for a 40 mm bearing, grease should be replaced every 5000 working hours, while for a 100 mm bearing it should be replaced every 500 working hours.

답변: The grease in a 100 mm bearing should be changed every 500 working hours, while for a 40 mm bearing it should be changed every 5000 working hours. [en_ball_bearing#13] This means the grease replacement interval for a 100 mm bearing is 10 times shorter than for a 40 mm bearing. [ko_ball_bearing#15] The time between grease replacements decreases very strongly with the diameter of the bearing. [en_ball_bearing#13]

**B12** (충실도 포함) 질문: 볼 베어링에 케이지를 달지 않으면 어떤 일이 생기나요?

기준 문장:
- (핵심) 케이지가 없으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다.
- (보조) Without the cage, the balls would eventually drift out of position during operation, causing the bearing to fail.

답변: 볼 베어링에 케이지를 달지 않으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다 [ko_ball_bearing#4]. 또한, 접선 위치는 두 개의 볼록한 표면이 서로 미끄러지면서 안정화되며, 이는 볼에 흠집이 생기는 것을 방지하고 마찰이 적다는 장점이 없다 [ko_ball_bearing#8]. 케이지가 없으면 볼의 위치가 불안정해지고, 하중 지지력이 저하된다 [ko_ball_bearing#7].

> [ko_ball_bearing#4] 페어링 메커니즘은 단순히 베어링을 직접 마주보게 하거나, 심, 부싱 또는 샤프트 특징으로 분리할 수 있다.  콘래드 콘래드 스타일 볼 베어링은 1903년 영국 특허 12,206호와 1906년 미국 특허 822,723호를 받은 발명가 로버트 콘래드의 이름을 따서 명명되었다. 이 베어링은 내륜을 외륜에 대해 편심 위치에 배치하고, 두 링이 한 점에서 접촉하게 하여 접촉점 반대편에 큰 틈을 만든 다음 볼을 틈을 통해 삽입하고 베어링 어셈블리 주위에 균등하게 분배하여 링이 동심원이 되도록 조립한다. 조립은 볼의 상대적 위치를 유지하기 위해 볼에 케이지를 장착함으로써 완료된다. 케이지가 없으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다. 케이지는 하중을 받지 않으며 볼의 위치를 유지하는 역할만 한다. 콘래드 베어링은 반경 방향 및 축 방향 하중을 모두 견딜 수 있다는 장점이 있지만, 베어링 어셈블리에 로드할 수 있는 볼의 수가 제한되어 하중 용량이 낮다는 단점이 있다. 아마도 가장 잘 알려진 산업용 볼 베어링은 딥 그루브 콘래드 스타일일 것이다. 이 베어링은 대부분의 기계 산업에서 사용된다. 슬롯 필

> [ko_ball_bearing#8] 스냅 링은 플랜지 기능을 담당한다. 케이지형 케이지는 일반적으로 콘래드 스타일 볼 베어링에서 볼을 고정하는 데 사용된다. 다른 구조 유형에서는 특정 케이지 모양에 따라 볼의 수가 줄어들어 하중 지지력이 감소할 수 있다. 케이지가 없으면 접선 위치는 두 개의 볼록한 표면이 서로 미끄러지면서 안정화된다. 케이지가 있으면 접선 위치는 볼록한 표면이 일치하는 오목한 표면에서 미끄러지면서 안정화되는데, 이는 볼에 흠집이 생기는 것을 방지하고 마찰이 적다. 케이지형 롤러 베어링은 존 해리슨이 18세기 중반 크로노그래프 작업의 일환으로 발명했다. 세라믹 볼을 사용한 하이브리드 볼 베어링 세라믹 베어링 볼은 크기와 재료에 따라 강철 볼보다 최대 40% 가볍다. 이는 원심 하중과 미끄러짐을 줄여주므로 하이브리드 세라믹 베어링은 기존 베어링보다 20%에서 40% 더 빠르게 작동할 수 있다. 이는 베어링이 회전할 때 외륜 홈이 볼에 가하는 안쪽 방향 힘이 줄어든다는 것을 의미한다. 이러한 힘의 감소는 마찰과 마찰력#구름 마찰력을 줄인다. 가벼운 볼은 베어링을 더 빠르게 회전시키고, 속도를 유지하는 데 더 적은 전력을 사용한다. 세라믹 볼은 일반적으로 레이스보다 단단하다. 마모로 인해 시간이 지남에 따라 레이스에 홈이 생길 것이다.

> [ko_ball_bearing#7] 3선, 선형 및 기타 와이어 레이스 베어링도 있다. 열 단열 베어링과 복열 베어링의 두 가지 열 설계가 있다. 대부분의 볼 베어링은 단열 설계로, 베어링 볼이 한 줄로 되어 있음을 의미한다. 이 설계는 반경 방향 및 스러스트 하중에 작용한다. 복열 설계는 베어링 볼이 두 줄로 되어 있다. 단열 베어링에 비해 복열 베어링의 장점은 양방향으로 반경 방향 및 축 방향 하중을 지지할 수 있다는 것이다. 복열 앵귤러 콘택트 볼 베어링은 기울기 효과도 지지할 수 있는 가파른 장착을 특징으로 한다. 복열 베어링의 다른 장점은 강성과 소형성이다. 단점은 단열 베어링보다 더 나은 정렬이 필요하다는 것이다. 플랜지형 외륜에 플랜지가 있는 베어링은 축 방향 위치 지정을 단순화한다. 이러한 베어링용 하우징은 균일한 직경의 관통 구멍으로 구성될 수 있지만, 하우징의 입구 면(외면 또는 내면)은 구멍 축에 대해 실제로 수직으로 가공되어야 한다. 그러나 이러한 플랜지는 제조 비용이 매우 많이 든다. 유사한 이점을 가진 베어링 외륜의 보다 비용 효율적인 배열은 외경의 양쪽 끝 또는 한쪽 끝에 스냅 링 홈을 만드는 것이다. 스냅 링은 플랜지 기능을 담당한다. 케이지형 케이지는 일반적으로 콘래드 스타일 볼 베어링에서 볼을 고정하는 데 사용된다.

**B13** (충실도 포함) 질문: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요?

기준 문장:
- (핵심) There are three usual limits to the lifetime or load capacity of a bearing: abrasion, fatigue and pressure-induced welding.
- (보조) Although there are many other apparent causes of bearing failure, most can be reduced to these three.

답변: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 금속 피로, 윤활 조건, 그리고 하중에 대한 요소입니다 [ko_ball_bearing#11]. 금속 피로는 수명을 제한하며, 수명 분포는 베이불 분포로 설명됩니다 [ko_ball_bearing#11][en_ball_bearing#10]. 윤활 조건은 점도가 너무 높거나 낮을 경우 수명에 영향을 미치며, 특히 점도가 낮을 경우 일반 오일에서는 수명이 점도의 제곱에 비례하여 감소합니다 [ko_ball_bearing#14]. 하중은 베어링의 수명과 직접적인 관계를 가지며, 현대 재료는 룬드베르크와 팔름그렌이 결정한 하중과 수명 관계와는 다른 관계를 보여줍니다 [ko_ball_bearing#11][en_ball_bearing#10].

> [ko_ball_bearing#11] 베어링의 공칭 최대 하중은 100만 회전의 수명에 대한 것이며, 50 Hz(즉, 3000 RPM)에서는 5.5 작동 시간의 수명에 해당한다. 해당 유형 베어링의 90%는 최소한 그 수명을 가지며, 50%의 베어링은 최소 5배 더 긴 수명을 가진다. 업계 표준 수명 계산은 1947년에 룬드베르크(Lundberg)와 팔름그렌(Palmgren)이 수행한 작업을 기반으로 한다. 이 공식은 수명이 금속 피로에 의해 제한되며, 수명 분포는 베이불 분포로 설명될 수 있다고 가정한다. 재료 특성, 윤활 및 하중에 대한 요소를 포함하는 다양한 변형 공식이 존재한다. 하중에 대한 요소는 현대 재료가 룬드베르크와 팔름그렌이 결정한 것과는 다른 하중과 수명 간의 관계를 보여준다는 암묵적인 인정으로 볼 수 있다.  베어링이 회전하지 않으면 최대 하중은 요소 또는 레이스웨이의 소성 변형을 유발하는 힘에 의해 결정된다. 요소에 의해 발생하는 함몰은 응력을 집중시키고 구성 요소에 균열을 발생시킬 수 있다. 회전하지 않거나 매우 느리게 회전하는 베어링의 최대 하중을 "정적" 최대 하중이라고 한다. 또한 베어링이 회전하지 않는 경우, 베어링에 가해지는 진동력은 베어링 레이스 또는 구름 요소에 충격 손상을 일으킬 수 있으며, 이를 브리넬링이라고 한다.

> [en_ball_bearing#10] The formula assumes the life to be limited by metal fatigue and that the life distribution can be described by a Weibull distribution. Many variations of the formula exist that include factors for material properties, lubrication, and loading. Factoring for loading may be viewed as a tacit admission that modern materials demonstrate a different relationship between load and life than Lundberg and Palmgren determined .  If a bearing is not rotating, maximum load is determined by force that causes plastic deformation of elements or raceways. The indentations caused by the elements can concentrate stresses and generate cracks at the components. Maximum load for not or very slowly rotating bearings is called "static" maximum load. Also, if a bearing is not rotating, oscillating forces on the bearing can cause impact damage to the bearing race or the rolling elements, known as brinelling. A second lesser form called false brinelling occurs if the bearing only rotates across a short arc and pushes lubricant out away from the rolling elements. For a rotating bearing, the dynamic load capacity indicates the load to which the bearing endures 1,000,000 cycles. If a bearing is rotating, but experiences heavy load that lasts shorter than one revolution, static max load must be used in computations, since the bearing does not rotate during the maximum load. If a sideways torque is applied to a deep groove radial bearing, an uneven force in the shape of an ellipse is applied on the outer ring by the rolling elements, concentrating in two regions on opposite sides of the outer ring.

> [ko_ball_bearing#14] 베어링 외경과 차축 구멍 직경의 평균이 50 mm이고 3000 RPM으로 회전하는 베어링의 권장 동적 점도는 12 mm2/s이다. 오일의 동적 점도는 온도에 따라 크게 달라진다는 점에 유의해야 한다. 50–70 °C의 온도 상승은 점도를 10배 감소시킨다. 윤활유의 점도가 권장보다 높으면 베어링의 수명이 증가하며, 대략 점도의 제곱근에 비례한다. 윤활유의 점도가 권장보다 낮으면 베어링의 수명은 감소하며, 얼마나 감소하는지는 사용되는 오일의 종류에 따라 달라진다. EP('극한 압력') 첨가제가 포함된 오일의 경우 수명은 동적 점도의 제곱근에 비례하며, 이는 점도가 너무 높은 경우와 마찬가지이다. 반면 일반 오일의 경우 권장보다 낮은 점도를 사용하면 수명은 점도의 제곱에 비례한다. 윤활은 그리스로 할 수 있는데, 그리스는 일반적으로 베어링 내에 보관되어 볼에 의해 압축될 때 윤활유를 방출하는 장점이 있다. 이는 베어링 금속에 환경으로부터 보호 장벽을 제공하지만, 이 그리스를 주기적으로 교체해야 하고 베어링의 최대 하중이 감소한다는 단점이 있다(베어링이 너무 뜨거워지면 그리스가 녹아 베어링 밖으로 흘러나오기 때문). 그리스 교체 주기는 베어링의 직경에 따라 매우 강하게 감소한다. 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.

**B14** (충실도 포함) 질문: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요?

기준 문장:
- (핵심) There are three usual limits to the lifetime or load capacity of a bearing: abrasion, fatigue and pressure-induced welding.
- (보조) Although there are many other apparent causes of bearing failure, most can be reduced to these three.

답변: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 금속 피로, 윤활 상태, 그리고 하중의 종류와 크기입니다. 수명은 금속 피로에 의해 제한되며, 이는 베이불 분포로 설명될 수 있습니다 [ko_ball_bearing#11]. 윤활은 하중과 수명 간의 관계에 영향을 미치며, 점도가 너무 낮거나 높으면 수명이 감소하거나 증가할 수 있습니다 [ko_ball_bearing#14]. 하중은 베어링의 수명에 직접적인 영향을 미치며, 특히 정적 하중이나 짧은 시간 동안 발생하는 중간 하중은 수명을 감소시킬 수 있습니다 [ko_ball_bearing#10].

> [ko_ball_bearing#11] 베어링의 공칭 최대 하중은 100만 회전의 수명에 대한 것이며, 50 Hz(즉, 3000 RPM)에서는 5.5 작동 시간의 수명에 해당한다. 해당 유형 베어링의 90%는 최소한 그 수명을 가지며, 50%의 베어링은 최소 5배 더 긴 수명을 가진다. 업계 표준 수명 계산은 1947년에 룬드베르크(Lundberg)와 팔름그렌(Palmgren)이 수행한 작업을 기반으로 한다. 이 공식은 수명이 금속 피로에 의해 제한되며, 수명 분포는 베이불 분포로 설명될 수 있다고 가정한다. 재료 특성, 윤활 및 하중에 대한 요소를 포함하는 다양한 변형 공식이 존재한다. 하중에 대한 요소는 현대 재료가 룬드베르크와 팔름그렌이 결정한 것과는 다른 하중과 수명 간의 관계를 보여준다는 암묵적인 인정으로 볼 수 있다.  베어링이 회전하지 않으면 최대 하중은 요소 또는 레이스웨이의 소성 변형을 유발하는 힘에 의해 결정된다. 요소에 의해 발생하는 함몰은 응력을 집중시키고 구성 요소에 균열을 발생시킬 수 있다. 회전하지 않거나 매우 느리게 회전하는 베어링의 최대 하중을 "정적" 최대 하중이라고 한다. 또한 베어링이 회전하지 않는 경우, 베어링에 가해지는 진동력은 베어링 레이스 또는 구름 요소에 충격 손상을 일으킬 수 있으며, 이를 브리넬링이라고 한다.

> [ko_ball_bearing#14] 베어링 외경과 차축 구멍 직경의 평균이 50 mm이고 3000 RPM으로 회전하는 베어링의 권장 동적 점도는 12 mm2/s이다. 오일의 동적 점도는 온도에 따라 크게 달라진다는 점에 유의해야 한다. 50–70 °C의 온도 상승은 점도를 10배 감소시킨다. 윤활유의 점도가 권장보다 높으면 베어링의 수명이 증가하며, 대략 점도의 제곱근에 비례한다. 윤활유의 점도가 권장보다 낮으면 베어링의 수명은 감소하며, 얼마나 감소하는지는 사용되는 오일의 종류에 따라 달라진다. EP('극한 압력') 첨가제가 포함된 오일의 경우 수명은 동적 점도의 제곱근에 비례하며, 이는 점도가 너무 높은 경우와 마찬가지이다. 반면 일반 오일의 경우 권장보다 낮은 점도를 사용하면 수명은 점도의 제곱에 비례한다. 윤활은 그리스로 할 수 있는데, 그리스는 일반적으로 베어링 내에 보관되어 볼에 의해 압축될 때 윤활유를 방출하는 장점이 있다. 이는 베어링 금속에 환경으로부터 보호 장벽을 제공하지만, 이 그리스를 주기적으로 교체해야 하고 베어링의 최대 하중이 감소한다는 단점이 있다(베어링이 너무 뜨거워지면 그리스가 녹아 베어링 밖으로 흘러나오기 때문). 그리스 교체 주기는 베어링의 직경에 따라 매우 강하게 감소한다. 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.

> [ko_ball_bearing#10] 볼과 레이스 모두 비슷한 경도를 가지기 때문에 마모는 고속에서 볼과 레이스 모두에 파편을 유발할 수 있으며, 이는 스파크를 유발할 수 있다. 자동 조심 베어링 그림에 표시된 빙크비스트 베어링과 같은 자동 조심 볼 베어링은 구형 레이스웨이를 가진 외륜 내에 내륜과 볼 어셈블리가 포함되도록 구성된다. 이 구조는 샤프트 또는 하우징 변형 또는 부적절한 장착으로 인한 작은 각도 오정렬을 베어링이 허용할 수 있게 한다. 이 베어링은 주로 섬유 공장의 변속기 샤프트와 같이 매우 긴 샤프트를 가진 베어링 배열에 사용되었다. 자동 조심 볼 베어링의 한 가지 단점은 제한된 하중 등급인데, 외륜 레이스웨이가 매우 낮은 오스큘레이션(반경이 볼 반경보다 훨씬 크다)을 가지기 때문이다. 이는 유사한 디자인을 가졌지만 볼 대신 롤러를 사용하는 구면 롤러 베어링의 발명으로 이어졌다. 구면 스러스트 롤러 베어링은 빙크비스트의 발견에서 파생된 또 다른 발명이다.  베어링의 계산된 수명은 베어링이 지지하는 하중과 작동 속도에 따라 달라진다. 업계 표준 가용 베어링 수명은 베어링 하중의 세제곱에 반비례한다. 베어링의 공칭 최대 하중은 100만 회전의 수명에 대한 것이며, 50 Hz(즉, 3000 RPM)에서는 5.5 작동 시간의 수명에 해당한다.

**B15** 질문: What does it mean when a grease is called shear-thinning?

기준 문장:
- (핵심) Greases are usually shear-thinning or pseudo-plastic fluids, which means that the viscosity of the fluid is reduced under shear stress.
- (보조) A common feature of greases is that they possess high initial viscosities which, upon the application of shear, drop to give the effect of an oil-lubricated bearing of approximately the same viscosity as the base oil used in the grease.
- (보조) This change in viscosity is called shear thinning.

답변: When a grease is called shear-thinning, it means that its viscosity decreases under the application of shear stress [en_grease#0]. This reduction in viscosity allows the grease to flow more easily when force is applied, such as when it is pumped into a bearing using a grease gun [en_grease#1]. After sufficient shear is applied, the viscosity drops and approaches that of the base lubricant, such as mineral oil [en_grease#1]. This behavior is characteristic of pseudo-plastic fluids and is a key property of true greases [en_grease#0].

**B16** (충실도 포함) 질문: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요?

기준 문장:
- (핵심) There are three usual limits to the lifetime or load capacity of a bearing: abrasion, fatigue and pressure-induced welding.
- (보조) Although there are many other apparent causes of bearing failure, most can be reduced to these three.

답변: 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 금속 피로, 윤활 상태, 그리고 하중 조건입니다 [ko_ball_bearing#11]. 금속 피로는 수명을 제한하며, 이는 룬드베르크와 팔름그렌의 공식에서 가정된 바 있습니다 [ko_ball_bearing#11]. 윤활 상태는 점도가 너무 높거나 낮을 경우 수명에 영향을 미치며, 점도는 수명에 제곱근 또는 제곱에 비례하여 영향을 줍니다 [ko_ball_bearing#14]. 하중 조건은 하중의 크기와 지속 시간에 따라 수명이 달라지며, 정적 하중이나 동적 하중에 따라 최대 하중이 결정됩니다 [ko_ball_bearing#10].

> [ko_ball_bearing#11] 베어링의 공칭 최대 하중은 100만 회전의 수명에 대한 것이며, 50 Hz(즉, 3000 RPM)에서는 5.5 작동 시간의 수명에 해당한다. 해당 유형 베어링의 90%는 최소한 그 수명을 가지며, 50%의 베어링은 최소 5배 더 긴 수명을 가진다. 업계 표준 수명 계산은 1947년에 룬드베르크(Lundberg)와 팔름그렌(Palmgren)이 수행한 작업을 기반으로 한다. 이 공식은 수명이 금속 피로에 의해 제한되며, 수명 분포는 베이불 분포로 설명될 수 있다고 가정한다. 재료 특성, 윤활 및 하중에 대한 요소를 포함하는 다양한 변형 공식이 존재한다. 하중에 대한 요소는 현대 재료가 룬드베르크와 팔름그렌이 결정한 것과는 다른 하중과 수명 간의 관계를 보여준다는 암묵적인 인정으로 볼 수 있다.  베어링이 회전하지 않으면 최대 하중은 요소 또는 레이스웨이의 소성 변형을 유발하는 힘에 의해 결정된다. 요소에 의해 발생하는 함몰은 응력을 집중시키고 구성 요소에 균열을 발생시킬 수 있다. 회전하지 않거나 매우 느리게 회전하는 베어링의 최대 하중을 "정적" 최대 하중이라고 한다. 또한 베어링이 회전하지 않는 경우, 베어링에 가해지는 진동력은 베어링 레이스 또는 구름 요소에 충격 손상을 일으킬 수 있으며, 이를 브리넬링이라고 한다.

> [ko_ball_bearing#14] 베어링 외경과 차축 구멍 직경의 평균이 50 mm이고 3000 RPM으로 회전하는 베어링의 권장 동적 점도는 12 mm2/s이다. 오일의 동적 점도는 온도에 따라 크게 달라진다는 점에 유의해야 한다. 50–70 °C의 온도 상승은 점도를 10배 감소시킨다. 윤활유의 점도가 권장보다 높으면 베어링의 수명이 증가하며, 대략 점도의 제곱근에 비례한다. 윤활유의 점도가 권장보다 낮으면 베어링의 수명은 감소하며, 얼마나 감소하는지는 사용되는 오일의 종류에 따라 달라진다. EP('극한 압력') 첨가제가 포함된 오일의 경우 수명은 동적 점도의 제곱근에 비례하며, 이는 점도가 너무 높은 경우와 마찬가지이다. 반면 일반 오일의 경우 권장보다 낮은 점도를 사용하면 수명은 점도의 제곱에 비례한다. 윤활은 그리스로 할 수 있는데, 그리스는 일반적으로 베어링 내에 보관되어 볼에 의해 압축될 때 윤활유를 방출하는 장점이 있다. 이는 베어링 금속에 환경으로부터 보호 장벽을 제공하지만, 이 그리스를 주기적으로 교체해야 하고 베어링의 최대 하중이 감소한다는 단점이 있다(베어링이 너무 뜨거워지면 그리스가 녹아 베어링 밖으로 흘러나오기 때문). 그리스 교체 주기는 베어링의 직경에 따라 매우 강하게 감소한다. 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.

> [ko_ball_bearing#10] 볼과 레이스 모두 비슷한 경도를 가지기 때문에 마모는 고속에서 볼과 레이스 모두에 파편을 유발할 수 있으며, 이는 스파크를 유발할 수 있다. 자동 조심 베어링 그림에 표시된 빙크비스트 베어링과 같은 자동 조심 볼 베어링은 구형 레이스웨이를 가진 외륜 내에 내륜과 볼 어셈블리가 포함되도록 구성된다. 이 구조는 샤프트 또는 하우징 변형 또는 부적절한 장착으로 인한 작은 각도 오정렬을 베어링이 허용할 수 있게 한다. 이 베어링은 주로 섬유 공장의 변속기 샤프트와 같이 매우 긴 샤프트를 가진 베어링 배열에 사용되었다. 자동 조심 볼 베어링의 한 가지 단점은 제한된 하중 등급인데, 외륜 레이스웨이가 매우 낮은 오스큘레이션(반경이 볼 반경보다 훨씬 크다)을 가지기 때문이다. 이는 유사한 디자인을 가졌지만 볼 대신 롤러를 사용하는 구면 롤러 베어링의 발명으로 이어졌다. 구면 스러스트 롤러 베어링은 빙크비스트의 발견에서 파생된 또 다른 발명이다.  베어링의 계산된 수명은 베어링이 지지하는 하중과 작동 속도에 따라 달라진다. 업계 표준 가용 베어링 수명은 베어링 하중의 세제곱에 반비례한다. 베어링의 공칭 최대 하중은 100만 회전의 수명에 대한 것이며, 50 Hz(즉, 3000 RPM)에서는 5.5 작동 시간의 수명에 해당한다.

**B17** 질문: 피로한도를 두지 않는 Lundberg-Palmgren 모델에서 최대 헤르츠 응력을 1379 MPa에서 2068 MPa로 올리면 상대 수명은 얼마로 줄어드나요?

기준 문장:
- (핵심) | 0 (0), Lundberg-Palmgren (Ref. 9) | 1 | 0.134 | 0.026 |

답변: 피로한도를 두지 않는 Lundberg-Palmgren 모델에서 최대 헤르츠 응력을 1379 MPa에서 2068 MPa로 올리면, 수명은 약 1/4258로 줄어듭니다. [nasa-tp-2013-215305-rev1#49]  
이 값은 ISO 281:2007 기준에서 2068 MPa에서의 수명이 4258×10⁶ 사이클임을 나타냅니다. [nasa-tp-2013-215305-rev1#49]  
1379 MPa에서의 수명은 무한대로 간주되며, 2068 MPa에서는 유한한 수명이 됩니다. [nasa-tp-2013-215305-rev1#49]

**B18** 질문: What fraction of the world's total energy expenditure is caused by friction and wear in the transport, manufacturing, power generation and residential sectors?

기준 문장:
- (핵심) 전 세계 총 에너지 지출의 약 20%는 운송, 제조, 발전 및 주거 부문에서 마찰과 마모의 영향으로 인해 발생한다.
- (핵심) Approximately 20% of the world's energy (2012) is consumed by friction and wear in the transportation, manufacturing, power generation, and residential sectors.

답변: Approximately 23% of the world's total energy expenditure is caused by tribological contacts, of which 20% is due to friction and 3% to remanufacturing worn parts and spare equipment due to wear [en_tribology#3]. This includes the transport, manufacturing, power generation, and residential sectors [en_tribology#0]. The fraction attributed to friction alone is 20% of global energy consumption [en_tribology#0].

**B19** 질문: How often should the grease be changed in a 100 mm bearing compared with a 40 mm one?

기준 문장:
- (핵심) 40 mm 베어링의 경우 그리스는 5000 작동 시간마다 교체해야 하는 반면, 100 mm 베어링의 경우 500 작동 시간마다 교체해야 한다.
- (핵심) Time between grease replacements decreases very strongly with diameter of bearing: for a 40 mm bearing, grease should be replaced every 5000 working hours, while for a 100 mm bearing it should be replaced every 500 working hours.

답변: The grease in a 100 mm bearing should be replaced every 500 working hours, while for a 40 mm bearing it should be replaced every 5000 working hours [en_ball_bearing#13][ko_ball_bearing#15][ko_ball_bearing#14]. Therefore, the grease replacement interval is 100 times shorter for a 100 mm bearing compared to a 40 mm bearing [en_ball_bearing#13][ko_ball_bearing#15][ko_ball_bearing#14].

**B20** 질문: 볼 베어링에 케이지를 달지 않으면 어떤 일이 생기나요?

기준 문장:
- (핵심) 케이지가 없으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있다.
- (보조) Without the cage, the balls would eventually drift out of position during operation, causing the bearing to fail.

답변: 볼 베어링에 케이지를 달지 않으면 볼은 작동 중에 결국 제자리를 벗어나 베어링이 고장 날 수 있습니다 [ko_ball_bearing#4]. 케이지가 없으면 접선 위치는 두 개의 볼록한 표면이 서로 미끄러지면서 안정화되며, 이는 볼에 흠집이 생기고 마찰이 증가시킬 수 있습니다 [ko_ball_bearing#8].

**B21** 질문: 마모량이 하중, 미끄럼 거리, 경도와 어떤 비례 관계인지 알려주세요. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 어떻게 되나요?

기준 문장:
- (핵심) 마모의 진행 과정에 대하여 가장 단순한 고체간 미끄럼인 경우에 마모량는 하중 및 거리에 각각 비례하고 굳기 에 반비례한다고 하며, 다음과 같은 관계식으로 된다.
- (보조) The mass involved in wear is proportional to the distance traveled in the rubbing between the surfaces.
- (보조) The mass involved in wear is proportional to the applied load.
- (보조) The mass involved in wear is inversely proportional to the hardness of the less hard material.

답변: 마모량은 하중과 미끄럼 거리에 각각 비례하고, 경도에 반비례한다 [ko_wear#0][en_tribology#25]. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 1배가 된다. 이는 하중이 두 배이고 거리가 반으로 줄어들었기 때문에, 두 배 × 반 = 1배이기 때문이다. 마모량은 하중과 거리의 곱에 비례하므로, 이 조건에서는 마모량이 변하지 않는다 [en_tribology#25].

**B22** (충실도 포함) 질문: 구동축을 설계할 때 강도를 확보하면서도 추가 중량을 피해야 하는 이유는 무엇인가요?

기준 문장:
- (핵심) 그러므로 스트레스를 견딜만큼 충분히 강해야 하며 관성 증가로 이어질 수 있으므로 하중을 추가로 너무 많이 주는 것은 피해야 한다.

답변: 구동축을 설계할 때 강도를 확보하면서도 추가 중량을 피해야 하는 이유는 구동축이 입력 토크와 부하 간 차이와 동등한 비틀림과 전단 응력을 받기 때문입니다. 이러한 비틀림 응력은 축의 강도를 초과하면 관성 증가로 이어져 파손이나 손상이 발생할 수 있기 때문입니다. 따라서 축의 강도를 충분히 확보하면서도 중량을 추가로 주면 관성 증가로 인해 응력이 증가하여 설계 안정성과 수명에 부정적인 영향을 줄 수 있기 때문입니다. [ko_drive_shaft#0]

> [ko_drive_shaft#0] 구동축(drive shaft)은 기계적 일률과 돌림힘, 회전을 전달하는 부품이다. 거리 때문에, 또는 상대적인 움직임을 허용할 필요가 있어서 직접 연결이 불가능한 드라이브트레인의 기타 부품들을 연결하기 위해 보통 사용한다. 구동축은 입력 토크와 부하 간 차이와 동등한 비틀림과 전단 응력에 종속된다. 그러므로 스트레스를 견딜만큼 충분히 강해야 하며 관성 증가로 이어질 수 있으므로 하중을 추가로 너무 많이 주는 것은 피해야 한다.  구동축의 영단어 드라이브샤프트(driveshaft)라는 단어는 19세기 중순에 등장했다. 스토버의 1861년 특허에서 이 용어는 기기가 구동되는 벨트 구동축을 의미했다. 이 용어는 최초 특허에는 사용되지 않는다. 다른 초기 용례로는 왓킨스와 브라이슨의 말에 의해 움직이는 예취기의 1861년 특허이다. 여기서 이 용어는 기기의 바퀴로부터 기어 트레인까지 힘을 전달하는 샤프트를 의미했다. 1890년대에 이 용어는 현대적 의미에 더 가까운 방식으로 사용되기 시작했다.

**B23** 질문: What fraction of the world's total energy expenditure is caused by friction and wear in the transport, manufacturing, power generation and residential sectors?

기준 문장:
- (핵심) 전 세계 총 에너지 지출의 약 20%는 운송, 제조, 발전 및 주거 부문에서 마찰과 마모의 영향으로 인해 발생한다.
- (핵심) Approximately 20% of the world's energy (2012) is consumed by friction and wear in the transportation, manufacturing, power generation, and residential sectors.

답변: Approximately 23% of the world's energy consumption originates from tribological contacts, of which 20% is due to friction and 3% to remanufacturing worn parts [en_tribology#3]. Thus, the fraction of the world's total energy expenditure caused by friction and wear in these sectors is 20% [en_tribology#0].

**B24** 질문: 칼슘계와 섬유(나트륨)계 그리스는 각각 어떤 성능이 장점이라고 분류하나요?

기준 문장:
- (핵심) 그리스는 증주제(tickner)의 종류에 따라 리튬(Li Grease), 칼슘(Ca Grease), 나트륨(Fibre Grease), 우레아계(Urea Grease) 등, 또 특성으로부터는 내수성(耐水性, Ca Grease) 및 내열성(Fibre Grease) 등으로 분류된다.
- (보조) 그리스는 증주제(Thickner)의 종류에 따라 리튬(Li Grease), 칼슘(Ca Grease), 나트륨(Fibre Grease), 우레아계(Urea Grease) 등, 또 특성으로부터는 내수성(耐水性, Ca Grease) 및 내열성(Fibre Grease) 등으로 분류된다.
- (보조) Lithium-based greases are the most commonly used; sodium- and lithium-based greases have higher melting points (dropping points) than calcium-based greases but are not as resistant to the action of water.

답변: 칼슘계 그리스는 내수성(물에 강함)이 장점으로 분류됩니다 [ko_grease#0][ko_lubrication#0][de_schmierfett#4]. 섬유(나트륨)계 그리스는 윤활제의 혼합물에 의해 좋은 분산성(에멀전성)을 가지며, 주로 변형이 많은 기계 부품에 사용되며, 특히 전동기의 유동 그리스에 적합합니다 [de_schmierfett#4].

**B25** (충실도 포함) 질문: 마모량이 하중, 미끄럼 거리, 경도와 어떤 비례 관계인지 알려주세요. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 어떻게 되나요?

기준 문장:
- (핵심) 마모의 진행 과정에 대하여 가장 단순한 고체간 미끄럼인 경우에 마모량는 하중 및 거리에 각각 비례하고 굳기 에 반비례한다고 하며, 다음과 같은 관계식으로 된다.
- (보조) The mass involved in wear is proportional to the distance traveled in the rubbing between the surfaces.
- (보조) The mass involved in wear is proportional to the applied load.
- (보조) The mass involved in wear is inversely proportional to the hardness of the less hard material.

답변: 마모량은 하중과 미끄럼 거리에 각각 비례하고, 경도에 반비례합니다 [ko_wear#0][en_tribology#25][en_tribology#24]. 하중을 두 배로 하고 거리를 절반으로 줄이면 마모량은 두 배로 되며, 거리가 절반으로 줄어들면 전체 마모량은 1배로 유지되므로, 최종적으로 마모량은 동일하게 유지됩니다 [en_tribology#25][en_tribology#24].

> [ko_wear#0] 기계공학에서 마모(磨耗)는 2개의 고체가 서로 접촉하면서 이동하고 있을 때, 그들 미끄럼 면에서부터 마찰에 의해서 물질이 이탈하고, 대체로 표면에 대하여 바람직하지 못한 영향을 주는 현상이다. 따라서 그 다뤄지는 범위는 매우 넓어지고, 다음과 같은 것이 있다.  재봉틀기름 등을 사용하며, 보통으로 생기는 정상마모(正常磨耗), 샌드페이퍼·모래 등에 의한 거칫거림마모, 고속·고하중하(高荷重下)에서 생기는 융착마모(融著磨耗), 장시간의 이용에 의해서 표면이 피로하여 생기는 얼룩마모, 물 등의 부식작용에 의한 부식마모, 이동거리가 0.5mm 정도인 미소이동 때 생기는 미동마모, 미끄럼면이 산화되어 있는 상태인 산화마모 등이 있다. 마모의 진행 과정에 대하여 가장 단순한 고체간 미끄럼인 경우에 마모량는 하중 및 거리에 각각 비례하고 굳기 에 반비례한다고 하며, 다음과 같은 관계식으로 된다. 는 비례정수이다. 는 미끄럼 조건에 따라서 정해지는 것이며, 동일한 마모기구가 성립하는 범위 내에서 유효하다. 가령 하중을 바꿈으로써, 정상마모로부터 산화마모로 바뀌면, 그에 상응하는 가 정해진다.

> [en_tribology#25] The mass involved in wear is proportional to the distance traveled in the rubbing between the surfaces. Law 2 – Load The mass involved in wear is proportional to the applied load. Law 3 – Hardness The mass involved in wear is inversely proportional to the hardness of the less hard material. An important aspect of wear is emission of wear particles into the environment which increasingly threatens human health and ecology. The first researcher who investigated this topic was Ernest Rabinowicz.  The abrasive wear consists of the cutting effort of hard surfaces that act on softer surfaces and can be caused either by the roughness that as tips cut off the material against which they rub (two-body abrasive wear), or from particles of hard material that interpose between two surfaces in relative motion (three-body abrasive wear). At application levels, the two-body wear is easily eliminated by means of an adequate surface finish, while the three-body wear can bring serious problems and must therefore be removed as much as possible by means of suitable filters, even before of a weighted machine design.  The fatigue wear is a type of wear that is caused by alternative loads, which cause local contact forces repeated over time, which in turn lead to deterioration of the materials involved. The most immediate example of this type of wear is that of a comb. If you slide a finger over the teeth of the comb over and over again, it is observed that at some point one or more teeth of the comb come off. This phenomenon can lead to the breaking of the surfaces due to mechanical or thermal causes. The first case is that described above in which a repeated load causes high contact stresses.

> [en_tribology#24] Erroneously we tend to imagine wear in a direct correlation with friction, in reality these two phenomena can not be easily connected. There may be conditions such that low friction can result in significant wear and vice versa. In order for this phenomenon to occur, certain implementation times are required, which may change depending on some variables, such as load, speed, lubrication and environmental conditions, and there are different wear mechanisms, which may occur simultaneously or even combined with each other:  Adhesive wear; Abrasive wear; Fatigue wear; Corrosive wear; Rubbing wear or fretting; Erosion wear; Other minor wear phenomena (wear by impact, cavitation, wear-fusion, wear-spreading).  As known, the contact between two surfaces occurs through the interaction between asperities. If a shearing force is applied in the contact area, it may be possible to detach a small part of the weaker material, due to its adhesion to the harder surface. What is described is precisely the mechanism of the adhesive wear represented in the figure. This type of wear is very problematic, since it involves high wear speeds, but at the same time it is possible to reduce adhesion by increasing surface roughness and hardness of the surfaces involved, or by inserting layers of contaminants such as oxygen, oxides, water, or oils. In conclusion, the behavior of the adhesive wear volume can be described by means of three main laws  Law 1 – Distance The mass involved in wear is proportional to the distance traveled in the rubbing between the surfaces. Law 2 – Load The mass involved in wear is proportional to the applied load. Law 3 – Hardness

**B26** 질문: 상용 터보프롭 기어박스의 현장 수명 데이터와 비교하면, Lundberg-Palmgren 방식은 기어박스의 L10 수명을 몇 배나 낮게 예측했나요?

기준 문장:
- (핵심) The field data suggest that the L10 life of the gearbox was under predicted by a factor of 7.56 (Ref. 22).
- (핵심) The field data suggest that the L10 life of the gearbox was underpredicted by a factor of 7.56 (Ref. 94).

답변: Lundberg-Palmgren 방식은 상용 터보프롭 기어박스의 L10 수명을 7.56배나 낮게 예측했습니다. [nasa-tp-2013-215305-rev1#122] 이 데이터는 현장 수명이 5627시간이었고, Lundberg-Palmgren 모델로 예측된 수명은 774시간이었기 때문입니다. [nasa-tm-2015-218895#23] 이는 실제 수명보다 예측된 수명이 훨씬 낮음을 나타냅니다.

**B27** 질문: 고속 회전용 볼 베어링에 세라믹 볼을 쓰는 이유 중 하나인 밀도는 강철과 비교해 어느 정도인가요?

기준 문장:
- (핵심) 질화 규소와 같은 세라믹은 낮은 밀도(강철의 40%) 때문에 이러한 응용 분야에서 정기적으로 사용된다.
- (보조) Ceramics such as silicon nitride are now regularly used in such applications due to their low density (40% of steel).

답변: 세라믹 볼은 강철의 40% 정도의 밀도를 가집니다 [en_ball_bearing#2]. 이는 원심력을 크게 줄이고 고속 회전에서 더 효율적으로 작동하게 합니다 [en_ball_bearing#7].

