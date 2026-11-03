# Retrieval trace: d05_retrieval_trace

Config: `pdfth_x13_rrf_en_dense_en_rerank_en_text.json`

Question: 오일 씰(Oil seal)에서 누유가 지속적으로 발생할 때, 립(Lip) 마모 외에 점검해야 할 샤프트 측 결함 요소는 무엇인가요?

Translated query: When oil leakage persists in an oil seal, what other shaft-side defect factors should be checked besides lip wear?

Served top 5: en_radial_shaft_seal#0, luh-diss-pelzer-2022#45, en_radial_shaft_seal#1, de_wellendichtring#1, luh-diss-pelzer-2022#78

## Translated query

| chunk | BM25 rank | dense rank (cos) | RRF rank | in reranker pool | reranker score | final rank |
|---|---|---|---|---|---|---|
| de_wellendichtring#0 | 35 | 115 (0.508) | 57 | no | -3.020 | - (would be 10) |
| luh-diss-pelzer-2022#19 | 9 | 27 (0.548) | 10 | yes | -2.850 | 7 |
| luh-diss-pelzer-2022#28 | 64 | 134 (0.505) | - | no | -5.969 | - (would be 29) |
| luh-diss-pelzer-2022#40 | 90 | 136 (0.504) | - | no | -5.176 | - (would be 26) |
| luh-diss-pelzer-2022#43 | 361 | 330 (0.466) | - | no | -7.828 | - (would be 31) |
| en_radial_shaft_seal#0 (final top) | 2 | 24 (0.549) | 5 | yes | -0.210 | 1 |
| luh-diss-pelzer-2022#45 (final top) | 11 | 1 (0.623) | 2 | yes | -1.921 | 2 |
| en_radial_shaft_seal#1 (final top) | 23 | 39 (0.537) | 19 | yes | -2.369 | 3 |
| de_wellendichtring#1 (final top) | 3 | 75 (0.521) | 23 | yes | -2.447 | 4 |
| luh-diss-pelzer-2022#78 (final top) | 15 | 3 (0.596) | 3 | yes | -2.549 | 5 |

Cut-offs: RRF takes each part's top 50; reranker pool = RRF top 30; generator reads the final top 5. Reranker score of final rank 5: -2.549.

Query tokens (document frequency in the English chunk texts): when (197), oil (196), leakage (31), persists (0), in (846), an (367), seal (87), what (40), other (217), shaft (234), side (73), defect (5), factors (91), should (74), be (554), checked (1), besides (8), lip (52), wear (170)

| chunk | query tokens present |
|---|---|
| de_wellendichtring#0 | in, seal, shaft, be, lip, wear |
| luh-diss-pelzer-2022#19 | oil, an, seal, other, shaft, side, be, lip |
| luh-diss-pelzer-2022#28 | in, an, seal, shaft, side |
| luh-diss-pelzer-2022#40 | oil, in, seal, factors, be |
| luh-diss-pelzer-2022#43 | in, seal, be |
| en_radial_shaft_seal#0 | oil, in, seal, shaft, side, be, lip, wear |
| luh-diss-pelzer-2022#45 | oil, leakage, in, seal, shaft, side, be |
| en_radial_shaft_seal#1 | in, an, seal, other, shaft, be, lip, wear |
| de_wellendichtring#1 | when, oil, in, seal, shaft, side, should, be, lip |
| luh-diss-pelzer-2022#78 | oil, leakage, in, seal, be, lip |

## Variant: When oil leakage persists in a radial shaft seal, what other shaft-side defect factors should be checked besides lip wear?

| chunk | BM25 rank | dense rank (cos) | RRF rank | in reranker pool | reranker score | final rank |
|---|---|---|---|---|---|---|
| de_wellendichtring#0 | 16 | 51 (0.544) | 32 | no | -1.398 | - (would be 3) |
| luh-diss-pelzer-2022#19 | 7 | 10 (0.586) | 5 | yes | -1.491 | 4 |
| luh-diss-pelzer-2022#28 | 47 | 137 (0.513) | 70 | no | -6.188 | - (would be 30) |
| luh-diss-pelzer-2022#40 | 147 | 124 (0.518) | - | no | -4.613 | - (would be 28) |
| luh-diss-pelzer-2022#43 | 255 | 224 (0.490) | - | no | -6.609 | - (would be 30) |
| en_radial_shaft_seal#0 (final top) | 1 | 5 (0.602) | 1 | yes | 0.666 | 1 |
| de_wellendichtring#1 (final top) | 3 | 30 (0.563) | 9 | yes | -1.305 | 2 |
| luh-diss-pelzer-2022#45 (final top) | 12 | 1 (0.623) | 3 | yes | -1.462 | 3 |
| en_radial_shaft_seal#1 (final top) | 8 | 17 (0.573) | 8 | yes | -1.629 | 5 |

Cut-offs: RRF takes each part's top 50; reranker pool = RRF top 30; generator reads the final top 5. Reranker score of final rank 5: -1.629.

Query tokens (document frequency in the English chunk texts): when (197), oil (196), leakage (31), persists (0), in (846), a (817), radial (316), shaft (234), seal (87), what (40), other (217), side (73), defect (5), factors (91), should (74), be (554), checked (1), besides (8), lip (52), wear (170)

| chunk | query tokens present |
|---|---|
| de_wellendichtring#0 | in, a, radial, shaft, seal, be, lip, wear |
| luh-diss-pelzer-2022#19 | oil, a, radial, shaft, seal, other, side, be, lip |
| luh-diss-pelzer-2022#28 | in, a, shaft, seal, side |
| luh-diss-pelzer-2022#40 | oil, in, a, radial, seal, factors, be |
| luh-diss-pelzer-2022#43 | in, a, radial, seal, be |
| en_radial_shaft_seal#0 | oil, in, a, radial, shaft, seal, side, be, lip, wear |
| de_wellendichtring#1 | when, oil, in, a, radial, shaft, seal, side, should, be, lip |
| luh-diss-pelzer-2022#45 | oil, leakage, in, radial, shaft, seal, side, be |
| luh-diss-pelzer-2022#19 | oil, a, radial, shaft, seal, other, side, be, lip |
| en_radial_shaft_seal#1 | in, a, radial, shaft, seal, other, be, lip, wear |

## Variant: When oil leakage persists in a radial shaft seal, what defects of the shaft surface should be checked besides lip wear?

| chunk | BM25 rank | dense rank (cos) | RRF rank | in reranker pool | reranker score | final rank |
|---|---|---|---|---|---|---|
| de_wellendichtring#0 | 6 | 28 (0.567) | 12 | yes | -0.368 | 2 |
| luh-diss-pelzer-2022#19 | 17 | 7 (0.605) | 8 | yes | -0.581 | 3 |
| luh-diss-pelzer-2022#28 | 64 | 96 (0.525) | - | no | -4.605 | - (would be 30) |
| luh-diss-pelzer-2022#40 | 113 | 190 (0.496) | - | no | -4.473 | - (would be 30) |
| luh-diss-pelzer-2022#43 | 142 | 272 (0.478) | - | no | -5.711 | - (would be 30) |
| en_radial_shaft_seal#0 (final top) | 4 | 4 (0.613) | 1 | yes | 0.769 | 1 |
| en_radial_shaft_seal#1 (final top) | 11 | 17 (0.582) | 9 | yes | -1.063 | 4 |
| de_wellendichtring#1 (final top) | 3 | 19 (0.580) | 7 | yes | -1.161 | 5 |

Cut-offs: RRF takes each part's top 50; reranker pool = RRF top 30; generator reads the final top 5. Reranker score of final rank 5: -1.161.

Query tokens (document frequency in the English chunk texts): when (197), oil (196), leakage (31), persists (0), in (846), a (817), radial (316), shaft (234), seal (87), what (40), defects (7), of (871), the (869), surface (221), should (74), be (554), checked (1), besides (8), lip (52), wear (170)

| chunk | query tokens present |
|---|---|
| de_wellendichtring#0 | in, a, radial, shaft, seal, of, the, surface, be, lip, wear |
| luh-diss-pelzer-2022#19 | oil, a, radial, shaft, seal, of, the, surface, be, lip |
| luh-diss-pelzer-2022#28 | in, a, shaft, seal, of, the, surface |
| luh-diss-pelzer-2022#40 | oil, in, a, radial, seal, of, the, surface, be |
| luh-diss-pelzer-2022#43 | in, a, radial, seal, of, the, surface, be |
| en_radial_shaft_seal#0 | oil, in, a, radial, shaft, seal, of, the, be, lip, wear |
| de_wellendichtring#0 | in, a, radial, shaft, seal, of, the, surface, be, lip, wear |
| luh-diss-pelzer-2022#19 | oil, a, radial, shaft, seal, of, the, surface, be, lip |
| en_radial_shaft_seal#1 | in, a, radial, shaft, seal, of, the, be, lip, wear |
| de_wellendichtring#1 | when, oil, in, a, radial, shaft, seal, of, the, should, be, lip |

## Variant: Besides lip wear, which properties of the opposing running surface of the shaft cause leakage of a radial shaft seal?

| chunk | BM25 rank | dense rank (cos) | RRF rank | in reranker pool | reranker score | final rank |
|---|---|---|---|---|---|---|
| de_wellendichtring#0 | 11 | 27 (0.592) | 13 | yes | 0.619 | 7 |
| luh-diss-pelzer-2022#19 | 5 | 4 (0.637) | 2 | yes | 1.656 | 2 |
| luh-diss-pelzer-2022#28 | 30 | 22 (0.598) | 22 | yes | -3.445 | 30 |
| luh-diss-pelzer-2022#40 | 40 | 248 (0.482) | 55 | no | -1.741 | - (would be 24) |
| luh-diss-pelzer-2022#43 | 34 | 104 (0.526) | 49 | no | -1.970 | - (would be 26) |
| luh-diss-pelzer-2022#58 (final top) | 7 | 3 (0.644) | 3 | yes | 2.672 | 1 |
| luh-diss-pelzer-2022#24 (final top) | 8 | 6 (0.637) | 7 | yes | 1.158 | 3 |
| luh-diss-pelzer-2022#78 (final top) | 3 | 18 (0.601) | 8 | yes | 1.157 | 4 |
| luh-diss-pelzer-2022#66 (final top) | 1 | 10 (0.616) | 4 | yes | 1.140 | 5 |

Cut-offs: RRF takes each part's top 50; reranker pool = RRF top 30; generator reads the final top 5. Reranker score of final rank 5: 1.140.

Query tokens (document frequency in the English chunk texts): besides (8), lip (52), wear (170), which (449), properties (60), of (871), the (869), opposing (45), running (77), surface (221), shaft (234), cause (96), leakage (31), a (817), radial (316), seal (87)

| chunk | query tokens present |
|---|---|
| de_wellendichtring#0 | lip, wear, of, the, surface, shaft, a, radial, seal |
| luh-diss-pelzer-2022#19 | lip, which, of, the, opposing, running, surface, shaft, a, radial, seal |
| luh-diss-pelzer-2022#28 | which, of, the, running, surface, shaft, a, seal |
| luh-diss-pelzer-2022#40 | of, the, opposing, running, surface, a, radial, seal |
| luh-diss-pelzer-2022#43 | which, of, the, opposing, running, surface, a, radial, seal |
| luh-diss-pelzer-2022#58 | lip, of, the, opposing, running, surface, shaft, leakage, a, radial |
| luh-diss-pelzer-2022#19 | lip, which, of, the, opposing, running, surface, shaft, a, radial, seal |
| luh-diss-pelzer-2022#24 | which, of, the, opposing, running, surface, shaft, cause, leakage, a, radial, seal |
| luh-diss-pelzer-2022#78 | lip, which, of, the, opposing, running, surface, leakage, a, radial, seal |
| luh-diss-pelzer-2022#66 | besides, lip, wear, which, of, the, opposing, surface, shaft, leakage, a, radial, seal |
