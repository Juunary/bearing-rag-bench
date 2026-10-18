# 평가셋 작성 규칙 (`eval/queries.jsonl`)

한 줄에 질문 하나. 정답은 **청크 ID가 아니라 "문서 ID + 근거 문장 원문"**으로 적는다.
청킹 설정이 바뀌어도 평가셋은 그대로 두고, 평가 시점에 근거 문장을 포함하는 청크를 자동으로 찾는다
(기본 규칙: 근거 문장의 50% 이상을 포함하는 청크를 정답으로 인정, `anchor_min_overlap`).

```json
{"qid": "q001", "q_lang": "ko", "question": "구름 베어링에서 유막이 끊기면 어떤 손상이 먼저 생기는가?",
 "gold": [
   {"doc_id": "en_rolling_bearing", "doc_lang": "en", "grade": 2,
    "anchor": "Insufficient lubrication leads to metal-to-metal contact and surface fatigue."},
   {"doc_id": "de_waelzlager", "doc_lang": "de", "grade": 1,
    "anchor": "Mangelschmierung führt zu erhöhtem Verschleiß."}
 ],
 "type": "cross", "difficulty": "easy", "note": "ko 질문, en 핵심 근거 + de 보조 근거"}
```

필드:
- `qid`: `q001`부터 순번.
- `q_lang`: 질문 언어 `ko | en | de`.
- `question`: 실제 사용자가 칠 법한 문장. 문서 문장을 그대로 베끼지 않는다(그러면 BM25가 너무 쉽게 맞춘다).
- `gold[]`: 정답 근거 1개 이상. **gold[0]은 주 근거(등급 2)**이며, 그 언어가 `type`과 집계 그룹
  (`q_lang->gold[0].doc_lang`)을 정한다. 같은 사실이 다른 언어 문서(번역 문서 포함)에도 있으면
  알고 있는 범위에서 함께 적어 부당한 오답 처리를 줄인다(전수 확인은 아님).
  - `doc_id`: `data/sources.csv`의 ID.
  - `doc_lang`: 그 문서의 언어. `(q_lang, doc_lang)` 쌍으로 집계한다.
  - `grade`: `2` = 그 문장만 있어도 답할 수 있는 핵심 근거, `1` = 보조 근거. nDCG에 쓰인다.
  - `anchor`: 문서 원문 **그대로 복사한 한 문장**(띄어쓰기·문장부호까지). 두 문장 이상이면 매핑이 깨지기 쉬우니 한 문장으로.
- `type`: `mono`(주 근거 gold[0]가 질문과 같은 언어) / `cross`(다른 언어).
- `difficulty`: `easy`(키워드가 문서에 그대로 있음) / `hard`(동의어·수치 추론·표현이 다름).
- `note`: 선택.

규모 목표: 언어당 질문 10~15개, 그중 1/3은 교차 언어. 총 40~50개.
정답 등급 2가 하나 이상인 질문만 넣는다(등급 1만 있는 질문은 답변 생성 단계에서 애매해진다).

## 변경 이력

- 2026-10-12: 45문항 초안을 Claude가 작성(사용자 위임). 표본 검수 12개 중 q011, q034 수정(`review_sample.md` 참고).
  수정 후 7개 검색 설정을 재실행했고 지표 변화는 없었다.
- 2026-10-19: `queries_v2.jsonl` 추가(90문항, 질문 언어 x 주 근거 언어 9개 쌍마다 10문항). 기존 45문항은 `queries.jsonl`과 같은 내용에서 시작하고,
  신규 45문항은 Claude 에이전트 3개가 문서만 보고 작성했다(`v2_draft/new_*.jsonl`, 실험 결과는 보지 않음). 90문항 전부를 별도 Claude 검수 에이전트
  5개가 독립적으로 검수했다(`v2_draft/review_output_*.json`; 사람 검수가 아님). 결과: 통과 36, 수정 제안 54, 삭제 0. 수정은 `scripts/apply_v2_review.py`가
  적용하며 변경 95건이 `v2_review_log.json`에 기록된다(누락 정답 문장 45건을 grade 1로 추가, 정답 근거가 아닌 항목 16건 삭제, 등급 변경 10건, 질문 수정 7건,
  q061은 영어·독일어 문서의 수치가 충돌해 새 문항으로 교체). 쌍별 균형을 위해 `gold[0]`의 문서 언어는 바꾸지 않았다. `queries.jsonl`(45문항)은 변경하지 않았다.
