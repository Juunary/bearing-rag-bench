"""PDF sources -> section-structured documents (data/processed/docs_pdf.jsonl), same record shape as docs.jsonl.

[EN]
- Role: the PDF corpus (public domain, CC0, CC BY, CC BY-SA, KOGL Type 1 only; data/pdf_sources.json). Each PDF is
  downloaded to data/raw/pdf/ (not committed), checked against its sha256, and turned into reading-order blocks by
  scripts/pdf_layout_export.mjs (layout reconstruction of the pdf-editor project).
- Block -> text rules: page headers and footers are dropped (running heads, page numbers); a heading paragraph starts a
  new section (path = [heading]); body, list items, captions, footnotes and other paragraphs are kept, one per line;
  a table becomes one line per row "| cell | cell |" (merged cells keep their text in the top-left cell); figure
  labels (axis ticks, legends) and table-of-contents lines (dot leaders ending in a page number) are dropped. Sections named like the boilerplate list of ingest.py
  (References, Literatur, 참고문헌 ...) are dropped, as for Wikipedia.
- Extra fields: source_type "pdf", sha256, pages, extractor {tool, pdf_editor_commit}, blocks [{page, kind, role,
  start, end}] with char offsets into `text` (which page an anchor comes from; tables can be found again).
- Corpora: a manifest entry's `corpus` (default wiki_pdf) picks the output file: wiki_pdf -> docs_pdf.jsonl (the six
  documents of 2026-11-02), wiki_pdf2 -> docs_pdf2.jsonl (practical maintenance documents, 2026-11-17).
- `excludePages` (0-based PDF page indexes, reason in `excludeReason`): pages holding only third-party material are
  dropped whole; the document then records `excluded_pages`.
- Usage: uv run python scripts/build_pdf_docs.py [--pdf-editor /path/to/pdf-editor] [--only id ...]

[KO]
- 역할: PDF 코퍼스(퍼블릭 도메인, CC0, CC BY, CC BY-SA, 공공누리 제1유형만; data/pdf_sources.json). PDF는
  data/raw/pdf/에 내려받고(커밋 안 함) sha256을 확인한 뒤, scripts/pdf_layout_export.mjs(pdf-editor 레이아웃 복원)로
  읽기 순서 블록을 얻는다.
- 블록 -> 텍스트 규칙: 머리말·꼬리말(반복 제목, 쪽 번호)은 버린다. 제목 문단은 새 절을 연다(경로 = [제목]). 본문·목록·
  캡션·각주·기타 문단은 한 줄에 하나씩 남긴다. 표는 행마다 한 줄 "| 칸 | 칸 |"(병합 셀 글자는 왼쪽 위 칸). 그림 안 글자
  (축 눈금, 범례)와 목차 줄(점선 뒤 쪽 번호)은 버린다. 참고문헌류 절(ingest.py 목록)은 위키와 같이 버린다.
- 추가 필드: source_type "pdf", sha256, pages, extractor {tool, pdf_editor_commit}, blocks [{page, kind, role,
  start, end}](text 안의 글자 위치. 근거 문장이 몇 쪽인지, 표가 어디인지 다시 찾을 수 있다).
- 코퍼스: 매니페스트 항목의 corpus(기본 wiki_pdf)로 출력 파일을 고른다. wiki_pdf -> docs_pdf.jsonl(2026-11-02의 6건),
  wiki_pdf2 -> docs_pdf2.jsonl(실무 정비 문서, 2026-11-17).
- excludePages(0부터 센 PDF 쪽, 이유는 excludeReason): 제3자 저작물만 있는 쪽은 통째로 빼고 문서에 excluded_pages를 남긴다.
- 사용: uv run python scripts/build_pdf_docs.py [--pdf-editor /path/to/pdf-editor] [--only id ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.ingest import DROP_SECTIONS, REPO, clean_body  # noqa: E402

SOURCES = REPO / "data" / "pdf_sources.json"
RAW = REPO / "data" / "raw" / "pdf"
OUT = REPO / "data" / "processed" / "docs_pdf.jsonl"
# 매니페스트 항목의 corpus(기본 wiki_pdf)마다 출력 파일이 따로다. wiki_pdf 파일은 기존 6건 그대로 남는다
OUTS = {"wiki_pdf": OUT, "wiki_pdf2": REPO / "data" / "processed" / "docs_pdf2.jsonl"}
EXPORTER = REPO / "scripts" / "pdf_layout_export.mjs"
DROP_ROLES = {"header", "footer"}
# 목차·그림 목록 줄: 점선(". . . ." 또는 "....") 뒤 쪽 번호로 끝난다
_TOC_LEADER = re.compile(r"(?:\.\s?){4,}\s*[0-9ivxlc]+\s*$", re.IGNORECASE)
_NUMBERING = re.compile(r"^\s*(?:[0-9]+(?:\.[0-9]+)*\.?|[IVXLC]+\.|[A-Z]\.)\s+")


def fetch(src: dict[str, Any]) -> Path:
    """Download once to data/raw/pdf/<id>.pdf and verify the sha256 of the manifest (a changed file is an error)."""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{src['id']}.pdf"
    if not path.exists():
        req = urllib.request.Request(src["url"], headers={"User-Agent": "bearing-rag-bench/0.1 (research corpus)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            path.write_bytes(r.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != src["sha256"]:
        raise ValueError(f"{src['id']}: sha256 {digest} does not match the manifest {src['sha256']}")
    return path


def heading_key(text: str) -> str:
    # "5. References" / "IV. LITERATUR" 같은 번호를 떼고 소문자로 비교한다
    return _NUMBERING.sub("", text).strip().rstrip(":").lower()


def table_lines(cells: list[list[str]]) -> list[str]:
    rows = [[" ".join(c.split()) for c in row] for row in cells]
    return ["| " + " | ".join(r) + " |" for r in rows if any(r)]


def corpus_of(src: dict[str, Any]) -> str:
    return src.get("corpus", "wiki_pdf")


def build_doc(src: dict[str, Any], rows: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
    # 1) 블록을 절로 묶는다. 각 절 = [(줄 텍스트, 블록 정보)], 블록 하나가 여러 줄(표의 행)일 수 있다
    # excludePages: 제3자 저작물만 있는 쪽(0부터 센 PDF 쪽 번호, 매니페스트에 이유를 적는다)은 통째로 뺀다
    excluded = set(src.get("excludePages", []))
    sections: list[dict[str, Any]] = [{"path": [], "level": 1, "lines": []}]
    for r in rows:
        if r["kind"] == "figure" or r.get("role") in DROP_ROLES or r["page"] in excluded:
            continue
        if r["kind"] == "paragraph" and r["role"] == "heading":
            sections.append({"path": [" ".join(r["text"].split())], "level": 2, "lines": []})
            continue
        info = {"page": r["page"], "kind": r["kind"], "role": r.get("role")}
        lines = table_lines(r["cells"]) if r["kind"] == "table" else [clean_body(r["text"]).replace("\n", " ")]
        for ln in lines:
            if ln.strip() and not (r["kind"] == "paragraph" and _TOC_LEADER.search(ln)):
                sections[-1]["lines"].append((ln, info))
    sections = [s for s in sections if s["lines"] and not (s["path"] and heading_key(s["path"][-1]) in DROP_SECTIONS)]

    # 2) 절은 빈 줄, 줄은 줄바꿈으로 잇는다 (docs.jsonl과 같은 규칙: 청커가 줄을 문단으로 본다). 블록 위치를 같이 기록한다
    text_parts: list[str] = []
    blocks: list[dict[str, Any]] = []
    pos = 0
    out_sections = []
    for si, s in enumerate(sections):
        if si:
            text_parts.append("\n\n")
            pos += 2
        sec_lines = []
        for li, (ln, info) in enumerate(s["lines"]):
            if li:
                text_parts.append("\n")
                pos += 1
            text_parts.append(ln)
            # 같은 블록(표)의 연속 줄은 블록 하나로 합친다
            if blocks and blocks[-1]["_id"] is info:
                blocks[-1]["end"] = pos + len(ln)
            else:
                blocks.append({"_id": info, **info, "start": pos, "end": pos + len(ln)})
            pos += len(ln)
            sec_lines.append(ln)
        out_sections.append({"path": s["path"], "level": s["level"], "text": "\n".join(sec_lines)})
    text = "".join(text_parts)
    for b in blocks:
        del b["_id"]
    doc = {
        "doc_id": src["id"], "lang": src["lang"], "title": src["title"], "url": src["landingUrl"], "revid": None,
        "license": src["license"], "source_type": "pdf", "pdf_url": src["url"], "sha256": src["sha256"], "pages": meta["pages"],
        "extractor": {"tool": "pdf-editor layout-recon", "pdf_editor_commit": meta["pdfEditorCommit"]},
        "sections": out_sections, "text": text, "n_chars": len(text), "blocks": blocks,
    }
    if excluded:                         # 뺀 쪽이 없는 문서는 기존 레코드와 글자 하나까지 같게 둔다
        doc["excluded_pages"] = sorted(excluded)
    return doc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-editor", default="/mnt/nas4/kjune/pdf-editor", help="pdf-editor checkout with built packages (pnpm build)")
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))["documents"]
    docs = []
    for src in sources:
        if args.only and src["id"] not in args.only:
            continue
        pdf = fetch(src)
        blocks_path = RAW / f"{src['id']}.blocks.jsonl"
        subprocess.run(["node", str(EXPORTER), args.pdf_editor, str(pdf), str(blocks_path)], check=True)
        lines = [json.loads(l) for l in blocks_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        doc = build_doc(src, lines[1:], lines[0]["meta"])
        kinds = {k: sum(b["kind"] == k for b in doc["blocks"]) for k in ("paragraph", "table")}
        print(f"{doc['doc_id']:32} {doc['lang']} pages {doc['pages']:4d} chars {doc['n_chars']:7d} sections {len(doc['sections']):3d} "
              f"paragraphs {kinds['paragraph']:4d} tables {kinds['table']:3d}")
        docs.append(doc)
    if args.only:
        print("--only: docs_pdf*.jsonl not written")
        return
    by_id = {s["id"]: s for s in sources}
    for corpus, out in OUTS.items():
        part = sorted((d for d in docs if corpus_of(by_id[d["doc_id"]]) == corpus), key=lambda d: (d["lang"], d["doc_id"]))
        with open(out, "w", encoding="utf-8") as f:
            for d in part:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"wrote {len(part)} docs -> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
