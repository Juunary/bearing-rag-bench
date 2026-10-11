"""Evaluation set loading and anchor -> chunk mapping.

Gold evidence is written as (doc_id, anchor sentence, grade). At evaluation time the anchor is
located in the document text and every chunk covering at least `min_overlap` of the anchor's
characters becomes a relevant chunk with that grade (if several golds hit one chunk, keep the
highest grade). This keeps eval/queries.jsonl independent of the chunking configuration.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ragbench.ingest import REPO

WS_RE = re.compile(r"\s+")


def load_queries(path: str | Path = REPO / "eval" / "queries.jsonl") -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def locate_anchor(doc_text: str, anchor: str) -> tuple[int, int]:
    """Char span of the anchor in the doc. Exact match first, then whitespace-insensitive."""
    i = doc_text.find(anchor)
    if i >= 0:
        return i, i + len(anchor)
    pattern = r"\s+".join(re.escape(tok) for tok in WS_RE.split(anchor.strip()) if tok)
    m = re.search(pattern, doc_text)
    if m:
        return m.start(), m.end()
    raise ValueError(f"anchor not found in document: {anchor[:60]!r}")


def map_gold_to_chunks(
    gold: list[dict[str, Any]],
    docs_by_id: dict[str, dict[str, Any]],
    chunks: list[dict[str, Any]],
    min_overlap: float = 0.5,
) -> dict[str, int]:
    """Return {chunk_id: grade} for one query."""
    by_doc: dict[str, list[dict[str, Any]]] = {}
    for c in chunks:
        by_doc.setdefault(c["doc_id"], []).append(c)
    out: dict[str, int] = {}
    for g in gold:
        doc = docs_by_id[g["doc_id"]]
        a_start, a_end = locate_anchor(doc["text"], g["anchor"])
        a_len = a_end - a_start
        for c in by_doc.get(g["doc_id"], []):
            ov = min(a_end, c["char_end"]) - max(a_start, c["char_start"])
            if ov > 0 and ov / a_len >= min_overlap:
                out[c["chunk_id"]] = max(out.get(c["chunk_id"], 0), int(g["grade"]))
    if not out:
        raise ValueError("no chunk covers any gold anchor (check anchors / min_overlap)")
    return out


def query_group(q: dict[str, Any], gold_doc_lang: str) -> str:
    return f"{q['q_lang']}->{gold_doc_lang}"
