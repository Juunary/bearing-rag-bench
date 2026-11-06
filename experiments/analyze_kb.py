"""Knowledge bundle experiment: human grades per mode -> experiments/results/kb_analysis.md.

[EN]
- Inputs: eval/kb/results.json (answers of every mode in results["modes"]: rag, bundle, hybrid, kb_first, both), eval/kb/sample.json (blind items,
  identical answers merged), eval/kb/labels.json (one person's grades: correctness 맞음/부분/틀림 for answers,
  refusal 적절/부적절 for refusals), eval/kb/questions.jsonl (scope in/out of the bundle topics).
- Sections: (1) per mode: answered / refused, correct / partial / wrong, refusal appropriate / inappropriate, split by
  in-scope (16) and out-of-scope (4) questions, mean prompt tokens and seconds; hybrid / kb_first also by path, and for
  kb_first how the questions matched (alias / dense) with the best dense cosine of every question, so the fixed threshold
  can be judged; (2) per question: the grade of every mode side by side; (3) the item -> mode map that the blind sheet hid.
- Usage: uv run python experiments/analyze_kb.py [--dir eval/kb2 --questions eval/kb/questions2.jsonl --out experiments/results/kb2_analysis.md]

[KO]
- 입력: eval/kb/results.json(results["modes"]의 모든 방식 답변: rag, bundle, hybrid, kb_first, both), eval/kb/sample.json(블라인드 항목, 같은 답변은 묶음),
  eval/kb/labels.json(사람 1명의 채점: 답변은 정확성 맞음/부분/틀림, 거절은 적절/부적절), eval/kb/questions.jsonl(번들 주제 안/밖).
- 구성: (1) 방식별 답변/거절 수, 맞음/부분/틀림, 거절 적절/부적절을 주제 안(16)·밖(4)으로 나눠서, 평균 프롬프트 토큰·초; hybrid·kb_first는
  경로별로도, kb_first는 매칭 방식(별칭/dense)과 질문별 최고 dense 코사인(고정 임계값의 타당성 확인용); (2) 질문별 채점; (3) 블라인드
  채점표가 숨겼던 항목 -> 방식 대응.
- 사용: uv run python experiments/analyze_kb.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import REPO  # noqa: E402

KB_DEFAULT = REPO / "eval" / "kb"
OUT_DEFAULT = REPO / "experiments" / "results" / "kb_analysis.md"


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=KB_DEFAULT, help="eval/kb (round 1, 12 pages) or eval/kb2 (round 2, 24 pages)")
    ap.add_argument("--questions", type=Path, default=None, help="question file (default <dir>/questions.jsonl)")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args()
    kbdir, OUTP = args.dir, args.out
    qfile = args.questions or kbdir / "questions.jsonl"
    res = json.loads((kbdir / "results.json").read_text(encoding="utf-8"))
    sample = json.loads((kbdir / "sample.json").read_text(encoding="utf-8"))["items"]
    lab = json.loads((kbdir / "labels.json").read_text(encoding="utf-8"))["labels"]
    scope = {json.loads(l)["qid"]: json.loads(l)["scope"] for l in qfile.read_text(encoding="utf-8").splitlines() if l.strip()}
    # (qid, mode) -> 채점 (같은 답변은 한 항목이므로 그 항목의 채점을 모든 방식에 적용)
    grade: dict[tuple[str, str], dict] = {}
    item_of: dict[tuple[str, str], str] = {}
    for it in sample:
        for m in it["modes"]:
            grade[(it["qid"], m)] = lab[it["item"]]
            item_of[(it["qid"], m)] = it["item"]
    rows = res["rows"]
    MODES = res["modes"]

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

    out = [f"# Knowledge bundle (data/kb, {res['kb_pages']} reviewed pages) vs RAG: {len(rows)} questions written by a person ({qfile.name})", "",
           f"Generator {res['model']}, prompt {res['prompt_version']}, RAG retrieval `{res['config']}` (top 5). Grades by one person "
           f"({kbdir.resolve().relative_to(REPO)}/labels.json); identical answers to the same question were graded once.", "",
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
    for m in ("hybrid", "kb_first", "kb_matched"):
        if m in MODES:
            paths = Counter(r["modes"][m]["path"] for r in rows)
            out += ["", f"{m} path: answered by RAG {paths['rag']}, by the bundle {paths['bundle']} "
                    f"(of which refused {sum(1 for r in rows if r['modes'][m]['path'] == 'bundle' and r['modes'][m]['blocked'])})."]
    if "kb_first" in MODES:
        how = Counter(("alias" if r["modes"]["kb_first"]["match"]["alias"] else "dense" if r["modes"]["kb_first"]["match"]["dense"] else "none") for r in rows)
        out += ["", f"kb_first matching (threshold {res.get('kb_dense_min')}): alias {how['alias']}, dense {how['dense']}, none {how['none']}.", "",
                "| qid | scope | matched page(s) | how | best dense page (cosine) |", "|---|---|---|---|---|"]
        for r in rows:
            mt = r["modes"]["kb_first"]["match"]
            h = "alias: " + "; ".join(f for fs in mt["alias"].values() for f in fs) if mt["alias"] else ("dense" if mt["dense"] else "-")
            out.append(f"| {r['qid']} | {scope[r['qid']]} | {', '.join(mt['ids']) or '-'} | {h} | {mt['dense_best'][0]} ({mt['dense_best'][1]:.2f}) |")
    out += ["", "## 2. Per question", "", "| qid | scope | topic | " + " | ".join(MODES) + " |", "|---|---|---|" + "---|" * len(MODES)]
    fmt = lambda g: (g["correctness"] if "correctness" in g else f"거절 ({g['refusal']})")  # noqa: E731
    for r in rows:
        cells = [fmt(grade[(r["qid"], m)]) + (f" via {r['modes'][m]['path']}" if "path" in r["modes"][m] else "") for m in MODES]
        out.append(f"| {r['qid']} | {scope[r['qid']]} | {r.get('topic') or '-'} | " + " | ".join(cells) + " |")
    out += ["", "## 3. Blind items -> modes", "", "| item | qid | modes | grade | note |", "|---|---|---|---|---|"]
    for it in sorted(sample, key=lambda x: x["item"]):
        g = lab[it["item"]]
        out.append(f"| {it['item']} | {it['qid']} | {', '.join(it['modes'])} | {fmt(g)} | {g['note']} |")
    text = "\n".join(out) + "\n"
    OUTP.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
