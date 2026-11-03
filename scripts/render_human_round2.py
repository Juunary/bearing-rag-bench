"""Render eval/human_round2/sample.json as the grading sheet -> eval/human_round2/sheet.md (and sheet_d.md).

[EN]
- The sheet shows only what a reviewer needs: the question, the gold sentences, the answer and, for
  faithfulness items, the cited passages. Conditions and judge verdicts are not shown (blind grading).
- sheet_d.md (when user_questions_answers.json exists): the answers to the grader's own questions, graded
  from the grader's knowledge (no gold), and for refusals the documents that were retrieved.
- Usage: uv run python scripts/render_human_round2.py

[KO]
- 채점표에는 검수에 필요한 것만 넣는다: 질문, 정답 문장, 답변, 충실도 항목이면 인용한 청크 원문. 조건과 판정
  모델 결과는 보여주지 않는다(블라인드 채점).
- sheet_d.md(user_questions_answers.json이 있을 때): 채점자가 직접 쓴 질문의 답변을 채점자 지식으로 채점(정답 라벨 없음),
  거절한 질문은 검색된 문서를 함께 보여준다.
- 사용: uv run python scripts/render_human_round2.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

DIR = REPO / "eval" / "human_round2"


def gold_lines(q: dict) -> list[str]:
    return [f"- ({'핵심' if g['grade'] == 2 else '보조'}) {g['anchor']}" for g in q["gold"]]


def main() -> None:
    s = json.loads((DIR / "sample.json").read_text(encoding="utf-8"))
    queries = {"v2": {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")},
               "pdf": {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_pdf.jsonl")}}
    out = ["# 사람 검수 2차", "",
           "조건과 판정 모델 결과는 넣지 않았습니다. 같은 질문이 여러 번 나오면 답변이 서로 다른 것입니다.", "",
           "## 답 형식 (한 항목에 한 줄)", "", "```",
           "A01 | 근거: 충분 | 표현: 자연 | 현실성: 높음 | 메모: (선택)",
           "B01 | 정확성: 맞음 | 관련성: 예",
           "B03 | 정확성: 부분 | 관련성: 예 | 충실도: 아니오      <- (충실도 포함) 항목만",
           "D01 | (직접 쓴 질문)", "```", "",
           "- A 근거: `충분` = 정답 문장만으로 질문에 답할 수 있음 / `부족` = 정답 문장에 답이 일부만 있음 / `불일치` = 정답 문장이 질문과 맞지 않음",
           "- A 표현: `복사` = 질문이 정답 문장 표현을 거의 그대로 옮김(번역 포함) / `자연` = 그렇지 않음",
           "- A 현실성: `높음` / `보통` / `낮음` = 실제 업무에서 사람이 할 법한 질문인가",
           "- B 정확성: `맞음` = 질문이 묻는 사실이 기준 문장과 일치 / `부분` = 일부만 맞거나 틀린 내용이 섞임 / `틀림`",
           "- B 관련성: `예` = 질문이 묻는 것을 다루려고 함(맞는지는 따지지 않음) / `아니오`",
           "- B 충실도: `예` = 답변의 모든 사실 진술이 아래 인용 청크에 있음 / `아니오` = 청크에 없는 내용이 있음",
           "- D: 문서를 보지 않고, 실제 업무에서 물을 법한 베어링·자동차 부품 질문 10개(한국어 또는 영어). 정답 표시는 다음 차례에 합니다.", "",
           "## A. 질문 검수", ""]
    for a in s["part_a"]:
        q = queries[a["evalset"]][a["qid"]]
        out += [f"**{a['item']}** 질문: {q['question']}", "", "정답 문장:", *gold_lines(q)]
        if q.get("answer"):
            out.append(f"- (참고 답) {q['answer']}")
        out.append("")
    out += ["## B. 답변 채점", ""]
    for b in s["part_b"]:
        q = queries[b["evalset"]][b["qid"]]
        out += [f"**{b['item']}**{' (충실도 포함)' if b['faithfulness_item'] else ''} 질문: {q['question']}", "",
                "기준 문장:", *gold_lines(q), "", f"답변: {b['answer']}", ""]
        for c in b.get("cited_passages", []):
            out += [f"> [{c['chunk_id']}] " + c["text"].replace("\n", " "), ""]
    (DIR / "sheet.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(len("\n".join(out)), "chars")

    if (DIR / "user_questions_answers.json").exists():
        render_d(json.loads((DIR / "user_questions_answers.json").read_text(encoding="utf-8")))


def render_d(d: dict) -> None:
    out = ["# 사람 검수 3차: 직접 쓴 질문의 답변", "",
           "## 답 형식 (한 항목에 한 줄)", "", "```",
           "D01 | 정확성: 맞음 | 메모: (선택)",
           "D02 | 거절: 적절 | 메모: (선택)", "```", "",
           "- 정확성(답변한 질문): 실무 지식 기준 `맞음` / `부분` = 일부만 맞거나 틀린 내용이 섞임 / `틀림`",
           "- 거절(거절한 질문): `적절` = 위키백과·NASA 보고서·베어링 학위논문 같은 일반 문헌에서 답을 기대하기 어려운 질문 / "
           "`부적절` = 이런 문헌에 있을 만한 기본 지식이라 답했어야 함", ""]
    for r in d["rows"]:
        out += [f"**{r['qid']}** {'(거절)' if r['blocked'] else ''} 질문: {r['question']}", ""]
        if r["blocked"]:
            docs = list(dict.fromkeys(c.split("#")[0] for c in r["best_top5"]))
            out += [f"답변: {r['answer']}", "", f"검색된 상위 5개 청크의 문서: {', '.join(docs)}", ""]
        else:
            out += [f"답변: {r['answer']}", ""]
    (DIR / "sheet_d.md").write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
