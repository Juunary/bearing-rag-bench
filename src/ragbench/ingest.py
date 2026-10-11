"""Raw Wikipedia extracts -> clean, section-structured documents (data/processed/docs.jsonl).

[EN]
- Role: parse TextExtracts plain text ("== Title ==" markers) into sections with heading paths,
  drop boilerplate sections (See also / References / Einzelnachweise / 같이 보기 ...),
  normalise whitespace, keep paragraph boundaries for the chunker.
- Output record: doc_id, lang, title, url, revid, license, sections[{path, level, text}],
  text (sections joined by blank line), n_chars.
- Why TextExtracts (not HTML parsing): one API call gives clean prose with section markers,
  enough for structure-based chunking in stage 2. Cost: tables and infoboxes are lost (limitation).
- Why docs.jsonl is committed: Wikipedia text is CC BY-SA 4.0, and the eval set's anchor
  sentences must point at an exact revision; pinning the text keeps the eval set stable.
- Language tag comes from the source list (per-wiki), no language detection needed.

[KO]
- 역할: TextExtracts 평문("== 제목 ==" 마커)을 절 단위로 나누고 제목 경로를 붙인다. 각주·같이 보기류
  절은 버리고, 공백을 정리하되 문단 경계는 청킹용으로 남긴다.
- 출력: doc_id, lang, title, url, revid, license, sections[{path, level, text}], text(절을 빈 줄로
  이어 붙임), n_chars.
- TextExtracts를 고른 이유: API 한 번으로 절 마커가 있는 깨끗한 본문을 얻어 2단계 구조 기반 청킹에
  충분하다. 대가로 표·인포박스는 사라진다(한계로 기록).
- docs.jsonl을 커밋하는 이유: 위키 본문은 CC BY-SA 4.0이고, 평가셋의 근거 문장은 특정 리비전 텍스트를
  가리켜야 한다. 텍스트를 고정해야 평가셋이 깨지지 않는다.
- 언어 태그는 출처 목록(언어별 위키)에서 오므로 언어 감지가 필요 없다.
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
