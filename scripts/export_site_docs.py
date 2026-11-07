"""Export the "PDF -> chunks" and "OKF" sets of the site -> docs/data/pdfdocs.json, pdfchunks.json, okf.json.

[EN]
- Role: two sets of the GitHub Pages site that need no model:
  - pdfdocs: for each of the 6 PDF documents, what the layout reconstruction produced (paragraph roles, tables, figures),
    what was dropped (headers, footers, figures, table-of-contents lines, reference sections), the sections, and every chunk
    (char span, tokens, section, sentence overlap with the previous chunk, repeated table header). Examples: three
    consecutive chunks (overlap) and one chunk that starts inside a table (caption + header row repeated).
    pdfchunks.json carries the text (and the English translation of German chunks) of every PDF chunk for the dialog.
  - okf: the 24 reviewed guide pages of the knowledge bundle (data/kb; aliases ko/en/de, related links, verified, author,
    body) and the 40 questions a person wrote blind (eval/kb/questions.jsonl, questions2.jsonl) answered through the bundle
    only: round 1 = kb_first on 12 pages (all pages in the context), round 2 = kb_matched on 24 pages (matched + related
    pages). Each question carries the page match, the context pages, the answer, the blind item id and the person's grade,
    plus the grade of the RAG answer to the same question for comparison. Nothing is regenerated.
- Raw block counts come from data/raw/pdf/<id>.blocks.jsonl (not committed); when absent they are omitted.
- Usage: uv run python scripts/export_site_docs.py

[KO]
- 역할: 모델 없이 만드는 사이트 세트 2개.
  - pdfdocs: PDF 6건 각각에 대해 레이아웃 복원이 만든 것(문단 역할·표·그림), 버린 것(머리말·꼬리말·그림·목차 줄·참고문헌 절),
    절, 청크 전부(문자 범위·토큰·절·이전 청크와의 문장 오버랩·표 머리글 반복). 예시: 연속 청크 3개(오버랩)와 표 중간에서
    시작하는 청크 1개(캡션 + 머리글 반복). pdfchunks.json은 대화상자용으로 PDF 청크 전부의 본문(독일어는 영어 번역도)을 담는다.
  - okf: 지식 번들의 검수된 안내 페이지 24쪽(data/kb; 별칭 ko/en/de, 관련 링크, 검수, 작성자, 본문)과 사람이 블라인드로 쓴
    질문 40개(eval/kb/questions.jsonl, questions2.jsonl)의 번들 전용 답변: 1차 = 12쪽 kb_first(페이지 전부), 2차 = 24쪽
    kb_matched(매칭 + related). 질문마다 페이지 매칭, 컨텍스트 페이지, 답변, 블라인드 항목 ID와 사람 채점, 비교용으로 같은 질문의
    RAG 답변 채점을 싣는다. 다시 생성하지 않는다.
- 원본 블록 수는 data/raw/pdf/<id>.blocks.jsonl(커밋 안 함)에서 읽고, 없으면 뺀다.
- 사용: uv run python scripts/export_site_docs.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from ragbench.chunking import PROCESSED  # noqa: E402
from ragbench.concepts import LANGS, load_concepts  # noqa: E402
from ragbench.ingest import DROP_SECTIONS  # noqa: E402

OUT = REPO / "docs" / "data"
CHUNKS = PROCESSED / "chunks_fixed_tok384_ov48_pdf_th.jsonl"          # 서비스·PDF 세트의 청크 파일 (크기 384, 오버랩 48, 표 머리글)
CHUNKS_EN = PROCESSED / "chunks_en_fixed_tok384_ov48_pdf_th.jsonl"
RAW = REPO / "data" / "raw" / "pdf"
# 2차 페이지 12쪽 (2026-11-05 추가, data/kb_review.md "Second round")
ROUND2 = {"bearing_selection_basics", "lubrication_method_choice", "shaft_misalignment", "bearing_temperature",
          "bearing_noise_diagnosis", "electric_motor_bearing", "gearbox_bearing_failure", "wheel_hub_bearing_replacement",
          "cv_joint_boot_service", "shaft_seat_repair", "bearing_reuse_assessment", "bearing_designation"}
ROUNDS = [
    {"round": 1, "dir": "eval/kb", "questions": "eval/kb/questions.jsonl", "mode": "kb_first", "context": "all"},
    {"round": 2, "dir": "eval/kb2", "questions": "eval/kb/questions2.jsonl", "mode": "kb_matched", "context": "matched"},
]
_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def build_pdf_docs_module():
    """scripts/build_pdf_docs.py as a module (its TOC regex and heading_key are reused for the dropped-line counts)."""
    spec = importlib.util.spec_from_file_location("build_pdf_docs", REPO / "scripts" / "build_pdf_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def raw_counts(doc_id: str, bpd) -> dict | None:
    """What the layout reconstruction produced and what build_pdf_docs dropped, from the raw block file."""
    path = RAW / f"{doc_id}.blocks.jsonl"
    if not path.exists():
        return None
    rows = [r for r in jsonl(path) if "meta" not in r]
    roles = Counter(r["role"] for r in rows if r["kind"] == "paragraph")
    figures = Counter(r["figureKind"] for r in rows if r["kind"] == "figure")
    toc = sum(1 for r in rows if r["kind"] == "paragraph" and r["role"] not in bpd.DROP_ROLES and r["role"] != "heading"
              and bpd._TOC_LEADER.search(" ".join(r["text"].split())))
    dropped_sections = [" ".join(r["text"].split()) for r in rows if r["kind"] == "paragraph" and r["role"] == "heading"
                        and bpd.heading_key(" ".join(r["text"].split())) in DROP_SECTIONS]
    return {"paragraphs": dict(roles), "tables": sum(1 for r in rows if r["kind"] == "table"), "figures": dict(figures),
            "dropped": {"header": roles.get("header", 0), "footer": roles.get("footer", 0), "figure": sum(figures.values()),
                        "toc_lines": toc, "sections": dropped_sections}}


def export_pdfdocs() -> None:
    bpd = build_pdf_docs_module()
    docs = {d["doc_id"]: d for d in jsonl(PROCESSED / "docs_pdf.jsonl")}
    chunks = [c for c in jsonl(CHUNKS) if c["doc_id"] in docs]
    en = {c["chunk_id"]: c for c in jsonl(CHUNKS_EN) if c["chunk_id"].rsplit("#", 1)[0] in docs}
    order = [d["id"] for d in json.loads((REPO / "data" / "pdf_sources.json").read_text(encoding="utf-8"))["documents"]]
    out, texts = [], {}
    for doc_id in order:
        d = docs[doc_id]
        # 절의 문자 범위: 절 본문을 "\n\n"으로 이었다 (ragbench.chunking.section_path_at와 같은 규칙)
        sections, pos = [], 0
        for s in d["sections"]:
            sections.append({"path": s["path"], "level": s["level"], "start": pos, "end": pos + len(s["text"]), "chunks": []})
            pos += len(s["text"]) + 2
        kept = Counter(f"{b['kind']}:{b['role']}" if b["kind"] == "paragraph" else b["kind"] for b in d["blocks"])
        mine = sorted((c for c in chunks if c["doc_id"] == doc_id), key=lambda c: c["idx"])
        rows, prev_end = [], None
        for c in mine:
            sec = next((i for i, s in enumerate(sections) if s["start"] <= c["char_start"] < s["end"]), len(sections) - 1)
            sections[sec]["chunks"].append(c["idx"])
            ov = max(0, prev_end - c["char_start"]) if prev_end is not None else 0
            rows.append({"idx": c["idx"], "start": c["char_start"], "end": c["char_end"], "tokens": c["n_tokens"], "section": sec,
                         "th": c.get("table_header_prefix", 0), "ov_prev": ov, "spans": c["section_path"] != c["section_path_end"]})
            prev_end = c["char_end"]
            e = en.get(c["chunk_id"], {})
            texts[c["chunk_id"]] = {"doc": doc_id, "title": d["title"], "lang": d["lang"], "text": c["text"],
                                    **({"en": e["text"]} if e.get("translated") else {})}
        # 예시 1: 앞뒤 모두 오버랩이 있고 표 머리글이 없는 연속 청크 3개 (문서 앞부분의 표지·목차는 피한다)
        ex_overlap = None
        for i in range(max(1, len(rows) // 10), len(rows) - 2):
            trio = rows[i:i + 3]
            if all(r["ov_prev"] > 0 and not r["th"] for r in trio[1:]) and not trio[0]["th"]:
                ex_overlap = [r["idx"] for r in trio]
                break
        ex_table = next((r["idx"] for r in rows if r["th"]), None)
        toks = [r["tokens"] for r in rows]
        ovs = [r["ov_prev"] for r in rows[1:]]
        out.append({
            "id": doc_id, "lang": d["lang"], "title": d["title"], "url": d["url"], "pdf_url": d["pdf_url"], "license": d["license"],
            "pages": d["pages"], "sha256": d["sha256"], "extractor": d["extractor"], "n_chars": d["n_chars"],
            "raw": raw_counts(doc_id, bpd), "kept": dict(kept), "sections": sections, "chunks": rows,
            "stats": {"n_chunks": len(rows), "tokens_mean": round(mean(toks), 1), "tokens_min": min(toks), "tokens_max": max(toks),
                      "overlap_chars_mean": round(mean(ovs), 1) if ovs else 0, "n_overlap": sum(1 for o in ovs if o > 0),
                      "n_th": sum(1 for r in rows if r["th"]), "n_spanning": sum(1 for r in rows if r["spans"])},
            "examples": {"overlap": ex_overlap, "table": ex_table},
        })
        print("pdfdocs", doc_id, len(rows), "chunks", "overlap example", ex_overlap, "table example", ex_table)
    meta = {"chunk_set": CHUNKS.stem, "size": 384, "overlap": 48, "unit": "token (BAAI/bge-m3 tokenizer)", "table_header": True,
            "extractor": "pdf-editor layout-recon", "n_docs": len(out), "n_chunks": sum(x["stats"]["n_chunks"] for x in out),
            "n_corpus_chunks": sum(1 for _ in jsonl(CHUNKS))}
    (OUT / "pdfdocs.json").write_text(json.dumps({"meta": meta, "docs": out}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "pdfchunks.json").write_text(json.dumps(texts, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("pdfdocs", meta)


def page_meta(path: Path) -> dict:
    import yaml

    m = _FRONT.match(path.read_text(encoding="utf-8"))
    return yaml.safe_load(m.group(1)) if m else {}


def export_okf() -> None:
    kbdir = REPO / "data" / "kb"
    pages = load_concepts(kbdir)
    backlinks: dict[str, list[str]] = {c.id: [] for c in pages}
    for c in pages:
        for r in c.related:
            if r in backlinks:
                backlinks[r].append(c.id)
    page_rows = [{"id": c.id, "title": c.title, "names": {lang: c.names.get(lang, []) for lang in LANGS}, "related": c.related,
                  "verified": c.verified, "author": page_meta(kbdir / f"{c.id}.md").get("author", ""),
                  "round": 2 if c.id in ROUND2 else 1, "body": c.description, "n_chars": len(c.description),
                  "backlinks": backlinks[c.id]} for c in pages]
    questions, rounds = [], []
    for spec in ROUNDS:
        d = REPO / spec["dir"]
        res = json.loads((d / "results.json").read_text(encoding="utf-8"))
        sample = json.loads((d / "sample.json").read_text(encoding="utf-8"))["items"]
        labels = json.loads((d / "labels.json").read_text(encoding="utf-8"))
        qmeta = {q["qid"]: q for q in jsonl(REPO / spec["questions"])}

        def grade(qid: str, mode: str) -> dict | None:
            it = next((s for s in sample if s["qid"] == qid and mode in s["modes"]), None)
            if it is None:
                return None
            lab = labels["labels"].get(it["item"], {})
            return {"item": it["item"], **{k: lab[k] for k in ("correctness", "refusal", "note") if k in lab}}

        for row in res["rows"]:
            m = row["modes"][spec["mode"]]
            mt = m.get("match") or {}
            rec = {"qid": row["qid"], "round": spec["round"], "question": row["question"], "scope": qmeta[row["qid"]]["scope"],
                   "topic": row["topic"], "path": m.get("path"),
                   "match": {k: mt.get(k) for k in ("alias", "dense", "ids", "related", "ids_with_related", "canonical_names")},
                   "dense_best": mt.get("dense_best"), "rag": grade(row["qid"], "rag")}
            if m.get("path") == "bundle":
                rec.update({"answer": m["answer"], "raw_answer": m.get("raw"), "blocked": m["blocked"], "reason": m["reason"],
                            "context_ids": m["context_ids"],
                            "pages": [c.removeprefix("kb_").rsplit("#", 1)[0] for c in m["context_ids"]],
                            "gen": {"prompt_tokens": m["prompt_tokens"], "completion_tokens": m["completion_tokens"], "seconds": m["seconds"]},
                            "human": grade(row["qid"], spec["mode"])})
            questions.append(rec)
        s = res["summary"][spec["mode"]]
        rounds.append({"round": spec["round"], "mode": spec["mode"], "context": spec["context"], "kb_pages": res["kb_pages"],
                       "kb_verified": res["kb_verified"], "n": s["n"], "fallback": s.get("fallback"), "blocked": s["blocked"],
                       "prompt_tokens_mean": s["prompt_tokens_mean"], "seconds_mean": s["seconds_mean"],
                       "results": f"{spec['dir']}/results.json", "labels": f"{spec['dir']}/labels.json",
                       "graded_by": labels["graded_by"], "graded_on": labels["graded_on"], "questions": spec["questions"],
                       "model": res["model"], "prompt_version": res["prompt_version"], "dense_min": res["kb_dense_min"]})
        print("okf round", spec["round"], len(res["rows"]), "questions")
    meta = {"n_pages": len(page_rows), "n_verified": sum(p["verified"] for p in page_rows), "rounds": rounds, "bundle": "data/kb",
            "review": "data/kb_review.md"}
    (OUT / "okf.json").write_text(json.dumps({"meta": meta, "pages": page_rows, "questions": questions}, ensure_ascii=False,
                                             separators=(",", ":")), encoding="utf-8")
    print("okf", len(page_rows), "pages", len(questions), "questions")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    export_pdfdocs()
    export_okf()


if __name__ == "__main__":
    main()
