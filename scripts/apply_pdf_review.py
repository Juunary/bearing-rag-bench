"""Apply the two independent reviews of the PDF question draft -> eval/queries_pdf.jsonl (+ change log).

[EN]
- Input: eval/pdf_draft/queries_pdf_prereview.jsonl (48 questions written by two agents from the PDF text only) and
  eval/pdf_draft/review_output_A.json / _B.json (two reviewer agents, AI, not human; each reviewed all 48 without seeing
  the other review or the writers' notes).
- Rules: (1) every `missing_gold` sentence proposed by either reviewer is added (if both propose it with different
  grades, the lower grade); it must occur verbatim in its document; (2) question rewrites flagged by both reviewers are
  applied (the rewrite of one of them is chosen in OPS); a change proposed by one reviewer only is applied when OPS says
  so; (3) table rows whose column headers are in another chunk get the header row or caption as grade 1 (from the
  reviewers' missing_gold) and the note "table_header_split"; (4) gold[0] keeps its document so the 8 questions per
  (question language, document language) pair are preserved.
- Output: eval/queries_pdf.jsonl, eval/pdf_review_log.json (one record per change).
- Usage: uv run python scripts/apply_pdf_review.py

[KO]
- 입력: eval/pdf_draft/queries_pdf_prereview.jsonl(에이전트 2개가 PDF 텍스트만 보고 쓴 48문항)과
  eval/pdf_draft/review_output_A.json·_B.json(검수 에이전트 2개, AI이며 사람이 아님. 서로의 검수와 작성자 메모를 보지 않고
  각자 48문항 전부를 검수).
- 규칙: (1) 어느 한 검수자라도 제안한 `missing_gold` 문장은 추가한다(둘이 다른 등급을 주면 낮은 등급). 문서 원문에 그대로
  있어야 한다. (2) 두 검수자가 모두 지적한 질문은 다시 쓴다(어느 쪽 문구를 쓸지는 OPS). 한 명만 제안한 변경은 OPS에 적은
  것만 반영한다. (3) 열 머리글이 다른 청크에 있는 표 행 문항은 머리글 행이나 캡션을 grade 1로 넣고(검수자의 missing_gold)
  note에 "table_header_split"를 붙인다. (4) gold[0]의 문서는 바꾸지 않아 (질문 언어, 문서 언어) 쌍마다 8문항이 유지된다.
- 출력: eval/queries_pdf.jsonl, eval/pdf_review_log.json(변경마다 한 줄).
- 사용: uv run python scripts/apply_pdf_review.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import locate_anchor  # noqa: E402
from ragbench.ingest import REPO, load_corpus  # noqa: E402

DRAFT = REPO / "eval" / "pdf_draft"

# 수동 결정. ("question", 새 질문, 새 답 또는 None, 근거) | ("grade", 앵커 앞부분, 새 등급) | ("remove", 앵커 앞부분)
# | ("anchor", 앵커 앞부분, 새 전체 앵커) | ("note", 메모)
OPS: dict[str, list[tuple]] = {
    "pdf001": [("note", "table_header_split: column headers in the previous chunk; caption and header row added as grade 1")],
    "pdf003": [("question", "Welche L10-Lebensdauer in Stunden sagt die Lundberg-Palmgren-Analyse mit Lebensdauerfaktoren für das "
                "Propeller-Axialkugellager des kommerziellen Turboprop-Getriebes voraus?", "L10 = 33 065 h (L50 = 180 484 h).",
                "A+B: the Weibull slope column has no header in the chunk"),
               ("note", "table_header_split")],
    "pdf005": [("note", "table_header_split")],
    "pdf006": [("note", "table_header_split")],
    "pdf010": [("question", "In the NASA review of rolling-element bearing life prediction, which figure shows Wöhler-type stress-cycle "
                "curves with an endurance limit, and which source is it credited to?", None, "A+B: copies the caption (B's wording)")],
    "pdf013": [("question", "Out of the roughly 224,000 airline engine bearings that came back for repair, how many had to be scrapped "
                "because of spalling fatigue?", None, "A+B: copies the anchor (A's wording; B's adds dates not asked by the anchor)")],
    "pdf018": [("grade", "Anecdotally, the life of these early engines", 1)],
    "pdf019": [("question", "Sugiura et al. ran rolling contact tests on fully crowned rollers with several crown radii. How much shorter "
                "was life because of edge loading than the central contact stress alone would suggest?", None, "A+B: copies the anchor (B's wording)")],
    "pdf020": [("question", "210 사이즈 원통 롤러 베어링에 기준 하중 29,190 N을 걸었을 때, 에어로스페이스 롤러 프로파일(평탄부 8 mm + "
                "곡률 반경 크라운)에서 내륜 최대 헤르츠 응력은 얼마인가요?", None, "B only: reference load missing, 'partial crowning' ambiguous")],
    "pdf021": [("question", "Auf welchen Wert sinkt nach Lundberg-Palmgren der Last-Lebensdauer-Exponent p bei Zylinderrollen mit sehr starker "
                "Vollbombierung (Bombierradius R = 100·d) im Vergleich zu unbombierten Rollen?", None,
                "B only: the same document gives 10/3 and p = 3.2 for other crown radii")],
    "pdf022": [("question", "If I size a cylindrical roller bearing with Zaretsky's life equation and the rollers have an aerospace-type or "
                "chamfered end relief, which load exponent should I use, and how does it differ from uncrowned and fully crowned rollers?",
                None, "A+B: copies conclusion 3 (B's wording)")],
    "pdf024": [("note", "conflicting statement in the corpus: tm-2015 and tp-2013 also say there was no breakdown of the cause for removal")],
    "pdf027": [("note", "table_header_split (row label readable)")],
    "pdf029": [("question", "NUP 2208 총형 원통롤러베어링의 스미어링 시험에 사용한 유압유의 ISO 점도 등급은 무엇인가요?", None,
                "A+B: the oil table belongs to the smearing tests only")],
    "pdf030": [("question", "Wie stark (Schadensklasse) schmierte das vollrollige NUP 2208 bei 1350 min−1, 35 kN Radial-, 2,3 kN Axialkraft "
                "und 70 °C trotz reduzierter axialer Luft am Außenring und 60 min Einlauf an?", None,
                "A+B: document-internal run number (A's wording keeps the conditions a user would give)")],
    "pdf031": [("question", "In welcher Abbildung der Dissertation zu Schlupf und Anschmierungen in vollrolligen Zylinderrollenlagern sieht man, "
                "wie die Messspule und die mit Magnet präparierte Rolle zur Messung der Rollendrehzahl aufgebaut sind?", None,
                "A+B: copies the caption (B's wording)")],
    "pdf034": [("anchor", "dem Teilkreisdurchmesser des Wälzkörpersatzes", "Die Zentrifugalkraft Fzent der Wälzkörper berechnet sich mit Hilfe der "
                "Wälzkörpersatzdreh-zahl nach Gleichung 1, dem Teilkreisdurchmesser des Wälzkörpersatzes dws = 54,5 mm und der Masse mwk = 11,2 g "
                "des Wälzkörpers zu:")],
    "pdf035": [("question", "Wie teilt sich im Wälzlagerprüfstand mit dem vollrolligen Prüflager NUP 2208 die aufgebrachte Last zwischen "
                "Prüflager und Gleitlager auf?", None, "B only: copies the anchor")],
    "pdf036": [("note", "uses the document's sample label D3 (A: kept as a lookup question)")],
    "pdf037": [("question", "The dissertation on rotating radial shaft seals illustrates an early Simmerring as a historical example. What year "
                "is that example seal from (not the year the Simmerring was first developed)?", None,
                "A: remove, B: fix; kept with B's wording to keep the en->de pair at 8"),
               ("note", "weak: answer only in a figure caption; Wikipedia gives 1929 for the first Simmerring (a different fact)")],
    "pdf048": [("remove", "Dieser Zusammenhang ist in Abbildung 9 dargestellt")],
}
NEW_GOLD_FROM_OPS = {
    "pdf048": [("innotrac-2020-467", "Die Messungen zeigten, dass bei einer Temperaturerhöhung auch der elektrische Widerstand der Sensorelemente "
                "eine Änderung aufweist.", 1)],
}


def find(golds: list[dict], prefix: str) -> dict:
    hit = [g for g in golds if g["anchor"].startswith(prefix)]
    if len(hit) != 1:
        raise ValueError(f"prefix {prefix!r} matches {len(hit)} gold entries")
    return hit[0]


def main() -> None:
    docs = {d["doc_id"]: d for d in load_corpus("wiki_pdf")}
    queries = [json.loads(l) for l in (DRAFT / "queries_pdf_prereview.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    reviews = {k: {r["qid"]: r for r in json.loads((DRAFT / f"review_output_{k}.json").read_text(encoding="utf-8"))} for k in "AB"}
    log: list[dict] = []
    for q in queries:
        qid = q["qid"]
        # (1) 누락 정답: 두 검수자 제안의 합집합, 같은 문장이면 낮은 등급
        proposed: dict[tuple[str, str], tuple[int, str]] = {}
        for k in "AB":
            for m in reviews[k][qid]["missing_gold"]:
                key = (m["doc_id"], " ".join(m["anchor"].split()))
                g = int(m["grade"])
                prev = proposed.get(key)
                proposed[key] = (min(g, prev[0]), prev[1] + k) if prev else (g, k)
        existing = {(g["doc_id"], " ".join(g["anchor"].split())) for g in q["gold"]}
        for (doc_id, norm), (grade, who) in proposed.items():
            if (doc_id, norm) in existing:
                continue
            anchor = next(m["anchor"] for k in "AB" for m in reviews[k][qid]["missing_gold"]
                          if m["doc_id"] == doc_id and " ".join(m["anchor"].split()) == norm)
            locate_anchor(docs[doc_id]["text"], anchor)            # 원문에 없으면 예외
            q["gold"].append({"doc_id": doc_id, "doc_lang": docs[doc_id]["lang"], "grade": grade, "anchor": anchor})
            log.append({"qid": qid, "change": "add_gold", "doc_id": doc_id, "grade": grade, "proposed_by": who, "anchor": anchor})
        for doc_id, anchor, grade in NEW_GOLD_FROM_OPS.get(qid, []):
            locate_anchor(docs[doc_id]["text"], anchor)
            q["gold"].append({"doc_id": doc_id, "doc_lang": docs[doc_id]["lang"], "grade": grade, "anchor": anchor})
            log.append({"qid": qid, "change": "add_gold", "doc_id": doc_id, "grade": grade, "proposed_by": "A (fix text)", "anchor": anchor})
        # (2) 수동 결정
        for op in OPS.get(qid, []):
            kind = op[0]
            if kind == "question":
                log.append({"qid": qid, "change": "question", "old": q["question"], "new": op[1], "reason": op[3]})
                q["question"] = op[1]
                if op[2]:
                    q["answer"] = op[2]
            elif kind == "grade":
                g = find(q["gold"], op[1])
                log.append({"qid": qid, "change": "grade", "anchor": g["anchor"], "old": g["grade"], "new": op[2]})
                g["grade"] = op[2]
            elif kind == "remove":
                g = find(q["gold"], op[1])
                q["gold"].remove(g)
                log.append({"qid": qid, "change": "remove_gold", "anchor": g["anchor"]})
            elif kind == "anchor":
                g = find(q["gold"], op[1])
                locate_anchor(docs[g["doc_id"]]["text"], op[2])
                log.append({"qid": qid, "change": "anchor", "old": g["anchor"], "new": op[2]})
                g["anchor"] = op[2]
            elif kind == "note":
                q["note"] = "; ".join(filter(None, [q.get("note"), op[1]]))
                log.append({"qid": qid, "change": "note", "note": op[1]})
        if q["gold"][0]["grade"] != 2:
            raise ValueError(f"{qid}: gold[0] must stay grade 2")
    out = REPO / "eval" / "queries_pdf.jsonl"
    out.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in queries), encoding="utf-8")
    (REPO / "eval" / "pdf_review_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    kinds: dict[str, int] = {}
    for e in log:
        kinds[e["change"]] = kinds.get(e["change"], 0) + 1
    print(f"wrote {len(queries)} questions -> {out.relative_to(REPO)}; {len(log)} changes {kinds}")


if __name__ == "__main__":
    main()
