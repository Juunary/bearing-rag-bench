### 1. overall / mono / cross (n=45 / 21 / 24)

| config | Recall@5 | MRR@10 | nDCG@10 | nDCG@10 95% CI | nDCG mono | nDCG cross |
|---|---|---|---|---|---|---|
| bm25_whitespace | 0.404 | 0.430 | 0.421 | 0.294 - 0.549 | 0.786 | 0.101 |
| bm25_kiwi | 0.411 | 0.425 | 0.410 | 0.283 - 0.538 | 0.781 | 0.086 |
| bm25_subword | 0.400 | 0.428 | 0.422 | 0.289 - 0.555 | 0.798 | 0.093 |
| dense_bge_m3_exact | 0.511 | 0.505 | 0.510 | 0.399 - 0.619 | 0.697 | 0.345 |
| dense_bge_m3 | 0.511 | 0.505 | 0.510 | 0.399 - 0.619 | 0.697 | 0.345 |
| hybrid_rrf | 0.422 | 0.429 | 0.427 | 0.299 - 0.559 | 0.808 | 0.093 |
| hybrid_rrf_rerank | 0.615 | 0.702 | 0.631 | 0.524 - 0.732 | 0.835 | 0.453 |

### 2. latency (ms per query) and index build

| config | p50 | p95 | index build (s) |
|---|---|---|---|
| bm25_whitespace | 0.09 | 0.12 | 0.04 |
| bm25_kiwi | 0.16 | 0.64 | 1.79 |
| bm25_subword | 0.20 | 0.26 | 10.89 |
| dense_bge_m3_exact | 10.83 | 13.72 | 0.00 |
| dense_bge_m3 | 8.61 | 10.46 | 0.00 |
| hybrid_rrf | 10.60 | 13.82 | 1.88 |
| hybrid_rrf_rerank | 168.52 | 174.32 | 2.15 |

### 3. complete failures of the best config (Recall@5 = 0)

9 of 45 queries

- q002 (ko->de): gold ['de_waelzlager#5'] | top-1 ko_bearing#0 | 요즘 구름 베어링의 케이지는 보통 무슨 소재로 만들고, 그 이유는 무엇인가요?
- q005 (ko->en): gold ['en_rolling_element_bearing#7', 'en_rolling_element_bearing#8'] | top-1 ko_ball_bearing#11 | 베어링의 수명이나 하중 용량을 제한하는 세 가지 대표 원인은 무엇인가요?
- q007 (ko->de): gold ['de_waelzlager#6'] | top-1 ko_lubrication#0 | 구름 베어링에 가장 흔히 쓰는 강종의 탄소와 크롬 함량은 어느 정도인가요?
- q010 (ko->de): gold ['de_wellendichtring#1'] | top-1 ko_seal#0 | 오토바이 앞 포크에서 오일과 공기가 새지 않도록 막는 데 쓰는 밀봉 부품은 무엇인가요?
- q021 (en->de): gold ['de_waelzlager#32', 'de_waelzlager#33'] | top-1 en_ball_bearing#8 | What kind of ready-made bearing unit combines a ball bearing with a sp
- q028 (en->de): gold ['de_waelzlager#33'] | top-1 en_ball_bearing#2 | Which kind of bearing do simple bicycles use in the wheels, bottom bra
- q029 (en->de): gold ['de_waelzlager#31'] | top-1 en_bearing_mechanical#12 | To what temperature may a bearing be heated for shrink-fit mounting on
- q032 (de->de): gold ['de_gleitlager#0', 'de_gleitlager#1', 'en_lubrication#1'] | top-1 de_hydrodynamisches_gleitlager#5 | Warum verschleißt ein hydrodynamisches Gleitlager beim Anfahren besond
- q041 (de->en): gold ['en_needle_roller_bearing#0'] | top-1 de_nadellager#0 | Wie viele Nadellager stecken typischerweise in der Kardanwelle eines F

### 4. dense better than RRF hybrid (gold chunks in top 5)

dense > hybrid: 10 queries; hybrid > dense: 4 queries
dense > hybrid groups: ['de->ko', 'en->ko', 'ko->de', 'ko->en'] | cross: 10 of 10

### 5. paired bootstrap of nDCG@10 differences (same queries, 10000 draws, seed 42)

| A - B | mean diff | 95% CI | A better in n queries |
|---|---|---|---|
| dense_bge_m3 - bm25_kiwi | +0.099 | -0.012 .. +0.211 | 18 / 11 (worse) |
| hybrid_rrf - dense_bge_m3 | -0.083 | -0.188 .. +0.021 | 11 / 14 (worse) |
| hybrid_rrf_rerank - dense_bge_m3 | +0.122 | +0.047 .. +0.203 | 17 / 6 (worse) |
| hybrid_rrf_rerank - hybrid_rrf | +0.205 | +0.101 .. +0.314 | 21 / 5 (worse) |
| bm25_kiwi - bm25_whitespace | -0.011 | -0.038 .. +0.009 | 3 / 3 (worse) |
| bm25_subword - bm25_whitespace | +0.001 | -0.030 .. +0.030 | 6 / 5 (worse) |

### 6. language of the top-1 chunk in complete failures of the best config

top-1 chunk is in the question language in 9 of 9 failures: [('q002', 'ko->de', 'ko'), ('q005', 'ko->en', 'ko'), ('q007', 'ko->de', 'ko'), ('q010', 'ko->de', 'ko'), ('q021', 'en->de', 'en'), ('q028', 'en->de', 'en'), ('q029', 'en->de', 'en'), ('q032', 'de->de', 'de'), ('q041', 'de->en', 'de')]

### 7. HNSW vs exact: identical rankings?

44 of 45 queries have identical top-10 lists
