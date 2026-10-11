"""Create the human grading sheet for a small, mixed sample of generated answers.

[EN]
- Role: pick 8 answers from the refusal-prompt run and write eval/human_grading_sheet.md for the
  user to grade, plus eval/human_sample.json (the qids only).
- Sample (seed 42): 4 answered questions whose gold chunk was in the prompt (one each from ko, en, de
  questions plus one more), 1 refusal although the gold chunk was in the prompt, and 3 answered
  questions whose gold chunk was NOT in the prompt. Order is shuffled so the groups are not visible.
- The sheet shows the question, the eval set's reference sentences, the answer and the text of the
  chunks the answer cites. It shows no judge output, so the human grading is independent of it.
- Human items: correctness (right / partial / wrong / refusal), faithfulness (yes / no), answer
  relevance (yes / no). Context relevance is not graded by hand: it follows from the gold labels.
- Usage: uv run python scripts/make_grading_sheet.py

[KO]
- 역할: 거절 프롬프트 실행에서 답변 8개를 골라 사용자가 채점할 eval/human_grading_sheet.md와 qid만 담은
  eval/human_sample.json을 만든다.
- 표본(시드 42): 정답 청크가 프롬프트에 있고 답한 4개(ko, en, de 질문에서 하나씩과 추가 1개), 정답 청크가
  프롬프트에 있는데 거절한 1개, 정답 청크가 프롬프트에 없는데 답한 3개. 어떤 집단인지 드러나지 않게
  순서를 섞는다.
- 채점표에는 질문, 평가셋 기준 문장, 답변, 답변이 인용한 청크 원문이 나온다. 판정 모델의 출력은 보여
  주지 않아 사람 채점이 독립적이다.
- 사람 채점 항목: 정확성(맞음/부분/틀림/거절), 충실도(예/아니오), 답변 관련성(예/아니오). 컨텍스트
  관련성은 정답 라벨로 정해지므로 손으로 채점하지 않는다.
- 사용: uv run python scripts/make_grading_sheet.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.generation import CITE_RE  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.validation import validate_answer  # noqa: E402

SOURCE = "s3_gen_cite_refuse_v1"


def select(rows: list[dict], seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    def refused(p): return validate_answer(p["answer"], p["context_ids"]).reason in ("refusal_sentinel", "refusal_text")
    a = [p for p in rows if p["metrics"]["gold_in_context"] and not refused(p)]
    b = [p for p in rows if p["metrics"]["gold_in_context"] and refused(p)]
    c = [p for p in rows if not p["metrics"]["gold_in_context"] and not refused(p)]
    picked = []
    for lang in ("ko", "en", "de"):
        picked.append(rng.choice([p for p in a if p["question_lang"] == lang]))
    picked.append(rng.choice([p for p in a if p not in picked]))
    picked += rng.sample(b, 1) + rng.sample(c, 3)
    ids = [p["qid"] for p in picked]
    rng.shuffle(ids)
    return ids


def main() -> None:
    res = json.loads((REPO / "experiments" / "results" / f"{SOURCE}.json").read_text(encoding="utf-8"))
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries.jsonl")}
    rows = []
    for p in res["per_query"]:
        rows.append({**p, "question_lang": queries[p["qid"]]["q_lang"]})
    ids = select(rows)
    by_qid = {p["qid"]: p for p in rows}
    by_chunk = {c["chunk_id"]: c for c in load_chunks(ChunkingConfig())}

    lines = ["# 사람 채점표 (8개)", "",
             "각 샘플의 질문, 평가셋 기준 문장, 답변, 답변이 인용한 청크 원문을 읽고 3항목을 표시해 주세요. 판정 모델의 결과는 포함되어 있지 않습니다.", "",
             "- **정확성**: `맞음` = 질문이 묻는 사실이 기준 문장과 일치 / `부분` = 일부만 맞거나 틀린 내용이 섞임 / `틀림` / `거절` = 답이 NO_ANSWER이거나 정보가 없다고만 함",
             "- **충실도**: `예` = 답변의 모든 사실 진술이 아래 인용 청크에 있음 / `아니오` = 청크에 없는 내용이 있음",
             "- **답변 관련성**: `예` = 질문이 묻는 것을 다루려고 함(맞는지는 따지지 않음) / `아니오` = 다른 얘기이거나 정보가 없다고만 함", "",
             "채팅에 아래 형식으로 8줄을 붙여 넣으면 됩니다.", "",
             "```", "q011 | 정확성: 맞음 | 충실도: 예 | 답변 관련성: 예", "```", "", "---", ""]
    for n, qid in enumerate(ids, start=1):
        p, q = by_qid[qid], queries[qid]
        cited = [i for i in dict.fromkeys(CITE_RE.findall(p["answer"])) if i in p["context_ids"]]
        lines += [f"## {n}. {qid}", "", f"**질문**: {q['question']}", "", "**기준 문장 (평가셋)**:"]
        lines += [f"- `{g['doc_id']}`: {g['anchor']}" for g in q["gold"]]
        lines += ["", f"**답변**: {p['answer']}", ""]
        if cited:
            lines += ["**답변이 인용한 청크 원문**:", ""]
            for cid in cited:
                text = by_chunk[cid]["text"]
                lines += [f"> `[{cid}]` {text[:1200]}{' ...' if len(text) > 1200 else ''}", ""]
        else:
            lines += ["**답변이 인용한 청크**: 없음", ""]
        lines += ["---", ""]
    (REPO / "eval" / "human_grading_sheet.md").write_text("\n".join(lines), encoding="utf-8")
    (REPO / "eval" / "human_sample.json").write_text(json.dumps({"source": SOURCE, "qids": ids}, indent=1), encoding="utf-8")
    print("sample:", ids)


if __name__ == "__main__":
    main()
