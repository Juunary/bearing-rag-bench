"""Agreement between the first and the second human grader -> experiments/results/human_agreement.md.

[EN]
- Input: eval/human_gold/grader2_answers.txt, one line per item in the sheet's format
  (`H01 | 정확성: 맞음 | 메모: ...` or `H02 | 거절: 적절 | 메모: ...`), and eval/human_gold/grader2_sample.json (H id -> gold id).
  The parsed grades are written to eval/human_gold/grader2.json.
- Correctness: Cohen's kappa over three classes (맞음/부분/틀림) and two classes (부분 = 틀림, the convention of the judge
  tables), raw agreement, and the agreement reweighted to the whole gold set with the stratum sizes (the sample takes
  every 부분/틀림 item but only 20 of 74 맞음 items). Refusals: agreement on 적절/부적절.
- Disagreements are listed with both grades so the two graders can settle them; the settled values go to
  eval/human_gold/adjudicated.json ({"labels": {gold id: value}}), which ragbench.humangold.load_items applies.
- The human-human kappa is the ceiling for the judge: a judge is good when its kappa with the adjudicated labels comes
  close to this value, not when it reaches 1.
- Usage: uv run python experiments/analyze_human_agreement.py

[KO]
- 입력: eval/human_gold/grader2_answers.txt(채점표 형식으로 한 줄씩), eval/human_gold/grader2_sample.json(H 번호 -> 정답 세트 ID).
  파싱한 채점은 eval/human_gold/grader2.json에 쓴다.
- 정확성: 3분류(맞음/부분/틀림)와 2분류(부분 = 틀림, 판정 표의 규약) Cohen's kappa, 그대로의 일치율, 층 크기로 정답 세트 전체에
  맞춘 가중 일치율(표본은 부분·틀림을 전부, 맞음은 74개 중 20개만 뽑았다). 거절: 적절/부적절 일치.
- 불일치 항목은 두 채점을 나란히 적어 두 채점자가 합의할 수 있게 한다. 합의한 값은 eval/human_gold/adjudicated.json에 쓰고
  ragbench.humangold.load_items가 반영한다.
- 사람끼리 kappa가 판정 모델의 상한이다. 판정 모델은 합의 라벨과의 kappa가 1이 아니라 이 값에 가까울 때 좋은 것이다.
- 사용: uv run python experiments/analyze_human_agreement.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.humangold import CORRECTNESS, GOLD_DIR, REFUSAL, binary, load_items  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.stats import cohen_kappa  # noqa: E402

OUT = REPO / "experiments" / "results" / "human_agreement.md"
LINE_RE = re.compile(r"^\s*(H\d+)\s*\|\s*(정확성|거절)\s*:\s*(\S+)\s*(?:\|\s*메모\s*:\s*(.*))?$")


def parse_answers(text: str) -> dict[str, dict[str, str]]:
    """Grader lines -> {H id: {"kind", "value", "note"}}; malformed or out-of-vocabulary lines raise."""
    out: dict[str, dict[str, str]] = {}
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            raise ValueError(f"line {n}: not in the sheet format: {line!r}")
        hid, kind, value, note = m.groups()
        kind = "correctness" if kind == "정확성" else "refusal"
        if value not in (CORRECTNESS if kind == "correctness" else REFUSAL):
            raise ValueError(f"line {n}: {value!r} is not a {kind} grade")
        if hid in out:
            raise ValueError(f"line {n}: {hid} graded twice")
        out[hid] = {"kind": kind, "value": value, "note": (note or "").strip()}
    return out


def weighted_agreement(pairs: list[tuple[str, str, str]], strata: dict[str, dict[str, int]]) -> float:
    """Agreement reweighted by pool / sampled of the first grader's stratum. pairs: (stratum key, grade 1, grade 2)."""
    num = den = 0.0
    for key, a, b in pairs:
        w = strata[key]["pool"] / strata[key]["sampled"]
        num += w * (a == b)
        den += w
    return num / den if den else float("nan")


def main() -> None:
    sample = json.loads((GOLD_DIR / "grader2_sample.json").read_text(encoding="utf-8"))
    g2 = parse_answers((GOLD_DIR / "grader2_answers.txt").read_text(encoding="utf-8"))
    (GOLD_DIR / "grader2.json").write_text(json.dumps({"graded_by": "person (second grader)", "labels": g2},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    gold = {it["id"]: it for it in load_items(adjudicated=None)}      # 합의 전 첫 채점과 비교한다
    missing = [h for h in sample["items"] if h not in g2]
    corr, refu, kind_mismatch = [], [], []
    for hid, gid in sample["items"].items():
        if hid not in g2:
            continue
        it, b = gold[gid], g2[hid]
        a = it["label"]
        if a["kind"] != b["kind"]:
            kind_mismatch.append((hid, gid, a, b))
            continue
        (corr if a["kind"] == "correctness" else refu).append((hid, gid, f"{a['kind']}/{a['value']}", a["value"], b["value"]))

    lines = ["# 사람 채점자 두 명의 일치도", "",
             f"표본 {len(sample['items'])}개, 두 번째 채점 {len(g2)}개, 빠진 항목 {len(missing)}개, 종류 불일치(한쪽만 거절로 봄) {len(kind_mismatch)}개.", ""]
    if corr:
        a3, b3 = [x[3] for x in corr], [x[4] for x in corr]
        a2, b2 = [binary(x) for x in a3], [binary(x) for x in b3]
        lines += ["## 정확성", "", "| 지표 | 값 |", "|---|---|",
                  f"| 항목 수 | {len(corr)} |",
                  f"| 일치율 (3분류) | {sum(x == y for x, y in zip(a3, b3)) / len(corr):.3f} |",
                  f"| kappa (3분류) | {cohen_kappa(a3, b3):.3f} |",
                  f"| 일치율 (부분 = 틀림) | {sum(x == y for x, y in zip(a2, b2)) / len(corr):.3f} |",
                  f"| kappa (부분 = 틀림) | {cohen_kappa(a2, b2):.3f} |",
                  f"| 가중 일치율 (3분류, 정답 세트 전체 환산) | {weighted_agreement([(x[2], x[3], x[4]) for x in corr], sample['strata']):.3f} |", "",
                  "| 첫 채점 \\ 두 번째 | " + " | ".join(CORRECTNESS) + " |", "|---|" + "---|" * len(CORRECTNESS)]
        for v in CORRECTNESS:
            lines.append(f"| {v} | " + " | ".join(str(sum(1 for x in corr if x[3] == v and x[4] == w)) for w in CORRECTNESS) + " |")
        lines.append("")
    if refu:
        lines += ["## 거절", "", f"항목 {len(refu)}개, 일치 {sum(x[3] == x[4] for x in refu)}개, "
                  f"kappa {cohen_kappa([x[3] for x in refu], [x[4] for x in refu]):.3f}.", ""]
    dis = [x for x in corr + refu if x[3] != x[4]]
    lines += ["## 합의가 필요한 항목", "", "| H | 정답 세트 ID | 첫 채점 | 두 번째 | 두 번째 메모 |", "|---|---|---|---|---|"]
    lines += [f"| {x[0]} | {x[1]} | {x[3]} | {x[4]} | {g2[x[0]]['note']} |" for x in dis]
    lines += [f"| {h} | {g} | {a['kind']}/{a['value']} | {b['kind']}/{b['value']} | {b['note']} |" for h, g, a, b in kind_mismatch]
    lines += ["", "합의한 값은 `eval/human_gold/adjudicated.json`에 `{\"labels\": {\"g012\": \"부분\"}}` 형식으로 적습니다."]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
