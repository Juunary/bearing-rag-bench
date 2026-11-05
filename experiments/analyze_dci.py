"""DCI (grep/read agent) on the questions RAG refused -> experiments/results/dci_analysis.md.

[EN]
- Inputs: eval/dci/results_v1.json and results_v2.json (trajectories and outcomes), eval/dci/sample_v2.json and
  labels_v2.json (one person's correctness grades of the v2 answers), eval/kb/results.json + labels.json (the bundle's
  grades on the same K questions, for comparison).
- Sections: (1) per variant and set: answered, calls, tokens, seconds, malformed outputs, PDF gold read / cited;
  (2) v2 answers with the human grade and, for K questions, the bundle grade; (3) search patterns of v1 vs v2 on D05.
- Usage: uv run python experiments/analyze_dci.py

[KO]
- 입력: eval/dci/results_v1.json·results_v2.json(궤적·결과), sample_v2.json·labels_v2.json(v2 답변의 사람 채점), eval/kb/results.json +
  labels.json(같은 K 질문에서 번들의 채점, 비교용).
- 구성: (1) 변형·세트별 답변 수, 호출, 토큰, 시간, 형식 오류, PDF 정답 청크 읽음/인용; (2) v2 답변의 사람 채점과 K 질문의 번들 채점;
  (3) D05에서 v1·v2의 검색어.
- 사용: uv run python experiments/analyze_dci.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import REPO  # noqa: E402

D = REPO / "eval" / "dci"
OUT = REPO / "experiments" / "results" / "dci_analysis.md"


def main() -> None:
    res = {v: json.loads((D / f"results_{v}.json").read_text(encoding="utf-8")) for v in ("v1", "v2")}
    items = json.loads((D / "sample_v2.json").read_text(encoding="utf-8"))["items"]
    lab = json.loads((D / "labels_v2.json").read_text(encoding="utf-8"))["labels"]
    grade = {it["qid"]: lab[it["item"]] for it in items}
    kb = json.loads((REPO / "eval" / "kb" / "results.json").read_text(encoding="utf-8"))
    kb_lab = json.loads((REPO / "eval" / "kb" / "labels.json").read_text(encoding="utf-8"))["labels"]
    kb_items = json.loads((REPO / "eval" / "kb" / "sample.json").read_text(encoding="utf-8"))["items"]
    bundle_grade = {}
    for it in kb_items:
        if "bundle" in it["modes"]:
            g = kb_lab[it["item"]]
            bundle_grade[it["qid"]] = g.get("correctness") or f"거절 ({g.get('refusal')})"
    out = ["# Direct corpus interaction: a grep/read agent on the 20 questions the serving pipeline refused", "",
           f"Generator {res['v2']['model']} (greedy), tool budget {res['v2']['max_calls']} calls. v1: regex grep, terse prompt; "
           "v2: all-terms grep (every term must occur, any order) and a prompt asking for one or two key terms per search.", "",
           "## 1. Outcomes", "", "| variant | set | n | answered | calls, mean | tokens, mean | seconds, mean | malformed outputs | gold read / cited (PDF) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for v, r in res.items():
        for s, m in r["summary"].items():
            g = f"{m['gold_read']} / {m['cites_gold']}" if s == "PDF" else "-"
            out.append(f"| {v} | {s} | {m['n']} | {m['answered']} | {m['calls_mean']:.1f} | {m['tokens_mean']:.0f} | {m['seconds_mean']:.0f} | {m['malformed']} | {g} |")
    out += ["", "## 2. v2 answers: human grade, and the knowledge bundle's grade on the same K questions", "",
            "| qid | set | scope | DCI v2 | DCI grade | bundle grade | chunks read |", "|---|---|---|---|---|---|---|"]
    for x in res["v2"]["rows"]:
        if x["set"] == "PDF":
            continue
        g = grade.get(x["qid"], {}).get("correctness", "-") if not x["blocked"] else "-"
        out.append(f"| {x['qid']} | {x['set']} | {x['scope']} | {'blocked (' + str(x['reason']) + ')' if x['blocked'] else 'answered'} | {g} | "
                   f"{bundle_grade.get(x['qid'], '-')} | {', '.join(x['read']) or '-'} |")
    out += ["", "Notes from the grader:", ""] + [f"- {it['item']} ({it['qid']}): {lab[it['item']]['correctness']} — {lab[it['item']]['note']}" for it in items]
    out += ["", "## 3. Search patterns on D05 (oil seal leakage)", ""]
    for v, r in res.items():
        row = next(x for x in r["rows"] if x["qid"] == "D05")
        pats = [json.loads(t["model"][t["model"].find("{"):t["model"].rfind("}") + 1]).get("pattern") for t in row["trajectory"] if '"grep"' in t["model"]]
        out.append(f"- {v}: " + "; ".join(f"`{p}`" for p in pats if p) + f" -> read {row['read'] or 'nothing'}, {'blocked (' + str(row['reason']) + ')' if row['blocked'] else 'answered'}")
    text = "\n".join(out) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
