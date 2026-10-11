### 1. human vs judge on the graded answers (Y = yes, N = no, - = not applicable)

| qid | outcome class | correctness H / J | faithfulness H / J | answer relevance H / J |
|---|---|---|---|---|
| q025 | ok | Y / Y | Y / Y | Y / Y |
| q021 | retrieval_failure | Y / Y | N / Y | Y / Y |
| q031 | ok | Y / Y | Y / Y | Y / Y |
| q015 | generation_failure | N / N | Y / Y | Y / Y |
| q027 | over_refusal | - / - | Y / - | N / - |
| q032 | retrieval_failure | Y / Y | Y / Y | Y / Y |
| q010 | retrieval_failure | N / N | N / Y | Y / Y |
| q017 | ok | Y / Y | Y / Y | Y / Y |

| dimension | agreements | comparable answers |
|---|---|---|
| correctness | 7 | 7 |
| faithfulness | 5 | 7 |
| answer_relevance | 7 | 7 |

disagreements (human vs judge) with the judge's reasoning:
- q021 faithfulness: human N, judge Y | The Answer correctly identifies the self-aligning ball bearing as the type that combines a ball bearing with a spherical outer ring and a housing, and accurately explains the tilting mechanism based on the spherical raceway allowi
- q010 faithfulness: human N, judge Y | Answer에서 언급된 "개스킷 또는 기계적 패킹"은 Passage에 명시되어 있으며, 스타팅 박스(스터핑 박스)도 Passage에 언급된 밀봉 부품 중 하나로, 오일과 공기 누출 방지에 사용될 수 있음을 나타내므로, 모든 사실적 진술이 Passage에 지지된다.  

### 2. outcome classes (n=45 each)

| prompt | ok | generation_failure | retrieval_failure | correct_refusal | over_refusal |
|---|---|---|---|---|---|
| cite_v1 | 29 | 6 | 5 | 4 | 1 |
| cite_refuse_v1 | 29 | 6 | 5 | 4 | 1 |

outcome classes by language pair (cite_refuse_v1):

| group | ok | generation_failure | retrieval_failure | correct_refusal | over_refusal |
|---|---|---|---|---|---|
| de->de | 7 | 1 | 1 | 0 | 0 |
| de->en | 3 | 0 | 0 | 1 | 0 |
| de->ko | 1 | 1 | 0 | 0 | 0 |
| en->de | 0 | 0 | 2 | 1 | 1 |
| en->en | 8 | 1 | 0 | 0 | 0 |
| en->ko | 2 | 0 | 0 | 0 | 0 |
| ko->de | 2 | 0 | 1 | 2 | 0 |
| ko->en | 4 | 2 | 1 | 0 | 0 |
| ko->ko | 2 | 1 | 0 | 0 | 0 |

### 3. judged dimensions per prompt (share of YES among applicable answers)

| prompt | faithfulness | answer_relevance | context_relevance | correctness | judge context relevance vs gold label |
|---|---|---|---|---|---|
| cite_v1 | 0.925 (n=40) | 0.975 (n=40) | 0.889 (n=45) | 0.850 (n=40) | 0.867 |
| cite_refuse_v1 | 0.950 (n=40) | 1.000 (n=40) | 0.889 (n=45) | 0.800 (n=40) | 0.867 |

answers identical between the prompts: 9 of 45; generation_failure under both prompts: 5 ['q003', 'q009', 'q015', 'q037', 'q044']
