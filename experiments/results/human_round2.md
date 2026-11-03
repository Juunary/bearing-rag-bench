# Human review, round 2

## A. Question review

| eval set | n | evidence | wording | realism |
|---|---|---|---|---|
| v2 | 11 | 충분 11 | 자연 11 | 낮음 1, 높음 9, 보통 1 |
| pdf | 12 | 충분 12 | 자연 12 | 낮음 1, 높음 9, 보통 2 |
| all | 23 | 충분 23 | 자연 23 | 낮음 2, 높음 18, 보통 3 |

Notes:
- A02 (q056): 실무보다는 역사적 사실을 묻는 퀴즈에 가깝습니다.
- A05 (q005): 번역투 느낌이 있으나 직역 형태라 자연스러운 범주로 볼 수 있습니다.
- A06 (q030): 설명문 일부를 발췌해 묻는 스무고개/퀴즈 형태에 가깝습니다.
- A08 (q072): 설계 기초 지식 확인용으로 적합합니다.
- A14 (pdf009): 특정 규격 번호를 묻는 질문으로 실무 활용도는 높으나 단편적입니다.
- A17 (pdf017): 비용 절감(Rework)과 관련된 현실적인 실무 질문입니다.
- A20 (pdf010): 문서 내 특정 그림 번호(Figure 27)와 출처를 묻는 형태로 독해 테스트에 가깝습니다.

## B. Answer grading: correctness

Human grades: {'맞음': 18, '부분': 4, '틀림': 5}. Pool (distinct answers) by judge stratum: {'disagree': 14, 'both_yes': 155, 'both_no': 4}; sampled: {'both_yes': 12, 'disagree': 11, 'both_no': 4}.

| judge | partial as | n | agree | agreement | kappa | reweighted agreement | human YES (reweighted) | judge YES (reweighted) |
|---|---|---|---|---|---|---|---|---|
| Qwen3-8B | NO | 27 | 14 | 0.519 | 0.05 | 0.707 | 0.733 | 0.903 |
| Qwen3-8B | excluded | 23 | 13 | 0.565 | 0.19 | 0.837 | 0.877 | 0.893 |
| Granite | NO | 27 | 17 | 0.630 | 0.06 | 0.729 | 0.733 | 0.970 |
| Granite | excluded | 23 | 16 | 0.696 | 0.04 | 0.864 | 0.877 | 0.972 |

Stratified bootstrap (partial as NO, 10000 draws): human YES (reweighted) 95% CI 0.502 .. 0.949; Qwen3-8B YES - human YES -0.041 .. +0.403; Granite YES - human YES +0.021 .. +0.467.

By stratum (partial as NO):

| stratum | n | human YES | Qwen3-8B agrees | Granite agrees |
|---|---|---|---|---|
| disagree | 11 | 6 | 4 | 7 |
| both_yes | 12 | 9 | 9 | 9 |
| both_no | 4 | 3 | 1 | 1 |

## B. Faithfulness and answer relevance

| dimension | judge | n | agree | kappa |
|---|---|---|---|---|
| faithfulness | Qwen3-8B | 10 | 8 | 0.55 |
| faithfulness | Granite | 10 | 6 | 0.00 |
| answer_relevance | Qwen3-8B | 27 | 27 | nan |
| answer_relevance | Granite | 27 | 27 | nan |

## B. Items

| item | qid | stratum | conditions | human | Qwen3-8B | Granite | faithfulness human / Qwen / Granite |
|---|---|---|---|---|---|---|---|
| B01 | q067 | both_yes | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li, v2g_ret_b_rrf_en_rerank | 맞음 | YES | YES |  |
| B02 | q003 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 부분 | NO | YES |  |
| B03 | q057 | both_yes | v2g_lora_s42 | 맞음 | YES | YES | 예 / YES / YES |
| B04 | q019 | both_yes | v2g_qlora_s42 | 맞음 | YES | YES |  |
| B05 | q023 | disagree | v2g_cmp_ar, v2g_ret_x2_rerank_en_text | 맞음 | NO | YES |  |
| B06 | pdf009 | disagree | pdfg_x13_rrf_en_dense_en_rerank_en_text | 부분 | YES | NO |  |
| B07 | q070 | disagree | v2g_base_4bit | 맞음 | NO | YES | 예 / YES / YES |
| B08 | pdf016 | both_no | pdfg_b_rrf_rerank | 틀림 | NO | NO | 아니오 / NO / YES |
| B09 | q054 | both_yes | v2g_base_bf16, v2g_cmp_ar, v2g_cmp_hs, v2g_cmp_li, v2g_ret_b_rrf_en_rerank | 맞음 | YES | YES | 예 / YES / YES |
| B10 | q069 | both_yes | v2g_cmp_ar | 맞음 | YES | YES |  |
| B11 | q069 | both_yes | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 맞음 | YES | YES |  |
| B12 | q003 | disagree | v2g_lora_s42 | 맞음 | NO | YES | 예 / YES / YES |
| B13 | q005 | disagree | v2g_lora_s42 | 틀림 | NO | YES | 아니오 / YES / YES |
| B14 | q005 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 틀림 | NO | YES | 아니오 / NO / YES |
| B15 | q019 | both_yes | v2g_ret_x2_rerank_en_text | 맞음 | YES | YES |  |
| B16 | q005 | disagree | v2g_qlora_s42 | 틀림 | NO | YES | 아니오 / YES / YES |
| B17 | pdf007 | both_yes | pdfg_b_rrf_rerank | 틀림 | YES | YES |  |
| B18 | q070 | both_no | v2g_qlora_s42 | 맞음 | NO | NO |  |
| B19 | q069 | both_yes | v2g_qlora_s42 | 부분 | YES | YES |  |
| B20 | q003 | disagree | v2g_cmp_ar | 맞음 | NO | YES |  |
| B21 | q057 | both_no | v2g_cmp_ar | 맞음 | NO | NO |  |
| B22 | q060 | disagree | v2g_base_4bit | 맞음 | NO | YES | 예 / YES / YES |
| B23 | q070 | disagree | v2g_base_bf16, v2g_cmp_hs, v2g_cmp_li | 맞음 | NO | YES |  |
| B24 | q059 | both_yes | v2g_ret_x2_rerank_en_text | 부분 | YES | YES |  |
| B25 | q057 | both_no | v2g_ret_x2_rerank_en_text | 맞음 | NO | NO | 예 / YES / YES |
| B26 | pdf023 | both_yes | pdfg_th_x13_rrf_en_dense_en_rerank_en_text | 맞음 | YES | YES |  |
| B27 | q055 | both_yes | v2g_ret_x2_rerank_en_text | 맞음 | YES | YES |  |
