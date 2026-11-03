"""Compare the second human review with the two judges -> experiments/results/human_round2.md.

[EN]
- Part A (question review): counts of evidence / wording / realism labels, per eval set.
- Part B (answer grading): agreement of the human correctness grade with Qwen3-8B and Granite. "Partial"
  is counted two ways: as NO (the judge prompt calls an answer incorrect if it omits or changes a fact) and
  left out. The sample over-represents answers where the judges disagree, so besides the raw agreement
  the agreement is reweighted to the whole pool with the stratum sizes (pool count / sampled count).
- Faithfulness and answer relevance: agreement on the items the human graded.
- Part D (the grader's own questions): correctness of the answered ones and whether each refusal was
  appropriate. For refusals graded inappropriate, RELATED lists chunks with related statements found by an
  AI agent in the English chunk texts, and the table shows whether they were among the retrieved candidates.
- Usage: uv run python experiments/analyze_human_round2.py

[KO]
- A(질문 검수): 근거·표현·현실성 라벨 개수(평가셋별).
- B(답변 채점): 사람의 정확성 채점과 Qwen3-8B·Granite 판정의 일치. `부분`은 두 가지로 센다: NO로 보기(판정
  프롬프트는 사실을 빠뜨리거나 바꾸면 incorrect) / 빼기. 표본이 판정 불일치 답변을 많이 뽑았으므로 그대로의 일치율과
  함께 층 크기(풀 개수 / 표본 개수)로 전체 풀에 맞춰 가중한 일치율을 낸다.
- 충실도·답변 관련성: 사람이 채점한 항목의 일치.
- D(채점자가 직접 쓴 질문): 답한 질문의 정확성과 거절이 적절했는지. 거절이 부적절로 채점된 질문은 AI 에이전트가
  영어 번역 청크에서 찾은 관련 문장 청크(RELATED)가 검색 후보에 들었는지 함께 표시한다.
- 사용: uv run python experiments/analyze_human_round2.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import REPO  # noqa: E402

DIR = REPO / "eval" / "human_round2"
OUT = REPO / "experiments" / "results" / "human_round2.md"
JUDGES = {"Qwen3-8B": "judge_qwen", "Granite": "judge_granite"}
# 거절이 부적절로 채점된 질문: 코퍼스(chunks_en_fixed_tok384_ov48_pdf_th)에서 관련 문장이 있는 청크
RELATED = {
    "D05": ["de_wellendichtring#0",          # 축 표면 다듬질 요구, 테이퍼 없이 연삭
            "luh-diss-pelzer-2022#19",       # 립이 상대면의 런아웃·편심을 따라감
            "luh-diss-pelzer-2022#40"],      # 상대면의 표면 다듬질·거칠기와 형상 공차
    "D10": ["en_ball_bearing#15"],           # 축·하우징 끼워맞춤 공차가 맞아야 최대 하중 (헐거울 때의 결과는 없음)
}


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def main() -> None:
    s = json.loads((DIR / "sample.json").read_text(encoding="utf-8"))
    lab = json.loads((DIR / "labels.json").read_text(encoding="utf-8"))["labels"]
    out = ["# Human review, round 2", ""]

    out += ["## A. Question review", "", "| eval set | n | evidence | wording | realism |", "|---|---|---|---|---|"]
    for es in ("v2", "pdf", None):
        items = [a for a in s["part_a"] if es is None or a["evalset"] == es]
        c = {k: Counter(lab[a["item"]][k] for a in items) for k in ("evidence", "wording", "realism")}
        fmt = lambda x: ", ".join(f"{k} {v}" for k, v in sorted(x.items()))  # noqa: E731
        out.append(f"| {es or 'all'} | {len(items)} | {fmt(c['evidence'])} | {fmt(c['wording'])} | {fmt(c['realism'])} |")
    notes = [(a["item"], a["qid"], lab[a["item"]]["note"]) for a in s["part_a"] if "note" in lab[a["item"]]]
    out += ["", "Notes:", *[f"- {i} ({q}): {n}" for i, q, n in notes]]

    B = s["part_b"]
    pool, picked = s["b_pool_strata"], Counter(b["stratum"] for b in B)
    weight = {k: pool[k] / picked[k] for k in picked}
    hc = Counter(lab[b["item"]]["correctness"] for b in B)
    out += ["", "## B. Answer grading: correctness", "",
            f"Human grades: {dict(hc)}. Pool (distinct answers) by judge stratum: {pool}; sampled: {dict(picked)}.", "",
            "| judge | partial as | n | agree | agreement | kappa | reweighted agreement | human YES (reweighted) | judge YES (reweighted) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for jn, key in JUDGES.items():
        for mode in ("NO", "excluded"):
            rows = [b for b in B if not (mode == "excluded" and lab[b["item"]]["correctness"] == "부분")]
            h = [lab[b["item"]]["correctness"] == "맞음" for b in rows]
            j = [bool(b[key]["correctness"]) for b in rows]
            w = [weight[b["stratum"]] for b in rows]
            agree = sum(x == y for x, y in zip(h, j))
            wa = sum(wi * (x == y) for wi, x, y in zip(w, h, j)) / sum(w)
            hy = sum(wi * x for wi, x in zip(w, h)) / sum(w)
            jy = sum(wi * y for wi, y in zip(w, j)) / sum(w)
            out.append(f"| {jn} | {mode} | {len(rows)} | {agree} | {agree / len(rows):.3f} | {kappa(h, j):.2f} | {wa:.3f} | {hy:.3f} | {jy:.3f} |")

    # 층별 재표집 부트스트랩: 가중 사람 YES 비율과 (판정 YES - 사람 YES) 차이의 95% 구간 (부분 = NO)
    rng = np.random.default_rng(0)
    by = {st: [b for b in B if b["stratum"] == st] for st in picked}
    stats = []
    for _ in range(10000):
        res = []
        for st, rows in by.items():
            idx = rng.integers(0, len(rows), len(rows))
            res += [(weight[st], rows[i]) for i in idx]
        tw = sum(w for w, _ in res)
        hy = sum(w * (lab[r["item"]]["correctness"] == "맞음") for w, r in res) / tw
        stats.append([hy] + [sum(w * bool(r[key]["correctness"]) for w, r in res) / tw - hy for key in JUDGES.values()])
    lo, hi = np.percentile(np.array(stats), [2.5, 97.5], axis=0)
    out += ["", f"Stratified bootstrap (partial as NO, 10000 draws): human YES (reweighted) 95% CI {lo[0]:.3f} .. {hi[0]:.3f}; "
            + "; ".join(f"{jn} YES - human YES {lo[i + 1]:+.3f} .. {hi[i + 1]:+.3f}" for i, jn in enumerate(JUDGES)) + "."]

    out += ["", "By stratum (partial as NO):", "", "| stratum | n | human YES | Qwen3-8B agrees | Granite agrees |", "|---|---|---|---|---|"]
    for st in ("disagree", "both_yes", "both_no"):
        rows = [b for b in B if b["stratum"] == st]
        h = [lab[b["item"]]["correctness"] == "맞음" for b in rows]
        qa = sum(x == bool(b["judge_qwen"]["correctness"]) for x, b in zip(h, rows))
        ga = sum(x == bool(b["judge_granite"]["correctness"]) for x, b in zip(h, rows))
        out.append(f"| {st} | {len(rows)} | {sum(h)} | {qa} | {ga} |")

    out += ["", "## B. Faithfulness and answer relevance", "", "| dimension | judge | n | agree | kappa |", "|---|---|---|---|---|"]
    for dim, yes in (("faithfulness", "예"), ("answer_relevance", "예")):
        rows = [b for b in B if dim in lab[b["item"]]]
        h = [lab[b["item"]][dim] == yes for b in rows]
        for jn, key in JUDGES.items():
            j = [bool(b[key][dim]) for b in rows]
            out.append(f"| {dim} | {jn} | {len(rows)} | {sum(x == y for x, y in zip(h, j))} | {kappa(h, j):.2f} |")

    out += ["", "## B. Items", "", "| item | qid | stratum | conditions | human | Qwen3-8B | Granite | faithfulness human / Qwen / Granite |",
            "|---|---|---|---|---|---|---|---|"]
    yn = lambda v: "-" if v is None else ("YES" if v else "NO")  # noqa: E731
    for b in B:
        lb = lab[b["item"]]
        f = f"{lb['faithfulness']} / {yn(b['judge_qwen']['faithfulness'])} / {yn(b['judge_granite']['faithfulness'])}" if "faithfulness" in lb else ""
        out.append(f"| {b['item']} | {b['qid']} | {b['stratum']} | {', '.join(b['conditions'])} | {lb['correctness']} | "
                   f"{yn(b['judge_qwen']['correctness'])} | {yn(b['judge_granite']['correctness'])} | {f} |")
    out += part_d()
    text = "\n".join(out) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text)


def part_d() -> list[str]:
    qs = json.loads((DIR / "labels.json").read_text(encoding="utf-8"))["user_questions"]
    rows = {r["qid"]: r for r in json.loads((DIR / "user_questions_answers.json").read_text(encoding="utf-8"))["rows"]}
    ans = [q for q in qs if "correctness" in q]
    ref = [q for q in qs if "refusal" in q]
    fmt = lambda c: ", ".join(f"{k} {v}" for k, v in sorted(c.items()))  # noqa: E731
    out = ["", "## D. The grader's own questions", "",
           f"Answered {len(ans)}: {fmt(Counter(q['correctness'] for q in ans))}. "
           f"Refused {len(ref)}: {fmt(Counter(q['refusal'] for q in ref))}.", "",
           "| qid | outcome | human | related chunks (in top 5 / in candidates) | note |", "|---|---|---|---|---|"]
    for q in qs:
        r = rows[q["qid"]]
        rel = "; ".join(f"{c} ({'yes' if c in r['best_top5'] else 'no'} / {'yes' if c in r['pool'] else 'no'})"
                        for c in RELATED.get(q["qid"], []))
        outcome, grade = ("refused", q["refusal"]) if r["blocked"] else ("answered", q["correctness"])
        out.append(f"| {q['qid']} | {outcome} | {grade} | {rel} | {q['note']} |")
    return out


if __name__ == "__main__":
    main()
