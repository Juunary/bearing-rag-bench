"""Compare the LLM judge with the human grading and summarise outcome classes.

[EN]
- Role: (1) agreement between the user's labels (eval/human_labels.json) and the judge on the same
  answers, per dimension; (2) outcome classes per prompt and per language pair; (3) the two prompts
  compared on the judged dimensions.
- Mapping of human labels to yes/no: correctness 맞음 = yes, 부분 and 틀림 = no, 거절 = not applicable;
  faithfulness and answer relevance 예 = yes, 아니오 = no. Dimensions the judge does not rate for
  refusals are skipped for those answers.
- With only 8 graded answers, agreement is reported as counts (k of n) with the disagreements listed;
  no percentage or confidence interval is claimed.
- Usage: uv run python experiments/analyze_judge.py

[KO]
- 역할: (1) 사용자 라벨(eval/human_labels.json)과 같은 답변에 대한 판정 모델 결과의 항목별 일치,
  (2) 프롬프트별·언어쌍별 결과 유형, (3) 두 프롬프트의 판정 항목 비교.
- 사람 라벨의 예/아니오 변환: 정확성 맞음 = 예, 부분·틀림 = 아니오, 거절 = 해당 없음. 충실도·답변 관련성은
  예 = 예, 아니오 = 아니오. 판정 모델이 거절 답변에 평가하지 않는 항목은 그 답변에서 건너뛴다.
- 채점한 답변이 8개뿐이라 일치도는 개수(n개 중 k개)와 불일치 목록으로 보고하며, 비율이나 신뢰구간을
  주장하지 않는다.
- 사용: uv run python experiments/analyze_judge.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "experiments" / "results"
DIMS = ("correctness", "faithfulness", "answer_relevance")


def human_to_bool(dim: str, label: str) -> bool | None:
    if dim == "correctness":
        return None if label == "거절" else label == "맞음"
    return label == "예"


def main() -> None:
    human = json.loads((REPO / "eval" / "human_labels.json").read_text(encoding="utf-8"))
    judged = {p["qid"]: p for p in json.loads((RES / f"s3_judge_{human['source'].removeprefix('s3_gen_')}.json").read_text(encoding="utf-8"))["per_query"]}

    print("### 1. human vs judge on the graded answers (Y = yes, N = no, - = not applicable)\n")
    print("| qid | outcome class | correctness H / J | faithfulness H / J | answer relevance H / J |")
    print("|---|---|---|---|---|")
    agree, comparable, disagreements = Counter(), Counter(), []
    fmt = lambda v: "-" if v is None else ("Y" if v else "N")
    for qid, lab in human["labels"].items():
        j = judged[qid]
        cells = []
        for d in DIMS:
            h, jv = human_to_bool(d, lab[d]), j["labels"][d]
            cells.append(f"{fmt(h)} / {fmt(jv)}")
            if h is not None and jv is not None:
                comparable[d] += 1
                if h == jv:
                    agree[d] += 1
                else:
                    disagreements.append((qid, d, fmt(h), fmt(jv), j["reasons"][d]))
        print(f"| {qid} | {j['outcome']} | " + " | ".join(cells) + " |")
    print("\n| dimension | agreements | comparable answers |\n|---|---|---|")
    for d in DIMS:
        print(f"| {d} | {agree[d]} | {comparable[d]} |")
    print("\ndisagreements (human vs judge) with the judge's reasoning:")
    for qid, d, h, jv, why in disagreements:
        print(f"- {qid} {d}: human {h}, judge {jv} | {why.splitlines()[0][:230]}")

    print("\n### 2. outcome classes (n=45 each)\n")
    files = {n: json.loads((RES / f"s3_judge_{n}.json").read_text(encoding="utf-8")) for n in ("cite_v1", "cite_refuse_v1")}
    classes = ("ok", "generation_failure", "retrieval_failure", "correct_refusal", "over_refusal")
    print("| prompt | " + " | ".join(classes) + " |\n|---|" + "---|" * len(classes))
    for n, d in files.items():
        c = Counter(p["outcome"] for p in d["per_query"])
        print(f"| {n} | " + " | ".join(str(c.get(k, 0)) for k in classes) + " |")

    print("\noutcome classes by language pair (cite_refuse_v1):\n")
    by = defaultdict(Counter)
    for p in files["cite_refuse_v1"]["per_query"]:
        by[p["group"]][p["outcome"]] += 1
    print("| group | " + " | ".join(classes) + " |\n|---|" + "---|" * len(classes))
    for g in sorted(by):
        print(f"| {g} | " + " | ".join(str(by[g].get(k, 0)) for k in classes) + " |")

    print("\n### 3. judged dimensions per prompt (share of YES among applicable answers)\n")
    dims = ("faithfulness", "answer_relevance", "context_relevance", "correctness")
    print("| prompt | " + " | ".join(dims) + " | judge context relevance vs gold label |\n|---|" + "---|" * (len(dims) + 1))
    for n, d in files.items():
        o = d["metrics"]["overall"]
        print(f"| {n} | " + " | ".join(f"{o[x]:.3f} (n={o[x + '_n']})" for x in dims) + f" | {o['judge_context_vs_gold_agreement']:.3f} |")

    same = sum(a["answer"] == b["answer"] for a, b in zip(files["cite_v1"]["per_query"], files["cite_refuse_v1"]["per_query"]))
    both_gen_fail = [a["qid"] for a, b in zip(files["cite_v1"]["per_query"], files["cite_refuse_v1"]["per_query"])
                     if a["outcome"] == "generation_failure" and b["outcome"] == "generation_failure"]
    print(f"\nanswers identical between the prompts: {same} of 45; generation_failure under both prompts: {len(both_gen_fail)} {both_gen_fail}")


if __name__ == "__main__":
    main()
