"""Evaluation set loading and anchor -> chunk mapping.

[EN]
- Role: load eval/queries.jsonl; turn each gold (doc_id, anchor sentence, grade) into
  {chunk_id: grade} for the current chunking.
- Why anchors instead of chunk ids: chunk ids change whenever chunking changes (stage 2);
  anchoring on the sentence text keeps one eval set valid across all chunkings.
- Rule: a chunk is relevant if it covers >= min_overlap (default 0.5) of the anchor's characters.
  If several golds hit one chunk, the highest grade wins.
- locate_anchor: exact substring first, then whitespace-insensitive regex; missing anchor raises
  (a typo in the eval set must surface, not silently score 0).

[KO]
- 역할: eval/queries.jsonl을 읽고, 각 gold(doc_id, 근거 문장, 등급)를 현재 청킹 기준 {청크ID: 등급}으로 바꾼다.
- 청크 ID 대신 근거 문장을 쓰는 이유: 청킹을 바꾸면(2단계) 청크 ID가 전부 바뀐다. 문장에 묶어 두면
  평가셋 하나로 모든 청킹을 평가할 수 있다.
- 규칙: 근거 문장 문자 수의 min_overlap(기본 0.5) 이상을 덮는 청크를 관련 청크로 본다.
  여러 gold가 한 청크에 걸리면 높은 등급을 쓴다.
- locate_anchor: 정확한 부분 문자열 -> 공백 무시 정규식 순. 못 찾으면 예외(평가셋 오타가 0점으로 묻히면 안 된다).
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


def primary_group(q: dict[str, Any]) -> str:
    """Language pair of the question and its primary evidence: "{q_lang}->{gold[0].doc_lang}"."""
    return f"{q['q_lang']}->{q['gold'][0]['doc_lang']}"
