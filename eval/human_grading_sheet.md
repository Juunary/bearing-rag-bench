# 사람 채점표 (8개)

각 샘플의 질문, 평가셋 기준 문장, 답변, 답변이 인용한 청크 원문을 읽고 3항목을 표시해 주세요. 판정 모델의 결과는 포함되어 있지 않습니다.

- **정확성**: `맞음` = 질문이 묻는 사실이 기준 문장과 일치 / `부분` = 일부만 맞거나 틀린 내용이 섞임 / `틀림` / `거절` = 답이 NO_ANSWER이거나 정보가 없다고만 함
- **충실도**: `예` = 답변의 모든 사실 진술이 아래 인용 청크에 있음 / `아니오` = 청크에 없는 내용이 있음
- **답변 관련성**: `예` = 질문이 묻는 것을 다루려고 함(맞는지는 따지지 않음) / `아니오` = 다른 얘기이거나 정보가 없다고만 함

채팅에 아래 형식으로 8줄을 붙여 넣으면 됩니다.

```
q011 | 정확성: 맞음 | 충실도: 예 | 답변 관련성: 예
```

---

## 1. q025

**질문**: Which CV joint improves on the six-ball cage design by guiding the balls on non-circular tracks, and where is it typically used?

**기준 문장 (평가셋)**:
- `en_cv_joint`: The Birfield joint is a type of constant-velocity joint based on the Rzeppa joint but confines the travel of the six balls using elliptical tracks.
- `en_cv_joint`: They have improved efficiency and are widely used in modern cars for the outboard driveshaft joints.

**답변**: The Birfield joint improves on the six-ball cage design by guiding the balls on elliptical tracks [en_cv_joint#3]. It is typically used in modern cars for the outboard driveshaft joints [en_cv_joint#3].

**답변이 인용한 청크 원문**:

> `[en_cv_joint#3]` The cage is spherical but with ends open, and it typically has six openings around the perimeter. This cage and gear fit into a grooved cup that has a splined and threaded shaft attached to it. Six large steel balls sit inside the cup grooves and fit into the cage openings, nestled in the grooves of the star gear. The output shaft on the cup then runs through the wheel bearing and is secured by the axle nut.
This joint can accommodate the large changes of angle when the front wheels are turned by the steering system; typical Rzeppa joints allow 45°–48° of articulation, while some can give 54°. At the "outboard" end of the driveshaft a slightly different unit is used. The end of the driveshaft is splined and fits into the outer "joint". It is typically held in place by a circlip.

The Birfield joint is a type of constant-velocity joint based on the Rzeppa joint but confines the travel of the six balls using elliptical tracks. They have improved efficiency and are widely used in modern cars for the outboard driveshaft joints. The Birfield joint was developed by Birfield Industries and came into widespread use with the development of front-wheel drive cars such as the Mini.

Tripod jo ...

---

## 2. q021

**질문**: What kind of ready-made bearing unit combines a ball bearing with a spherical outer ring and a housing, and why can the bearing tilt inside the housing?

**기준 문장 (평가셋)**:
- `de_waelzlager`: Sie bestehen aus einem Radial-Rillenkugellager mit balligem (kugelförmigem) Außenring und einem Lagergehäuse.
- `de_waelzlager`: In dem Gehäuse kann das Lager um einige Winkelgrade verstellt werden, um Fluchtungsfehler auszugleichen.

**답변**: A self-aligning ball bearing combines a ball bearing with a spherical outer ring and a housing [en_ball_bearing#8]. The spherical outer ring allows the bearing to tolerate a small angular misalignment resulting from shaft or housing deflections or improper mounting [en_ball_bearing#8]. This design enables the bearing to tilt inside the housing because the spherical raceway accommodates minor misalignments without causing excessive stress or failure [en_ball_bearing#16].

**답변이 인용한 청크 원문**:

> `[en_ball_bearing#8]` While ceramic hybrid bearings use ceramic balls in place of steel ones, they are constructed with steel inner and outer rings; hence the hybrid designation. While the ceramic material itself is stronger than steel, it is also stiffer, which results in increased stresses on the rings, and hence decreased load capacity. Ceramic balls are electrically insulating, which can prevent 'arcing' failures if current should be passed through the bearing. Ceramic balls can also be effective in environments where lubrication may not be available (such as in space applications). In some settings only a thin coating of ceramic is used over a metal ball bearing.
Fully ceramic bearings
These bearings make use of both ceramic balls and race. These bearings are impervious to corrosion and rarely require lubrication if at all. Due to the stiffness and hardness of the balls and race these bearings are noisy at high speeds. The stiffness of the ceramic makes these bearings brittle and liable to crack under load or impact. Because both ball and race are of similar hardness, wear can lead to chipping at high speeds of both the balls and the race, which can cause sparking.
Self-aligning
Self-aligning ball  ...

> `[en_ball_bearing#16]` Bearing manufacturers supply tolerances for the fit of the shaft and the housing so that this can be achieved. The material and hardness may also be specified.
Fittings that are not allowed to slip are made to diameters that prevent slipping and consequently the mating surfaces cannot be brought into position without force. For small bearings this is best done with a press because tapping with a hammer damages both bearing and shaft, while for large bearings the necessary forces are so great that there is no alternative to heating one part before fitting, so that thermal expansion allows a temporary sliding fit.

If a shaft is supported by two bearings, and the center-lines of rotation of these bearings are not the same, then large forces are exerted on the bearing, which may destroy it. Some very small amount of misalignment is acceptable, and how much depends on type of bearing. For bearings that are specifically made to be 'self-aligning', acceptable misalignment is between 1.5 and 3 degrees of arc. Bearings that are not designed to be self-aligning can accept misalignment of only 2–10 minutes of arc (0.033-0.166 degrees) .

In general, ball bearings are used in most application ...

---

## 3. q031

**질문**: Welche Kräfte nimmt ein Festlager auf und was gilt dagegen für ein Loslager?

**기준 문장 (평가셋)**:
- `de_waelzlager`: Das Festlager nimmt also sowohl Radial- als auch Axialkräfte auf.
- `de_waelzlager`: Vom Loslager werden keine Axialkräfte aufgenommen.

**답변**: Ein Festlager nimmt sowohl Radial- als auch Axialkräfte auf. Ein Loslager kann im Gegensatz dazu in axialer Richtung wandern und nimmt daher keine Axialkräfte auf [de_waelzlager#32].

**답변이 인용한 청크 원문**:

> `[de_waelzlager#32]` Die Lageranordnungen berücksichtigen, dass sich das zu lagernde Element (Welle, Achse, …) bei Erwärmung ausdehnt. Bis auf die angestellte Lagerung wird die Wärmedehnung zugelassen, ohne dass sich dabei die Lager verspannen. Bei der Wahl der Anordnung müssen zudem auch die Fertigungstoleranzen berücksichtigt werden.

Bei der klassischen Fest-Los-Lagerung ist eines der Lager verschiebbar und das andere fixiert. Das Festlager ist so auf dem zu lagernden Element montiert, dass es sich nicht in axialer Richtung verschieben kann. Das Festlager nimmt also sowohl Radial- als auch Axialkräfte auf. Wie groß die maximal aufnehmbare Axialkraft sein kann, hängt von der Ausführung dieses Lagers ab.
Das Loslager kann im Gegensatz zum Festlager in axialer Richtung wandern. Vom Loslager werden keine Axialkräfte aufgenommen.

Bei dieser Art der Lagerung nimmt jedes der beiden Lager die axiale Kraft in jeweils nur einer Richtung auf. Bei der schwimmenden Lagerung wird ein Axialspiel zwischen den inneren oder äußeren Laufringen der beiden Lager vorgesehen, um die Wärmedehnung kompensieren zu können und eine Verspannung der Lager zu vermeiden. Bei der angestellten Lagerung werden Schrägkugellager oder  ...

---

## 4. q015

**질문**: 앞바퀴 구동 차에서 조향할 때 큰 각도로 꺾이는 구동축 바깥쪽 조인트의 대표 형식과 허용 각도는 어느 정도인가요?

**기준 문장 (평가셋)**:
- `en_cv_joint`: This joint can accommodate the large changes of angle when the front wheels are turned by the steering system; typical Rzeppa joints allow 45°–48° of articulation, while some can give 54°.
- `de_homokinetisches_gelenk`: Es zeichnet sich durch großen Auslenkwinkel von bis zu 46 Grad, relativ einfache Fertigung und gute Lebensdauer aus.

**답변**: 앞바퀴 구동 차에서 조향할 때 큰 각도로 꺾이는 구동축 바깥쪽 조인트의 대표 형식은 Birfield 조인트입니다. 이 조인트는 Rzeppa 조인트를 기반으로 하며, 6개의 공을 타원형 궤도에 제한하여 효율을 향상시킵니다. 허용 각도는 일반적으로 45°–48°이며, 일부 모델에서는 54°까지 가능합니다 [en_cv_joint#3].

**답변이 인용한 청크 원문**:

> `[en_cv_joint#3]` The cage is spherical but with ends open, and it typically has six openings around the perimeter. This cage and gear fit into a grooved cup that has a splined and threaded shaft attached to it. Six large steel balls sit inside the cup grooves and fit into the cage openings, nestled in the grooves of the star gear. The output shaft on the cup then runs through the wheel bearing and is secured by the axle nut.
This joint can accommodate the large changes of angle when the front wheels are turned by the steering system; typical Rzeppa joints allow 45°–48° of articulation, while some can give 54°. At the "outboard" end of the driveshaft a slightly different unit is used. The end of the driveshaft is splined and fits into the outer "joint". It is typically held in place by a circlip.

The Birfield joint is a type of constant-velocity joint based on the Rzeppa joint but confines the travel of the six balls using elliptical tracks. They have improved efficiency and are widely used in modern cars for the outboard driveshaft joints. The Birfield joint was developed by Birfield Industries and came into widespread use with the development of front-wheel drive cars such as the Mini.

Tripod jo ...

---

## 5. q027

**질문**: Which groove design is used in hydrodynamic plain bearings for particularly quiet computer fans?

**기준 문장 (평가셋)**:
- `de_gleitlager`: Eingesetzt wird die spiralförmige Nutung etwa bei besonders leise laufenden Computerlüftern.
- `de_gleitlager`: Heute werden auch hydrodynamische Gleitlager mit spiralförmiger Nutung (engl. spiral groove bearing) eingesetzt, bei welchen das Schmiermittel bei rotierender Welle durch die Nut von außen zugeführt und ins Zentrum des Lagers befördert wird (Spiralrillenlager).
- `en_plain_bearing`: Most plain bearings have a plain inner surface; however, some are grooved, such as spiral groove bearing.

**답변**: NO_ANSWER

**답변이 인용한 청크**: 없음

---

## 6. q032

**질문**: Warum verschleißt ein hydrodynamisches Gleitlager beim Anfahren besonders stark?

**기준 문장 (평가셋)**:
- `de_gleitlager`: Beim Anlauf der Welle entsteht zunächst Mischreibung.
- `de_gleitlager`: Mit zunehmender Drehzahl wird der Schmierstoff durch die Bewegung der Welle in den Spalt zwischen Welle und Lagerbuchse gezogen.
- `en_lubrication`: This design of bearing may wear when started, stopped or reversed, as the lubricant film breaks down.

**답변**: Ein hydrodynamisches Gleitlager verschleißt beim Anfahren besonders stark, weil zu Beginn nur ein unvollständiger oder fehlender Schmierfilm vorhanden ist, was zu Mischreibung führt. Bei Mischreibung berühren sich die Oberflächen direkt, wodurch Mikroskopische Unebenheiten sich verhaken und ein erhöhter Reibungswiderstand entsteht. Dieser direkte Kontakt führt zu Verschleiß, da Material von den Oberflächen abgetragen wird. [de_gleitlager#2][de_gleitlager#7]

**답변이 인용한 청크 원문**:

> `[de_gleitlager#2]` Im Gegensatz zum hydrodynamischen Gleitlager, bei dem der Schmierfilm durch die Relativbewegung der Welle selbst erzeugt wird, ist das hydrostatische Lager unabhängig von Bewegung und Belastung des Lagers.

Folgende Reibungszustände sind möglich: Festkörperreibung, Mischreibung oder Flüssigkeitsreibung.

Festkörperreibung, auch Trockenreibung genannt, tritt auf, wenn zwei feste Oberflächen direkt aufeinander gleiten, ohne dass ein Schmiermittel zwischen ihnen vorhanden ist. In einem Gleitlager, das unter Bedingungen der Festkörperreibung arbeitet, ist kein flüssiger oder gasförmiger Schmierfilm vorhanden, um die Reibung zwischen der Welle und dem Lager zu reduzieren.

Direkter Kontakt: Die Oberflächen von Welle und Lagerbuchse berühren sich direkt. Mikroskopische Unebenheiten und Asperitäten (Spitzen und Täler) auf den Oberflächen verhaken sich ineinander.
Reibungswiderstand: Um die Bewegung zu initiieren oder aufrechtzuerhalten, muss eine Kraft aufgebracht werden, die groß genug ist, um die Verhakungen der Asperitäten zu überwinden. Dies führt zu einem hohen Reibungswiderstand.
Verschleiß: Die direkte Interaktion zwischen den Oberflächen führt zu Abrieb, wodurch Material von den O ...

> `[de_gleitlager#7]` Geringer Verschleiß: Da es keinen direkten Kontakt zwischen den Gleitflächen gibt, ist der Verschleiß minimal.
Geringe Wärmeentwicklung: Die Reibungswärme ist aufgrund der niedrigen Reibungskoeffizienten gering.
Lange Lebensdauer: Die Komponenten des Lagers haben aufgrund der geringen Reibung und des geringen Verschleißes eine längere Lebensdauer.
Geringer Energieverlust: Die Effizienz des Systems ist höher, da weniger Energie zur Überwindung der Reibung benötigt wird.

Drehzahl: Für die Aufrechterhaltung eines hydrodynamischen Schmierfilms ist eine Mindestdrehzahl erforderlich. Unterhalb dieser Drehzahl kann es zu Mischreibung kommen.
Belastung: Die Belastung muss innerhalb der Tragfähigkeit des Schmierfilms liegen, um den hydrodynamischen Zustand aufrechtzuerhalten.
Schmiermittel: Die Viskosität und die Qualität des Schmiermittels müssen geeignet sein, um einen stabilen Schmierfilm über den gesamten Betriebsbereich hinweg zu gewährleisten.

Start- und Stoppvorgänge: Beim Anfahren und Anhalten der Maschine kann es zu einem kurzzeitigen Zustand der Mischreibung kommen, bevor der volle hydrodynamische Schmierfilm aufgebaut ist.
Schmiermittelauswahl: Die richtige Auswahl des Schmierm ...

---

## 7. q010

**질문**: 오토바이 앞 포크에서 오일과 공기가 새지 않도록 막는 데 쓰는 밀봉 부품은 무엇인가요?

**기준 문장 (평가셋)**:
- `de_wellendichtring`: Entgegen ihrem ursprünglichen Einsatzzweck verwendet man RWDR auch als Gabeldichtring bei Motorrädern, um Austreten von Öl und Luft zwischen den Stand- und Tauchrohren zu verhindern und damit die Funktion des in der Gabel integrierten Dämpfers sicherzustellen.

**답변**: 오토바이 앞 포크에서 오일과 공기가 새지 않도록 막는 데 쓰는 밀봉 부품은 개스킷 또는 기계적 패킹입니다. [ko_seal#0] 이는 압력을 가두고 오염 물질을 배제하여 시스템을 밀봉하는 데 사용되며, 포크와 같은 기계 시스템에서 흔히 사용됩니다. [ko_seal#1] 또한, 스타팅 박스(스터핑 박스)는 압력 시스템에서 유체 누출을 방지하는 데 사용되며, 이는 포크의 밀봉에 유사한 역할을 할 수 있습니다. [ko_seal#1]

**답변이 인용한 청크 원문**:

> `[ko_seal#0]` 씰(seal)은 누출(예: 펌핑 시스템에서)을 방지하고, 압력을 가두거나, 오염 물질을 배제하여 시스템, 메커니즘 또는 기타 재료를 서로 결합하는 데 도움이 되는 장치 또는 재료이다. 씰의 효과는 밀봉제의 경우 접착력에, 개스킷의 경우 압축력에 따라 달라진다. 씰은 화학, 수자원 공급, 제지 생산, 식품 가공 및 기타 여러 응용 분야를 포함한 광범위한 산업에서 펌프에 설치된다.
정지 씰은 '패킹'이라고도 불린다.
씰 유형:

유도 밀봉 또는 캡 밀봉
접착제, 밀봉제
보독 씰, 의료용으로 특화된 가스 밀봉 와셔
본드 씰, 다우티 씰 또는 다우티 와셔라고도 불린다. 나사 또는 볼트의 진입점에서 밀봉을 제공하는 데 널리 사용되는 일체형 개스킷이 있는 와셔의 일종이다.
브리지먼 씰, 저압원에서 고압 저장소를 생성하는 피스톤 밀봉 메커니즘
분할 씰은 다양한 기계 시스템에서 효율성과 편의성을 향상시키도록 설계된 혁신적인 밀봉 솔루션이다. 이 씰은 기존 씰과 관련된 문제를 해결하도록 특별히 설계되어 향상된 설치, 유지 보수 및 작동 이점을 제공한다.
마개
압축 씰 피팅
다이어프램 씰
강자성 유체 씰
개스킷 또는 기계적 패킹
플랜지 개스킷
O링
O링 보스 씰
피스톤 링
유리-금속 밀봉
유리-세라믹-금속 밀봉

> `[ko_seal#1]` 개스킷 또는 기계적 패킹
플랜지 개스킷
O링
O링 보스 씰
피스톤 링
유리-금속 밀봉
유리-세라믹-금속 밀봉
열 밀봉
호스 커플링, 다양한 유형의 호스 커플링
헤르메틱 씰
정수 씰
유체역학 씰
팽창식 씰 세 가지 기본 작동 방향(축 방향, 방사형 내측 방향, 방사형 외측 방향)으로 팽창 및 수축하는 씰이다. 이러한 각 팽창 방향은 팽창 높이 및 씰이 통과할 수 있는 중심선 굽힘 반경과 같은 측정값에 대한 자체 성능 매개변수 세트를 갖는다. 팽창식 씰은 어려운 밀봉 문제가 있는 수많은 응용 분야에 사용할 수 있다.
미로 씰 액체가 흐르도록 구불구불한 경로를 만드는 씰
뚜껑 (용기)
회전면 기계적 씰
면 씰
플러그
방사형 샤프트 씰
트랩 (배관) (사이펀 트랩)
스터핑 박스 (기계적 패킹)
와이퍼 씰
건식 가스 씰

---

## 8. q017

**질문**: What stops the conical rollers of a tapered bearing from being squeezed out under load?

**기준 문장 (평가셋)**:
- `en_tapered_roller_bearing`: The rollers are stabilized and restrained by a flange on the inner ring, against which their large end slides, which stops the rollers from popping out due to the "pumpkin seed effect" of their conical shape.

**답변**: The flange on the inner ring stops the conical rollers from being squeezed out under load, as it provides a surface against which the large end of the rollers slides, preventing them from popping out due to the "pumpkin seed effect" of their conical shape [en_tapered_roller_bearing#0].

**답변이 인용한 청크 원문**:

> `[en_tapered_roller_bearing#0]` Tapered roller bearings are rolling element bearings that can support axial forces (i.e., they are good thrust bearings) as well as radial forces.

The inner and outer ring raceways are segments of cones and the rollers are tapered so that the conical surfaces of the raceways, and the roller axes, if projected, would all meet at a common point on the main axis of the bearing. This geometry makes the motion of the cones remain coaxial, with no sliding motion between the raceways and the outside diameter of the rollers.
This conical geometry creates a linear contact patch which permits greater loads to be carried than with spherical (ball) bearings, which have point contact. The geometry means that the tangential speeds of the surfaces of each of the rollers are the same as their raceways along the whole length of the contact patch and no differential scrubbing occurs.
The rollers are stabilized and restrained by a flange on the inner ring, against which their large end slides, which stops the rollers from popping out due to the "pumpkin seed effect" of their conical shape.
The larger the half angles of these cones the larger the axial force that the bearing can sustain.
Tapered roll ...

---
