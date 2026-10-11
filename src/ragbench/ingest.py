"""Turn raw Wikipedia extracts (data/raw/wiki/*.json) into clean section-structured documents.

Output: data/processed/docs.jsonl, one document per line:
    {"doc_id", "lang", "title", "url", "revid", "license",
     "sections": [{"path": ["Overall design", "Ball bearing"], "level": 3, "text": "..."}],
     "text": "<all section texts joined>", "n_chars"}

- The TextExtracts plain text marks headings as ``== Title ==`` (level = number of '=').
- Boilerplate sections (See also / References / Einzelnachweise / 같이 보기 ...) are dropped.
- Runs of blank lines are collapsed; paragraph boundaries ("\n") are kept for chunking.
- Wikipedia text is CC BY-SA 4.0, so the processed file is committed to pin the exact revision
  the evaluation set's anchor sentences refer to.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RAW_WIKI = REPO / "data" / "raw" / "wiki"
DOCS_PATH = REPO / "data" / "processed" / "docs.jsonl"

HEADING_RE = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$")

DROP_SECTIONS = {
    # en
    "see also", "references", "external links", "further reading", "notes", "bibliography",
    "sources", "citations", "footnotes", "gallery",
    # de
    "siehe auch", "einzelnachweise", "literatur", "weblinks", "anmerkungen", "quellen",
    "belege", "fußnoten",
    # ko
    "같이 보기", "각주", "외부 링크", "참고 문헌", "참고문헌", "참고 자료", "주석", "출처",
}


def parse_sections(text: str) -> list[dict[str, Any]]:
    """Split extract text into sections with their heading path. Lead section has path []."""
    sections: list[dict[str, Any]] = []
    path: list[str] = []
    buf: list[str] = []
    level = 1

    def flush() -> None:
        body = clean_body("\n".join(buf))
        if body:
            sections.append({"path": list(path), "level": level, "text": body})
        buf.clear()

    for line in text.split("\n"):
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            path = path[: level - 2] + [title]     # level 2 -> depth 1
        else:
            buf.append(line)
    flush()

    return [s for s in sections if not (s["path"] and s["path"][-1].lower() in DROP_SECTIONS)]


def clean_body(body: str) -> str:
    body = body.replace(" ", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in body.split("\n")]
    out: list[str] = []
    for ln in lines:
        if ln:
            out.append(ln)
        elif out and out[-1] != "":
            out.append("")
    return "\n".join(out).strip()


def build_doc(raw: dict[str, Any]) -> dict[str, Any]:
    sections = parse_sections(raw["text"])
    full = "\n\n".join(s["text"] for s in sections)
    return {
        "doc_id": raw["doc_id"], "lang": raw["lang"], "title": raw["title"], "url": raw["url"],
        "revid": raw["revid"], "license": raw["license"],
        "sections": sections, "text": full, "n_chars": len(full),
    }


def load_docs(path: Path = DOCS_PATH) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    raws = sorted(RAW_WIKI.glob("*.json"))
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    docs = [build_doc(json.loads(p.read_text(encoding="utf-8"))) for p in raws]
    docs.sort(key=lambda d: (d["lang"], d["doc_id"]))
    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    by_lang: dict[str, list[int]] = {}
    for d in docs:
        by_lang.setdefault(d["lang"], []).append(d["n_chars"])
    for lang, sizes in sorted(by_lang.items()):
        print(f"{lang}: {len(sizes):2d} docs, {sum(sizes):7d} chars, min {min(sizes)}, median {sorted(sizes)[len(sizes)//2]}, max {max(sizes)}")
    print(f"wrote {len(docs)} docs -> {DOCS_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
