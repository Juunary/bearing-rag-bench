"""Blind grading sheet for a second human grader, drawn from eval/human_gold/items.jsonl.

[EN]
- Role: measure agreement between two people on the same answers. Without it the judge has no ceiling to be compared
  with: a judge cannot be expected to agree with one person better than another person does.
- Sample (fixed seed): every 부분 and 틀림 item (they are rare and the hard cases), 6 refusals graded 적절 and 6 graded
  부적절, and 20 맞음 items; refusals without a first grade are left out. Stratum sizes and pool sizes are stored so
  agreement can be reweighted to the whole gold set.
- The sheet shows the question, the reference evidence (gold sentences, or the guide page for practical questions;
  the same material the first grader had) and the answer as it was shown. It never shows the first grade, the
  note, the round or the system that produced the answer. Items are shuffled across rounds and numbered H01 ..
- Outputs: eval/human_gold/grader2_sample.json (H id -> gold id, strata; not for the grader),
  eval/human_gold/sheet_grader2.md (for the grader). Answers go to eval/human_gold/grader2_answers.txt, one line per
  item in the sheet's format, and are read by experiments/analyze_human_agreement.py.
- Usage: uv run python scripts/make_grader2_sheet.py

[KO]
- 역할: 같은 답변에 대한 사람 두 명의 일치도를 잰다. 이것이 없으면 판정 모델을 비교할 상한이 없다(판정 모델이 사람끼리보다
  사람과 더 잘 맞을 수는 없다).
- 표본(고정 시드): 부분·틀림 전부(드물고 어려운 경우), 거절 적절 6·부적절 6, 맞음 20. 1차 판정이 없는 거절은 뺀다. 층 크기와
  전체 크기를 저장해 정답 세트 전체로 가중 환산할 수 있게 한다.
- 채점표에는 질문, 기준 근거(정답 문장, 실무 질문은 안내 페이지: 첫 채점자가 본 것과 같은 자료), 보인 그대로의 답변만 있다.
  첫 채점 결과·메모·라운드·답을 낸 시스템은 보이지 않는다. 라운드를 섞어 H01부터 번호를 붙인다.
- 출력: eval/human_gold/grader2_sample.json(H 번호 -> 정답 세트 ID, 층; 채점자용 아님), eval/human_gold/sheet_grader2.md(채점자용).
  답은 eval/human_gold/grader2_answers.txt에 채점표 형식으로 한 줄씩 쓰고 experiments/analyze_human_agreement.py가 읽는다.
- 사용: uv run python scripts/make_grader2_sheet.py
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.humangold import GOLD_DIR, load_items, reference_texts  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

SEED = 20261118
TARGET = {("correctness", "부분"): None, ("correctness", "틀림"): None, ("refusal", "적절"): 6, ("refusal", "부적절"): 6,
          ("correctness", "맞음"): 20}          # None = 층 전부


def draw(items: list[dict], seed: int = SEED) -> tuple[list[dict], dict]:
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for it in items:
        strata[(it["label"]["kind"], it["label"]["value"])].append(it)
    rng = random.Random(seed)
    picked, sizes = [], {}
    for key, n in TARGET.items():
        pool = sorted(strata.get(key, []), key=lambda x: x["id"])
        take = pool if n is None or n >= len(pool) else rng.sample(pool, n)
        picked += take
        sizes["/".join(key)] = {"pool": len(pool), "sampled": len(take)}
    rng.shuffle(picked)
    return picked, sizes


def sheet(rows: list[tuple[str, dict]]) -> str:
    lines = ["# 답변 채점표 (두 번째 채점자, 블라인드)", "",
             "질문마다 기준 근거와 답변이 있습니다. 기준 근거와 실무 지식으로 답변을 판정해 주세요.",
             "답 형식(grader2_answers.txt에 한 줄씩): `H01 | 정확성: 맞음 | 메모:` (맞음/부분/틀림) 또는 "
             "`H02 | 거절: 적절 | 메모:` (답변이 거절이면 적절/부적절).",
             "- 맞음: 질문이 묻는 핵심에 맞게 답했고 틀린 내용이 없음",
             "- 부분: 핵심 일부만 답했거나, 기준 근거에 없는 내용이 섞임",
             "- 틀림: 핵심이 틀렸거나 질문과 다른 것에 답함",
             "- 거절 적절: 기준 근거로도 답할 수 없는 질문 / 부적절: 답할 수 있었는데 거절함", ""]
    for hid, it in rows:
        refs = reference_texts(it)
        lines += [f"## {hid}", "", f"**질문**: {it['question']}", ""]
        if refs:
            quoted = ["> " + r.replace("\n", "\n> ") for r in refs]
            lines += ["**기준 근거**:", "", *quoted, ""]
        else:
            lines += ["**기준 근거**: (이 질문에 해당하는 기준 근거 페이지가 없습니다)", ""]
        lines += [("**답변(거절)**: " if it["blocked"] else "**답변**: ") + it["answer"], "", "---", ""]
    return "\n".join(lines)


def main() -> None:
    items = [it for it in load_items() if it["label"]["value"] is not None]
    picked, sizes = draw(items)
    rows = [(f"H{i:02d}", it) for i, it in enumerate(picked, start=1)]
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    (GOLD_DIR / "grader2_sample.json").write_text(json.dumps(
        {"seed": SEED, "strata": sizes, "items": {hid: it["id"] for hid, it in rows}}, ensure_ascii=False, indent=1), encoding="utf-8")
    (GOLD_DIR / "sheet_grader2.md").write_text(sheet(rows), encoding="utf-8")
    print(json.dumps(sizes, ensure_ascii=False))
    print(f"{len(rows)} items -> {(GOLD_DIR / 'sheet_grader2.md').relative_to(REPO)}")


if __name__ == "__main__":
    main()
