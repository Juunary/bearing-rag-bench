# 평가셋 검수 표본 (12/45, seed 42)



| qid | 질문 | 주 근거(gold[0]) | 판정 | 사유 |
|---|---|---|---|---|
| q004 (ko→en, hard) | 풍력터빈 블레이드나 헬리콥터 피치 베어링처럼 계속 구르지 못하고 작게 흔들리기만 하는 베어링에서 생기는 손상은 무엇인가요? | `en_fretting`: In rolling-element bearings, fretting may occur when the bearing is operating in a mainly oscillating motion and the balls or roller bars are not allowed to roll along the bearing groove as they would if it were a wheel bearing. | | |
| q005 (ko→en, easy) | 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요? | `en_rolling_element_bearing`: There are three usual limits to the lifetime or load capacity of a bearing: abrasion, fatigue and pressure-induced welding. | | |
| q010 (ko→de, hard) | 오토바이 앞 포크에서 오일과 공기가 새지 않도록 막는 데 쓰는 밀봉 부품은 무엇인가요? | `de_wellendichtring`: Entgegen ihrem ursprünglichen Einsatzzweck verwendet man RWDR auch als Gabeldichtring bei Motorrädern, um Austreten von Öl und Luft zwischen den Stand- und Tauchrohren zu verhindern und damit die Funktion des in der Gabel integrierten Dämpfers sicherzustellen. | | |
| q011 (ko→ko, easy) | 자동차가 커브를 돌 때 안쪽 바퀴와 바깥쪽 바퀴가 서로 다른 속도로 돌 수 있게 해 주는 장치는 무엇인가요? | `ko_differential`: 이와 같은 동력전달장치로서 차동기어가 사용되고 있다. | X | 지시어("이와 같은")로 앞 문맥이 필요해 단독 핵심 근거로 부적합. 자족적인 설명 문장을 gold[0]로 교체 |
| q013 (ko→en, hard) | 금속 표면이 서로 달라붙었다 떨어지며 표면에 덩어리가 생기는 접착 마모를 산업 현장에서는 뭐라고 부르나요? | `en_wear`: In industrial manufacturing, this is referred to as galling, which eventually breaches the oxidized surface layer and connects to the underlying bulk material, enhancing the possibility for a stronger adhesion and plastic flow around the lump. | | |
| q019 (en→en, easy) | What does it mean when a grease is called shear-thinning? | `en_grease`: A common feature of greases is that they possess high initial viscosities which, upon the application of shear, drop to give the effect of an oil-lubricated bearing of approximately the same viscosity as the base oil used in the grease. | | |
| q022 (en→en, hard) | Which phase of a fatigue failure uses up most of the component's life? | `en_fatigue_material`: Most of the fatigue life is generally consumed in the crack growth phase. | | |
| q024 (en→en, hard) | How can I tell fretting damage from false brinelling in a bearing? | `en_fretting`: The main difference is that false brinelling occurs under lubricated and fretting under dry contact conditions. | | |
| q029 (en→de, easy) | To what temperature may a bearing be heated for shrink-fit mounting on a shaft? | `de_waelzlager`: Um die nötige Einpresskraft bei Montage auf einer Welle zu verringern bzw. zum Aufschrumpfen wird das Lager mit einem elektrischen Heizgerät (Induktionsgerät) oder in einem Ölbad auf 80–100 °C erwärmt (um eine Stahlgefügeveränderung zu verhindern, je nach Hersteller max. ca. 125 °C). | | |
| q033 (de→de, easy) | Wie wird die Dichtlippe eines Radial-Wellendichtrings an die Welle gedrückt? | `de_wellendichtring`: Ihre Dichtlippe läuft auf der Oberfläche der sich drehenden Welle und wird meist von einer Schlauchfeder (Wurmfeder) radial auf die Wellenoberfläche gedrückt. | | |
| q034 (de→de, hard) | Warum verschweißen die Gleitpartner eines Lagers bei fehlendem Schmierfilm lokal miteinander? | `de_fressen_technik`: Fresser treten an tribologisch hochbeanspruchten Teilen auf, wenn deren Notlaufeigenschaften unzureichend sind und kein Schmierfilm mehr zwischen den Gleitelementen vorhanden ist, also keine hydrodynamische Schmierung mehr erfolgt. | X | '왜'를 묻는데 근거는 발생 조건만 서술. 원인 문장(국부 가열과 융착 온도)을 2점으로 올리고 조건 문장을 1점으로 내림 |
| q037 (de→de, easy) | In welchem Bereich liegen die geforderten Lebensdauern von Wälzlagern? | `de_waelzlager`: Die von Wälzlagern geforderten Lebensdauern reichen von wenigen hundert Stunden, zum Beispiel für Haushaltsgeräte oder medizinisch-technische Geräte, bis zu ca. 100.000 Stunden für Lauflager von Hochseeschiffen, Grubenpumpen und -gebläse und Papiermaschinen. | | |


검수 기록 (2026-10-12): 12개 중 q011, q034가 X, 나머지 10개는 판정 미기재(미확정). X 2건은 gold를 수정했고 7개 설정을 다시 돌렸으며 모든 지표가 소수점 셋째 자리까지 동일했다(정답 문장이 같은 청크에 있었기 때문).
