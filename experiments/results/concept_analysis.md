# Concept-mediated retrieval (data/concepts, 26 pages) against the best setting

## PDF questions (48, table-header chunks)

### 1. Per setting

| setting | R@5 | MRR@10 | nDCG@10 | matched queries (alias / dense) | pool additions, mean | p50 ms |
|---|---|---|---|---|---|---|
| baseline (x13) | 0.882 | 0.850 | 0.831 | - | 0.0 | 196 |
| c_pool | 0.882 | 0.850 | 0.831 | 43 (42 / 1) | 1.1 | 220 |
| c_pool_query | 0.825 | 0.770 | 0.765 | 43 (42 / 1) | 1.1 | 224 |
| c_rrf_query | 0.825 | 0.770 | 0.768 | 43 (42 / 1) | 0.0 | 218 |

### 2. nDCG@10, variant - baseline (95% interval: question-level / document-cluster)

| variant | subset | n | mean diff | question CI | cluster CI | better/worse/tie |
|---|---|---|---|---|---|---|
| c_pool | all | 48 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/48 |
| c_pool | matched | 43 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/43 |
| c_pool | unmatched | 5 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/5 |
| c_pool_query | all | 48 | -0.066 | -0.112 .. -0.023 | -0.111 .. -0.027 | 2/18/28 |
| c_pool_query | matched | 43 | -0.074 | -0.124 .. -0.026 | -0.127 .. -0.029 | 2/18/23 |
| c_pool_query | unmatched | 5 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/5 |
| c_rrf_query | all | 48 | -0.064 | -0.109 .. -0.021 | -0.105 .. -0.027 | 2/18/28 |
| c_rrf_query | matched | 43 | -0.071 | -0.121 .. -0.025 | -0.121 .. -0.029 | 2/18/23 |
| c_rrf_query | unmatched | 5 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/5 |

### 3. Matched queries

| qid | concepts (how) | baseline nDCG | c_pool | c_pool_query | c_rrf_query |
|---|---|---|---|---|---|
| pdf001 | bearing_life (alias: life factor; 수명 계수), bearing_material (alias: bearing steel; M-50; 베어링강; 베어링 강) | 0.950 | 0.950 | 0.924 | 0.924 |
| pdf002 | cv_joint_driveline (alias: propeller shaft) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf003 | bearing_life (alias: L10 life; Lundberg-Palmgren; life factor; Lebensdauerfaktor) | 0.213 | 0.213 | 0.000 | 0.000 |
| pdf004 | deep_groove_ball_bearing (alias: deep groove ball bearing; 깊은 홈 볼 베어링; 깊은홈 볼베어링) | 0.631 | 0.631 | 0.631 | 0.631 |
| pdf005 | hertzian_contact (alias: Hertz stress) | 0.760 | 0.760 | 0.760 | 0.760 |
| pdf006 | bearing_life (alias: Lebensdauer) | 0.950 | 0.950 | 0.627 | 0.627 |
| pdf007 | bearing_life (alias: Lundberg-Palmgren), hertzian_contact (alias: maximum Hertz stress; 헤르츠 응력) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf008 | bearing_material (alias: M-50; M50 NiL; VIM-VAR), hertzian_contact (alias: maximum Hertz stress) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf009 | bearing_material (alias: material factor) | 0.840 | 0.840 | 0.840 | 0.840 |
| pdf010 | bearing_life (alias: bearing life) | 1.000 | 1.000 | 0.950 | 0.950 |
| pdf012 | hertzian_contact (dense 0.61) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf013 | surface_fatigue (alias: spalling) | 0.733 | 0.733 | 0.733 | 0.733 |
| pdf015 | bearing_life (alias: fatigue life; L10; Ermüdungslebensdauer) | 0.920 | 0.920 | 0.877 | 0.877 |
| pdf016 | bearing_life (alias: bearing life) | 1.000 | 1.000 | 0.631 | 0.631 |
| pdf018 | bearing_life (alias: Lebensdauer) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf019 | cylindrical_roller_bearing (alias: crowned roller), hertzian_contact (alias: contact stress) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf020 | cylindrical_roller_bearing (alias: cylindrical roller bearing; roller profile; 원통 롤러 베어링; 원통롤러 베어링), hertzian_contact (alias: maximum Hertz stress; 헤르츠 응력) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf021 | bearing_life (alias: Lundberg-Palmgren; Lebensdauer), cylindrical_roller_bearing (alias: Zylinderrolle) | 0.631 | 0.631 | 0.315 | 0.315 |
| pdf022 | cylindrical_roller_bearing (alias: cylindrical roller bearing; crowned roller) | 0.964 | 0.964 | 0.912 | 0.912 |
| pdf023 | bearing_life (alias: L10 life; Lundberg-Palmgren) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf025 | cylindrical_roller_bearing (alias: cylindrical roller bearing) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf026 | cylindrical_roller_bearing (alias: cylindrical roller bearing; 원통 롤러 베어링; 원통롤러 베어링), slip_smearing (alias: smearing; 스미어링) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf027 | cylindrical_roller_bearing (alias: cylindrical roller bearing; Zylinderrollenlager; vollrollig), slip_smearing (alias: Anschmierungen) | 0.655 | 0.655 | 0.311 | 0.311 |
| pdf028 | preload_clearance (alias: radial clearance), slip_smearing (alias: smearing) | 1.000 | 1.000 | 0.387 | 0.387 |
| pdf029 | cylindrical_roller_bearing (alias: cylindrical roller bearing; 원통 롤러 베어링; 원통롤러 베어링), lubricant_film (alias: viscosity; 점도), slip_smearing (alias: smearing; 스미어링) | 0.924 | 0.924 | 0.907 | 0.907 |
| pdf030 | cylindrical_roller_bearing (alias: vollrollig) | 0.870 | 0.870 | 0.480 | 0.594 |
| pdf031 | cylindrical_roller_bearing (alias: cylindrical roller bearing; Zylinderrollenlager; vollrollig), slip_smearing (alias: Schlupf; Anschmierungen) | 0.000 | 0.000 | 0.000 | 0.000 |
| pdf032 | cylindrical_roller_bearing (alias: cylindrical roller bearing), slip_smearing (alias: smearing) | 0.682 | 0.682 | 0.662 | 0.662 |
| pdf033 | cylindrical_roller_bearing (alias: cylindrical roller bearing; 원통 롤러 베어링; 원통롤러 베어링), slip_smearing (alias: smearing; 스미어링) | 0.877 | 0.877 | 0.725 | 0.725 |
| pdf035 | cylindrical_roller_bearing (alias: vollrollig), plain_bearing (alias: sliding bearing; Gleitlager) | 0.631 | 0.631 | 0.500 | 0.500 |
| pdf036 | radial_shaft_seal (alias: RWDR) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf037 | radial_shaft_seal (alias: radial shaft seal; Simmerring; Simmerring) | 0.760 | 0.760 | 0.860 | 0.860 |
| pdf038 | radial_shaft_seal (alias: radial shaft seal) | 0.760 | 0.760 | 0.760 | 0.760 |
| pdf039 | radial_shaft_seal (alias: radial shaft seal; Radial-Wellendichtring) | 0.356 | 0.356 | 0.315 | 0.315 |
| pdf040 | cage (alias: retainer), deep_groove_ball_bearing (alias: deep groove ball bearing), radial_shaft_seal (alias: RWDR) | 0.500 | 0.500 | 0.500 | 0.500 |
| pdf041 | radial_shaft_seal (alias: radial shaft seal) | 0.544 | 0.544 | 0.924 | 0.924 |
| pdf042 | radial_shaft_seal (alias: radial shaft seal; Radial-Wellendichtring), sealing_lip (alias: seal lip; Dichtlippe) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf043 | radial_shaft_seal (alias: RWDR) | 0.500 | 0.500 | 0.315 | 0.315 |
| pdf044 | radial_shaft_seal (alias: radial shaft seal; Radial-Wellendichtring) | 1.000 | 1.000 | 0.631 | 0.631 |
| pdf045 | plain_bearing (alias: sliding bearing; 미끄럼 베어링) | 0.674 | 0.674 | 0.674 | 0.674 |
| pdf046 | plain_bearing (alias: plain bearing) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf047 | plain_bearing (alias: sliding bearing; Kunststoffgleitlager) | 1.000 | 1.000 | 1.000 | 1.000 |
| pdf048 | plain_bearing (alias: sliding bearing; 미끄럼 베어링) | 1.000 | 1.000 | 1.000 | 1.000 |

### 4. Concepts

| concept | chunks | queries matched |
|---|---|---|
| bearing_life | 220 | 10 |
| slip_smearing | 177 | 7 |
| raceway | 155 | 0 |
| tribology | 139 | 0 |
| lubricant_film | 129 | 1 |
| hertzian_contact | 110 | 6 |
| radial_shaft_seal | 108 | 9 |
| plain_bearing | 106 | 5 |
| cylindrical_roller_bearing | 94 | 13 |
| preload_clearance | 68 | 1 |
| shaft_counterface | 61 | 0 |
| seal_leakage | 59 | 0 |
| cage | 56 | 1 |
| grease | 55 | 0 |
| sealing_lip | 55 | 1 |
| surface_fatigue | 53 | 1 |
| bearing_material | 52 | 3 |
| deep_groove_ball_bearing | 45 | 2 |
| bearing_fit | 32 | 0 |
| angular_contact_ball_bearing | 30 | 0 |
| cv_joint_driveline | 26 | 1 |
| wear_debris_analysis | 22 | 0 |
| brinelling | 19 | 0 |
| tapered_roller_bearing | 19 | 0 |
| fretting | 16 | 0 |
| needle_roller_bearing | 12 | 0 |

## v2 questions (90, wiki + pdf chunks)

### 1. Per setting

| setting | R@5 | MRR@10 | nDCG@10 | matched queries (alias / dense) | pool additions, mean | p50 ms |
|---|---|---|---|---|---|---|
| baseline (x13) | 0.884 | 0.909 | 0.869 | - | 0.0 | 189 |
| c_pool | 0.884 | 0.909 | 0.869 | 65 (49 / 16) | 1.3 | 212 |
| c_pool_query | 0.846 | 0.893 | 0.859 | 65 (49 / 16) | 1.3 | 214 |
| c_rrf_query | 0.846 | 0.893 | 0.860 | 65 (49 / 16) | 0.0 | 210 |

### 2. nDCG@10, variant - baseline (95% interval: question-level / document-cluster)

| variant | subset | n | mean diff | question CI | cluster CI | better/worse/tie |
|---|---|---|---|---|---|---|
| c_pool | all | 90 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/90 |
| c_pool | matched | 65 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/65 |
| c_pool | unmatched | 25 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/25 |
| c_pool_query | all | 90 | -0.010 | -0.043 .. +0.022 | -0.042 .. +0.021 | 11/17/62 |
| c_pool_query | matched | 65 | -0.014 | -0.060 .. +0.031 | -0.056 .. +0.030 | 11/17/37 |
| c_pool_query | unmatched | 25 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/25 |
| c_rrf_query | all | 90 | -0.009 | -0.042 .. +0.023 | -0.041 .. +0.022 | 11/17/62 |
| c_rrf_query | matched | 65 | -0.012 | -0.058 .. +0.033 | -0.055 .. +0.031 | 11/17/37 |
| c_rrf_query | unmatched | 25 | +0.000 | +0.000 .. +0.000 | +0.000 .. +0.000 | 0/0/25 |

### 3. Matched queries

| qid | concepts (how) | baseline nDCG | c_pool | c_pool_query | c_rrf_query |
|---|---|---|---|---|---|
| q001 | plain_bearing (alias: journal bearing; 저널 베어링) | 0.760 | 0.760 | 0.760 | 0.760 |
| q002 | cage (alias: 케이지) | 0.500 | 0.500 | 1.000 | 1.000 |
| q003 | cage (alias: cage; 케이지) | 0.860 | 0.860 | 0.760 | 0.760 |
| q004 | plain_bearing (dense 0.56) | 0.863 | 0.863 | 0.740 | 0.838 |
| q005 | bearing_life (dense 0.67) | 0.760 | 0.760 | 0.760 | 0.760 |
| q007 | bearing_material (dense 0.62) | 1.000 | 1.000 | 1.000 | 1.000 |
| q008 | needle_roller_bearing (alias: needle roller bearing; 바늘 롤러 베어링) | 0.639 | 0.639 | 0.558 | 0.558 |
| q009 | grease (alias: grease; 그리스) | 0.950 | 0.950 | 0.950 | 0.950 |
| q012 | tribology (alias: 구름 마찰) | 0.760 | 0.760 | 0.760 | 0.760 |
| q013 | tribology (alias: adhesive wear) | 0.760 | 0.760 | 0.760 | 0.760 |
| q014 | surface_fatigue (dense 0.59) | 0.633 | 0.633 | 0.362 | 0.362 |
| q015 | cv_joint_driveline (alias: drive shaft; 구동축) | 0.875 | 0.875 | 0.907 | 0.907 |
| q016 | tapered_roller_bearing (dense 0.60) | 0.860 | 0.860 | 0.839 | 0.839 |
| q017 | tapered_roller_bearing (dense 0.72) | 1.000 | 1.000 | 1.000 | 1.000 |
| q018 | brinelling (alias: dent), plain_bearing (alias: plain bearing; bushing) | 0.333 | 0.333 | 1.000 | 1.000 |
| q019 | grease (alias: grease) | 1.000 | 1.000 | 1.000 | 1.000 |
| q020 | grease (alias: lithium grease) | 1.000 | 1.000 | 1.000 | 1.000 |
| q021 | bearing_material (dense 0.60) | 1.000 | 1.000 | 1.000 | 1.000 |
| q022 | bearing_life (dense 0.58) | 0.000 | 0.000 | 0.000 | 0.000 |
| q023 | plain_bearing (alias: sleeve bearing) | 0.950 | 0.950 | 0.950 | 0.950 |
| q024 | brinelling (alias: false brinelling), fretting (alias: fretting) | 1.000 | 1.000 | 1.000 | 1.000 |
| q025 | cage (alias: cage), cv_joint_driveline (alias: constant-velocity joint) | 1.000 | 1.000 | 1.000 | 1.000 |
| q026 | tapered_roller_bearing (dense 0.55) | 0.978 | 0.978 | 0.936 | 0.936 |
| q027 | plain_bearing (alias: plain bearing; journal bearing) | 0.639 | 0.639 | 0.639 | 0.639 |
| q028 | plain_bearing (dense 0.55) | 1.000 | 1.000 | 1.000 | 1.000 |
| q030 | seal_leakage (alias: oil leak) | 1.000 | 1.000 | 1.000 | 1.000 |
| q031 | plain_bearing (dense 0.60) | 1.000 | 1.000 | 1.000 | 1.000 |
| q032 | plain_bearing (alias: journal bearing; Gleitlager) | 0.692 | 0.692 | 0.685 | 0.685 |
| q033 | radial_shaft_seal (alias: radial shaft seal; Radial-Wellendichtring), sealing_lip (alias: sealing lip; Dichtlippe) | 0.631 | 0.631 | 1.000 | 1.000 |
| q034 | tribology (alias: Fressen) | 0.431 | 0.431 | 0.500 | 0.500 |
| q035 | grease (alias: lubricating grease; Schmierfett) | 0.982 | 0.982 | 0.982 | 0.982 |
| q037 | bearing_life (alias: Lebensdauer) | 1.000 | 1.000 | 0.315 | 0.315 |
| q039 | lubricant_film (alias: Schmierfilm), plain_bearing (alias: sliding bearing; Gleitlager) | 0.693 | 0.693 | 0.801 | 0.801 |
| q040 | brinelling (alias: true brinelling; false brinelling) | 0.837 | 0.837 | 0.837 | 0.837 |
| q041 | cv_joint_driveline (alias: driveshaft; Kardanwelle), needle_roller_bearing (alias: needle bearing; Nadellager) | 1.000 | 1.000 | 1.000 | 1.000 |
| q042 | plain_bearing (dense 0.59) | 0.655 | 0.655 | 0.728 | 0.728 |
| q043 | radial_shaft_seal (alias: radial shaft seal; Radial-Wellendichtring) | 1.000 | 1.000 | 1.000 | 1.000 |
| q047 | lubricant_film (alias: Stribeck curve; 스트리벡 곡선), plain_bearing (alias: sliding bearing; 미끄럼 베어링) | 1.000 | 1.000 | 1.000 | 1.000 |
| q048 | tribology (alias: 연마 마모) | 0.458 | 0.458 | 0.375 | 0.375 |
| q052 | radial_shaft_seal (alias: oil seal; 오일 씰; 오일씰) | 1.000 | 1.000 | 1.000 | 1.000 |
| q053 | radial_shaft_seal (alias: oil seal; 오일 씰; 오일씰) | 0.627 | 0.627 | 0.860 | 0.860 |
| q054 | angular_contact_ball_bearing (alias: angular contact ball bearing; contact angle; 앵귤러 콘택트 볼 베어링; 접촉각) | 0.867 | 0.867 | 0.867 | 0.867 |
| q055 | bearing_material (alias: ceramic ball; 세라믹 볼) | 0.860 | 0.860 | 0.860 | 0.860 |
| q056 | cage (alias: cage; 케이지) | 1.000 | 1.000 | 0.896 | 0.896 |
| q057 | bearing_fit (dense 0.56) | 1.000 | 1.000 | 1.000 | 1.000 |
| q059 | grease (alias: grease; 그리스) | 0.978 | 0.978 | 0.947 | 0.947 |
| q060 | cv_joint_driveline (alias: drive shaft; 구동축) | 1.000 | 1.000 | 0.500 | 0.500 |
| q061 | preload_clearance (alias: internal clearance) | 1.000 | 1.000 | 1.000 | 1.000 |
| q064 | surface_fatigue (alias: pitting; Pitting) | 1.000 | 1.000 | 1.000 | 1.000 |
| q065 | needle_roller_bearing (alias: needle bearing) | 1.000 | 1.000 | 0.431 | 0.431 |
| q066 | lubricant_film (alias: viscosity), seal_leakage (alias: leakage) | 0.500 | 0.500 | 0.356 | 0.356 |
| q068 | bearing_material (alias: ceramic ball) | 0.860 | 0.860 | 0.860 | 0.860 |
| q069 | grease (alias: grease) | 1.000 | 1.000 | 1.000 | 1.000 |
| q074 | grease (alias: grease; thickener) | 0.978 | 0.978 | 1.000 | 1.000 |
| q075 | cv_joint_driveline (alias: drive shaft) | 1.000 | 1.000 | 1.000 | 1.000 |
| q076 | hertzian_contact (dense 0.63) | 1.000 | 1.000 | 1.000 | 1.000 |
| q078 | bearing_material (alias: silicon nitride; Siliziumnitrid) | 0.860 | 0.860 | 1.000 | 1.000 |
| q079 | plain_bearing (dense 0.56) | 0.860 | 0.860 | 0.950 | 0.950 |
| q080 | bearing_material (alias: bearing steel; 100Cr6; Wälzlagerstahl; 100Cr6) | 1.000 | 1.000 | 1.000 | 1.000 |
| q081 | tribology (alias: abrasive wear) | 1.000 | 1.000 | 1.000 | 1.000 |
| q082 | lubricant_film (alias: oil film) | 1.000 | 1.000 | 1.000 | 1.000 |
| q086 | tribology (alias: sliding friction) | 0.776 | 0.776 | 0.753 | 0.753 |
| q087 | plain_bearing (dense 0.60) | 1.000 | 1.000 | 1.000 | 1.000 |
| q089 | cv_joint_driveline (alias: drive shaft; Antriebswelle) | 0.760 | 0.760 | 0.380 | 0.380 |
| q090 | grease (alias: grease; Fett) | 0.892 | 0.892 | 0.855 | 0.855 |

### 4. Concepts

| concept | chunks | queries matched |
|---|---|---|
| bearing_life | 214 | 3 |
| slip_smearing | 177 | 0 |
| raceway | 155 | 0 |
| tribology | 139 | 6 |
| lubricant_film | 129 | 4 |
| radial_shaft_seal | 108 | 4 |
| plain_bearing | 106 | 13 |
| hertzian_contact | 103 | 1 |
| cylindrical_roller_bearing | 94 | 0 |
| preload_clearance | 68 | 1 |
| shaft_counterface | 61 | 0 |
| seal_leakage | 59 | 2 |
| cage | 56 | 4 |
| grease | 55 | 8 |
| sealing_lip | 55 | 1 |
| surface_fatigue | 53 | 2 |
| bearing_material | 52 | 6 |
| deep_groove_ball_bearing | 41 | 0 |
| bearing_fit | 32 | 1 |
| angular_contact_ball_bearing | 30 | 1 |
| cv_joint_driveline | 25 | 6 |
| wear_debris_analysis | 22 | 0 |
| brinelling | 19 | 3 |
| tapered_roller_bearing | 19 | 3 |
| fretting | 16 | 1 |
| needle_roller_bearing | 12 | 3 |

## Human-written questions (10, cite_refuse_v1)

| variant | refused | top-5 changed | D05 targets in reranker pool | D05 target ranks (top 10) | D05 outcome |
|---|---|---|---|---|---|
| baseline | 5 | - | - | - | refused |
| c_pool | 5 | 1 | 1/5 | r-2022#19=7, htring#0=-, r-2022#28=-, r-2022#40=-, r-2022#43=- | refused |
| c_pool_query | 5 | 9 | 1/5 | r-2022#19=3, htring#0=-, r-2022#28=-, r-2022#40=-, r-2022#43=- | answered |
| c_rrf_query | 5 | 9 | 1/5 | r-2022#19=3, htring#0=-, r-2022#28=-, r-2022#40=-, r-2022#43=- | answered |

Per question (blocked = the answer was replaced by the fixed message):

| qid | baseline | c_pool | c_pool_query | c_rrf_query |
|---|---|---|---|---|
| D01 | answered | answered [angular_contact_ball_bearing] | answered (top-5 changed) [angular_contact_ball_bearing] | answered (top-5 changed) [angular_contact_ball_bearing] |
| D02 | blocked | blocked [cv_joint_driveline] | blocked (top-5 changed) [cv_joint_driveline] | blocked (top-5 changed) [cv_joint_driveline] |
| D03 | answered | answered [grease] | answered (top-5 changed) [grease] | answered (top-5 changed) [grease] |
| D04 | answered | answered (top-5 changed) [wear_debris_analysis] | answered (top-5 changed) [wear_debris_analysis] | answered (top-5 changed) [wear_debris_analysis] |
| D05 | blocked | blocked [radial_shaft_seal, seal_leakage] | answered (top-5 changed) [radial_shaft_seal, seal_leakage] | answered (top-5 changed) [radial_shaft_seal, seal_leakage] |
| D06 | answered | answered [cv_joint_driveline] | answered (top-5 changed) [cv_joint_driveline] | answered (top-5 changed) [cv_joint_driveline] |
| D07 | answered | answered [plain_bearing] | blocked (top-5 changed) [plain_bearing] | blocked (top-5 changed) [plain_bearing] |
| D08 | blocked | blocked | blocked | blocked |
| D09 | blocked | blocked [brinelling] | blocked (top-5 changed) [brinelling] | blocked (top-5 changed) [brinelling] |
| D10 | blocked | blocked [bearing_fit, bearing_life] | blocked (top-5 changed) [bearing_fit, bearing_life] | blocked (top-5 changed) [bearing_fit, bearing_life] |
