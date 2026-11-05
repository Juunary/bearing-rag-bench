"""Knowledge bundle experiment: human grades per mode -> experiments/results/kb_analysis.md.

[EN]
- Inputs: eval/kb/results.json (answers of rag / bundle / hybrid for 20 questions), eval/kb/sample.json (blind items,
  identical answers merged), eval/kb/labels.json (one person's grades: correctness 맞음/부분/틀림 for answers,
  refusal 적절/부적절 for refusals), eval/kb/questions.jsonl (scope in/out of the bundle topics).
- Sections: (1) per mode: answered / refused, correct / partial / wrong, refusal appropriate / inappropriate, split by
  in-scope (16) and out-of-scope (4) questions, mean prompt tokens and seconds; hybrid also by path; (2) per question:
  the grade of every mode side by side; (3) the item -> mode map that the blind sheet hid.
- Usage: uv run python experiments/analyze_kb.py

[KO]
- 입력: eval/kb/results.json(질문 20개에 대한 rag / bundle / hybrid 답변), eval/kb/sample.json(블라인드 항목, 같은 답변은 묶음),
  eval/kb/labels.json(사람 1명의 채점: 답변은 정확성 맞음/부분/틀림, 거절은 적절/부적절), eval/kb/questions.jsonl(번들 주제 안/밖).
- 구성: (1) 방식별 답변/거절 수, 맞음/부분/틀림, 거절 적절/부적절을 주제 안(16)·밖(4)으로 나눠서, 평균 프롬프트 토큰·초; hybrid는
  경로별로도; (2) 질문별 세 방식의 채점; (3) 블라인드 채점표가 숨겼던 항목 -> 방식 대응.
- 사용: uv run python experiments/analyze_kb.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import REPO  # noqa: E402

KB = REPO / "eval" / "kb"
OUT = REPO / "experiments" / "results" / "kb_analysis.md"
MODES = ["rag", "bundle", "hybrid"]


def main() -> None:
    res = json.loads((KB / "results.json").read_text(encoding="utf-8"))
    sample = json.loads((KB / "sample.json").read_text(encoding="utf-8"))["items"]
    lab = json.loads((KB / "labels.json").read_text(encoding="utf-8"))["labels"]
    scope = {json.loads(l)["qid"]: json.loads(l)["scope"] for l in (KB / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    # (qid, mode) -> 채점 (같은 답변은 한 항목이므로 그 항목의 채점을 모든 방식에 적용)
    grade: dict[tuple[str, str], dict] = {}
    item_of: dict[tuple[str, str], str] = {}
    for it in sample:
        for m in it["modes"]:
            grade[(it["qid"], m)] = lab[it["item"]]
            item_of[(it["qid"], m)] = it["item"]
    rows = res["rows"]

    def summary(mode: str, qids: list[str]) -> dict:
        c = Counter()
        for q in qids:
            g = grade[(q, mode)]
            c["n"] += 1
            if "correctness" in g:
                c["answered"] += 1
                c[g["correctness"]] += 1
            else:
                c["refused"] += 1
                c["refusal_" + g["refusal"]] += 1
        return c

    out = ["# Knowledge bundle (data/kb, 12 reviewed pages) vs RAG vs hybrid: 20 questions written by a person", "",
           f"Generator {res['model']}, prompt {res['prompt_version']}, RAG retrieval `{res['config']}` (top 5). Grades by one person "
           f"(eval/kb/labels.json); identical answers to the same question were graded once.", "",
           "## 1. Per mode", "", "| mode | subset | n | answered | 맞음 | 부분 | 틀림 | refused | 거절 적절 | 거절 부적절 | prompt tokens, mean | seconds, mean |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    all_q = [r["qid"] for r in rows]
    subsets = {"all": all_q, "in-scope": [q for q in all_q if scope[q] == "in"], "out-of-scope": [q for q in all_q if scope[q] == "out"]}
    for m in MODES:
        for name, qids in subsets.items():
            c = summary(m, qids)
            rs = [r["modes"][m] for r in rows if r["qid"] in qids]
            tok = sum(r["prompt_tokens"] or 0 for r in rs) / len(rs)
            sec = sum(r["seconds"] for r in rs) / len(rs)
            out.append(f"| {m} | {name} | {c['n']} | {c['answered']} | {c['맞음']} | {c['부분']} | {c['틀림']} | {c['refused']} | "
                       f"{c['refusal_적절']} | {c['refusal_부적절']} | {tok:.0f} | {sec:.1f} |")
    paths = Counter(r["modes"]["hybrid"]["path"] for r in rows)
    out += ["", f"Hybrid path: answered by RAG {paths['rag']}, fell back to the bundle {paths['bundle']} "
            f"(of which refused again {sum(1 for r in rows if r['modes']['hybrid']['path'] == 'bundle' and r['modes']['hybrid']['blocked'])}).",
            "", "## 2. Per question", "", "| qid | scope | topic | " + " | ".join(MODES) + " |", "|---|---|---|" + "---|" * len(MODES)]
    fmt = lambda g: (g["correctness"] if "correctness" in g else f"거절 ({g['refusal']})")  # noqa: E731
    for r in rows:
        cells = [fmt(grade[(r["qid"], m)]) + (f" via {r['modes'][m]['path']}" if m == "hybrid" else "") for m in MODES]
        out.append(f"| {r['qid']} | {scope[r['qid']]} | {r.get('topic') or '-'} | " + " | ".join(cells) + " |")
    out += ["", "## 3. Blind items -> modes", "", "| item | qid | modes | grade | note |", "|---|---|---|---|---|"]
    for it in sorted(sample, key=lambda x: x["item"]):
        g = lab[it["item"]]
        out.append(f"| {it['item']} | {it['qid']} | {', '.join(it['modes'])} | {fmt(g)} | {g['note']} |")
    text = "\n".join(out) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
