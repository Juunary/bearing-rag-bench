"""Apply the independent review of the 90-question evaluation set -> eval/queries_v2.jsonl (+ change log).

[EN]
- Input: eval/v2_draft/queries_v2_prereview.jsonl (45 original + 45 new questions) and the five review
  outputs eval/v2_draft/review_output_*.json (independent reviewer agents, AI, not human).
- Rules: (1) every `missing_gold` sentence a reviewer found is added as grade 1 unless listed in SKIP_MISSING
  or overridden in OPS; (2) OPS holds the manual decisions for every other proposed fix (question rewrite, grade
  change, removal, anchor replacement); (3) gold[0] keeps its document language so the 10 questions per
  (question language, primary language) pair are preserved; a new sentence in another language is added as
  a non-primary grade-2 entry instead; (4) every anchor is checked to exist verbatim in its document.
- Output: eval/queries_v2.jsonl, eval/v2_review_log.json (one record per change).

[KO]
- 입력: eval/v2_draft/queries_v2_prereview.jsonl(기존 45 + 신규 45)과 독립 검수 결과 5개
  eval/v2_draft/review_output_*.json(검수 에이전트, AI이며 사람이 아님).
- 규칙: (1) 검수자가 찾은 `missing_gold` 문장은 SKIP_MISSING에 있거나 OPS가 덮어쓰지 않는 한 grade 1로
  추가한다. (2) 나머지 수정 제안(질문 재작성, 등급 변경, 삭제, 앵커 교체)은 OPS에 수동 결정으로 적는다.
  (3) gold[0]은 문서 언어를 유지해 (질문 언어, 주 근거 언어) 쌍마다 10문항이 보존되게 하고, 다른 언어의
  새 문장은 주 근거가 아닌 grade 2로 추가한다. (4) 모든 앵커가 문서에 그대로 있는지 확인한다.
- 출력: eval/queries_v2.jsonl, eval/v2_review_log.json(변경마다 한 줄).
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import locate_anchor  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402

# 수동 결정. 앵커 지정은 앞부분 문자열(prefix)로 한다.
# ("remove", prefix) | ("grade", prefix, g) | ("add", doc_id, prefix_or_full, g) | ("question", text)
# ("replace", prefix, new_full_anchor) | ("merge_prev", prefix, other_prefix)  (두 문장을 이어 한 앵커로, other 항목이 gold에 있으면 제거) | ("first", prefix)
OPS: dict[str, list[tuple]] = {
    "q001": [("remove", "Without adequate lubrication, journal bearings")],
    "q002": [("remove", "Käfigwerkstoff")],
    "q011": [("grade", "이와 같은 동력전달장치로서 차동기어가", 2)],
    "q013": [("merge_prev", "In industrial manufacturing, this is referred to as galling", "Adhesive wear can lead to an increase in roughness"),
             ],
    "q016": [("grade", "If pressing force is applied to the wrong race", 2), ("grade", "Care must usually be taken", 1),
             ("first", "If pressing force is applied to the wrong race")],
    "q018": [("remove", "They are also compact and lightweight")],
    "q019": [("add", "en_grease", "Greases are usually shear-thinning or pseudo-plastic fluids", 2),
             ("first", "Greases are usually shear-thinning or pseudo-plastic fluids"),
             ("grade", "A common feature of greases is that they possess high initial viscosities", 1)],
    "q021": [("add", "de_waelzlager", "Lagereinheiten bilden eine besonders einfache Möglichkeit für die Lagerung von Wellen.", 2)],
    "q023": [("question", "What is the advantage of a sleeve bearing over a ball bearing in case fans, and what happens to its life at high rotation speed?"),
             ("grade", "높은 회전속도에서는 고발열로 인해", 1), ("first", "슬리브베어링 (sleeve bearing)")],
    "q024": [("remove", "If the bearing movement is limited to small motions")],
    "q025": [("question", "Which constant-velocity joint improves on the Rzeppa six-ball cage design by confining the balls to elliptical tracks?"),
             ("remove", "They have improved efficiency and are widely used")],
    "q027": [("grade", "Heute werden auch", 1)],
    "q029": [("remove", "Die Ringe dehnen sich minimal aus")],
    "q030": [("remove", "회전체의 한 점이 회전중심으로부터")],
    "q032": [("question", "Welcher Reibungszustand tritt beim Anlauf der Welle eines hydrodynamischen Gleitlagers zunächst auf?"),
             ("remove", "This design of bearing may wear when started")],
    "q033": [("remove", "As the advent of modern elastomers")],
    "q034": [("question", "Wovon hängt die Temperatur ab, ab der die Gleitpartner eines Lagers beim Fressen miteinander verschweißen?"),
             ("grade", "Die progressiv fortschreitende Grenz- und Mischreibung", 1),
             ("remove", "Fresser treten an tribologisch hochbeanspruchten Teilen auf"), ("remove", "Fressen bedeutet in der Technik")],
    "q035": [("add", "de_schmierfett", "Unter Schmierfetten versteht man physikalisch Suspensionen aus", 2),
             ("add", "de_schmierfett", "In der Regel bestehen Schmierfette aus 65–95 % Schmieröl", 2)],
    "q038": [("merge_prev", "Dazu zählen metallische Rollgeräusche", "Zum Beispiel sind Schäden an Lagern im Auto"),
             ("remove", "In Kurven können Klopf- oder Vibrationsgeräusche")],
    "q040": [("grade", "The result is a finely polished surface", 2), ("first", "The result is a finely polished surface"),
             ("grade", "Brinelling is permanent plastic deformation", 1)],
    "q041": [("remove", "Needle bearings are heavily used in automobile components")],
    "q043": [("remove", "This standard covers all aspects")],
    "q044": [("remove", "동식물유에서 얻는 편이")],
    "q045": [("remove", "그 한가지 예로")],
    "q055": [("replace", "such as silicon nitride", "Ceramics such as silicon nitride are now regularly used in such applications due to their low density (40% of steel).")],
    "q069": [("add", "en_ball_bearing", "Time between grease replacements decreases very strongly", 2)],
    "q070": [("question", "What fraction of the world's total energy expenditure is caused by friction and wear in the transport, manufacturing, power generation and residential sectors?"),
             ("add", "en_tribology", "Approximately 20% of the world's energy (2012) is consumed by", 2)],
    "q072": [("add", "en_fatigue_material", "called a fatigue limit or endurance limit", 2)],
    "q078": [("question", "Wie hoch ist die Dichte von Siliziumnitrid im Vergleich zu Stahl?")],
    "q083": [("grade", "Leonardo da Vinci incorporated drawings of ball bearings", 2)],
    "q085": [("question", "Wie viel Prozent der weltweit eingesetzten Energie gehen in Transport, Fertigung, Stromerzeugung und Wohnsektor durch Reibung und Verschleiß verloren?"),
             ("add", "en_tribology", "Approximately 20% of the world's energy (2012) is consumed by", 2)],
    "q090": [("add", "en_grease", "Greases are applied to mechanisms that can be lubricated only infrequently", 2)],
}
# 검수자가 찾은 missing_gold 중 적용하지 않는 것 (질문을 바꿨거나, 같은 사실이 아닌 경우)
SKIP_MISSING = {"q032": ("Die Hauptprobleme bei Mischreibung", "Beim Anfahren wird die Haftreibung überwunden"),
                "q034": ("Without lubrication, the pressure", "When lubrication breaks down"),
                "q070": ("In total, ~23%", "23 % des weltweiten"), "q085": ("In total, ~23%", "23 % des weltweiten", "20 % entstehen durch Reibung")}
# 교체 문항: 쓰인 적 없는 독일어 문서에서 새로 쓴다 (q061의 영어·독일어 수치 충돌 해소)
REPLACE = {"q061": {"question": "At what internal clearance do ball bearings reach their longest service life?",
                    "gold": [{"doc_id": "de_lager_maschinenelement", "doc_lang": "de", "grade": 2,
                              "anchor": "Bei Kugellagern ergibt sich die höchste Lebensdauer bei einem Lagerspiel nahe null oder einer minimalen Vorspannung."}],
                    "type": "cross", "difficulty": "hard", "note": "de: clearance vs life; wording differs (internal clearance / Lagerspiel)"}}


def find(q: dict, prefix: str) -> int:
    hits = [i for i, g in enumerate(q["gold"]) if g["anchor"].startswith(prefix) or prefix in g["anchor"][:200]]
    if len(hits) != 1:
        raise SystemExit(f"{q['qid']}: prefix {prefix[:40]!r} matched {len(hits)} gold entries")
    return hits[0]


def main() -> None:
    docs = {d["doc_id"]: d for d in load_docs()}
    qs = [json.loads(l) for l in open(REPO / "eval/v2_draft/queries_v2_prereview.jsonl", encoding="utf-8") if l.strip()]
    reviews = {}
    for f in sorted(glob.glob(str(REPO / "eval/v2_draft/review_output_*.json"))):
        for r in json.load(open(f, encoding="utf-8")):
            reviews[r["qid"]] = r
    log: list[dict] = []

    def record(qid: str, op: str, detail: str) -> None:
        log.append({"qid": qid, "op": op, "detail": detail})

    def full_anchor(doc_id: str, prefix: str) -> str:
        # 검수자가 준 앵커를 문서 원문에서 그대로 확인한다 (앞부분만 주어졌으면 그 문장 전체를 복원)
        text = docs[doc_id]["text"]
        start, _ = locate_anchor(text, prefix.rstrip(".…")) if not prefix.endswith(".") else locate_anchor(text, prefix)
        end = text.find("\n", start)
        end = len(text) if end < 0 else end
        # 문장 끝까지: 마침표+공백 또는 줄 끝
        import re
        m = re.search(r"(?<=[.!?。])\s", text[start:end])
        return text[start:start + m.start()] if m else text[start:end]

    for q in qs:
        qid = q["qid"]
        if qid in REPLACE:
            q.update({k: v for k, v in REPLACE[qid].items()})
            record(qid, "replace_question", REPLACE[qid]["question"])
            continue
        for op in OPS.get(qid, []):
            kind = op[0]
            if kind == "question":
                record(qid, "question", f"{q['question']} -> {op[1]}")
                q["question"] = op[1]
            elif kind == "remove":
                i = find(q, op[1]); g = q["gold"].pop(i)
                record(qid, "remove_gold", f"{g['doc_id']} grade{g['grade']}: {g['anchor'][:80]}")
            elif kind == "grade":
                i = find(q, op[1]); record(qid, "grade", f"{q['gold'][i]['anchor'][:60]}: {q['gold'][i]['grade']} -> {op[2]}")
                q["gold"][i]["grade"] = op[2]
            elif kind == "first":
                i = find(q, op[1]); q["gold"].insert(0, q["gold"].pop(i)); record(qid, "first", q["gold"][0]["anchor"][:60])
            elif kind == "replace":
                i = find(q, op[1]); locate_anchor(docs[q["gold"][i]["doc_id"]]["text"], op[2])
                record(qid, "replace_anchor", f"{q['gold'][i]['anchor'][:60]} -> {op[2][:60]}"); q["gold"][i]["anchor"] = op[2]
            elif kind == "merge_prev":
                i = find(q, op[1]); j = find(q, op[2]) if any(g["anchor"].startswith(op[2]) for g in q["gold"]) else None
                a_first = (op[2] if j is None else q["gold"][j]["anchor"]); a_second = q["gold"][i]["anchor"]
                doc = docs[q["gold"][i]["doc_id"]]["text"]
                s1, e1 = locate_anchor(doc, a_first); s2, e2 = locate_anchor(doc, a_second)
                merged = doc[s1:e2]
                if "\n" in merged or e1 > s2:
                    raise SystemExit(f"{qid}: sentences are not contiguous in one line")
                record(qid, "merge_anchor", f"{merged[:90]}"); q["gold"][i]["anchor"] = merged
                if j is not None:      # 합쳐진 앞 문장 항목은 중복이므로 함께 제거한다
                    q["gold"].pop(j)
            elif kind == "add":
                _, doc_id, pre, grade = op
                anchor = pre if pre.endswith((".", "?", "!")) and len(pre) > 60 else full_anchor(doc_id, pre)
                locate_anchor(docs[doc_id]["text"], anchor)
                if not any(g["doc_id"] == doc_id and g["anchor"] == anchor for g in q["gold"]):
                    q["gold"].append({"doc_id": doc_id, "doc_lang": docs[doc_id]["lang"], "grade": grade, "anchor": anchor})
                    record(qid, "add_gold", f"{doc_id} grade{grade}: {anchor[:80]}")
        # 검수자가 찾은 누락 정답: grade 1로 추가
        for m in (reviews.get(qid, {}).get("missing_gold") or []):
            if any(m["anchor"].startswith(s) for s in SKIP_MISSING.get(qid, ())):
                continue
            try:
                locate_anchor(docs[m["doc_id"]]["text"], m["anchor"])
            except (ValueError, KeyError):
                record(qid, "missing_gold_not_found", f"{m['doc_id']}: {m['anchor'][:80]}")
                continue
            if any(g["doc_id"] == m["doc_id"] and (g["anchor"] == m["anchor"] or g["anchor"].startswith(m["anchor"][:60])) for g in q["gold"]):
                continue
            q["gold"].append({"doc_id": m["doc_id"], "doc_lang": docs[m["doc_id"]]["lang"], "grade": 1, "anchor": m["anchor"]})
            record(qid, "add_missing_gold", f"{m['doc_id']}: {m['anchor'][:80]}")
        q.pop("draft_qid", None)

    # 주 근거는 grade 2여야 한다: grade 2가 앞에 오도록 하되 gold[0]의 문서 언어는 바뀌면 안 된다
    pre = {json.loads(l)["qid"]: json.loads(l)["gold"][0]["doc_lang"] for l in open(REPO / "eval/v2_draft/queries_v2_prereview.jsonl", encoding="utf-8")}
    for q in qs:
        if q["gold"][0]["grade"] != 2:
            raise SystemExit(f"{q['qid']}: gold[0] is not grade 2 after the edits")
        if q["qid"] not in REPLACE and q["gold"][0]["doc_lang"] != pre[q["qid"]]:
            raise SystemExit(f"{q['qid']}: primary language changed {pre[q['qid']]} -> {q['gold'][0]['doc_lang']}")
    with open(REPO / "eval/queries_v2.jsonl", "w", encoding="utf-8") as f:
        for q in qs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    (REPO / "eval/v2_review_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(qs), "questions;", len(log), "changes;", dict(Counter(r["op"] for r in log)))


if __name__ == "__main__":
    main()
