"""Document-first translation: translate sentence spans in place, keep an original <-> English alignment.

[EN]
- Role: helpers for "translate the document, then chunk" (the alternative to "chunk, then translate").
  The chunker's own sentence spans (chunking.split_sentences) are the translation units. The English
  document is the original text with each span replaced by its translation, so paragraph breaks,
  blank lines and list lines stay where they were, and every unit records
  (orig_start, orig_end, en_start, en_end).
- Gold mapping: an anchor (original char span) is mapped to the English span covered by the units it
  overlaps; the usual >= 50 % chunk overlap rule is then applied on the English chunks.
- Translation request: consecutive lines are grouped into windows of about `max_tokens` source
  tokens and sent as numbered sentences "[1] ... [2] ...". The answer must contain exactly the same
  numbers; otherwise the caller falls back to line-sized windows and then to single sentences.
- Pure functions only (no model calls) so the alignment is unit-tested on CPU.

[KO]
- 역할: "문서를 먼저 번역하고 청킹"(청킹 후 번역의 대안)을 위한 보조 함수. 청커가 쓰는 문장 구간
  (chunking.split_sentences)을 번역 단위로 쓴다. 영어 문서는 원문에서 각 구간만 번역문으로 바꾼 텍스트라
  문단 구분, 빈 줄, 목록 줄이 그대로 남고, 단위마다 (원문 시작, 원문 끝, 영어 시작, 영어 끝)을 기록한다.
- gold 매핑: 근거 문장(원문 글자 범위)이 겹치는 단위들이 덮는 영어 범위로 바꾼 뒤, 영어 청크에
  기존 50% 겹침 규칙을 적용한다.
- 번역 요청: 연속된 줄을 원문 약 `max_tokens` 토큰 단위의 창으로 묶어 "[1] ... [2] ..." 번호 문장으로
  보낸다. 답에 같은 번호가 정확히 있어야 하고, 아니면 호출 쪽이 줄 단위 창, 다시 문장 단위로 되돌린다.
- 모델 호출이 없는 순수 함수라 정렬을 CPU에서 단위 테스트한다.
"""

from __future__ import annotations

import re
from typing import Any

_NUM_LINE = re.compile(r"^\s*\[(\d+)\]\s*(.*\S)?\s*$")


def group_lines(text: str, spans: list[Any]) -> list[list[int]]:
    """Indices of spans grouped by text line (a new line starts when a newline lies between two spans)."""
    lines: list[list[int]] = []
    for i, sp in enumerate(spans):
        if lines and "\n" not in text[spans[i - 1].end:sp.start]:
            lines[-1].append(i)
        else:
            lines.append([i])
    return lines


def make_windows(lines: list[list[int]], spans: list[Any], max_tokens: int = 350) -> list[list[list[int]]]:
    """Pack whole lines into windows of at most `max_tokens` source tokens (a longer single line is its own window).

    A window is a list of lines, a line is a list of span indices, so a failed window can be retried line by line.
    """
    windows: list[list[list[int]]] = []
    cur: list[list[int]] = []
    cur_tokens = 0
    for line in lines:
        n = sum(spans[i].n_tokens for i in line)
        if cur and cur_tokens + n > max_tokens:
            windows.append(cur)
            cur, cur_tokens = [], 0
        cur.append(line)
        cur_tokens += n
    if cur:
        windows.append(cur)
    return windows


def numbered_text(sentences: list[str]) -> str:
    return "\n".join(f"[{i}] {' '.join(s.split())}" for i, s in enumerate(sentences, 1))


def parse_numbered(output: str, n: int) -> list[str] | None:
    """Return the n translations if the output has exactly the numbers 1..n in order, else None."""
    found: list[str] = []
    for line in (output or "").splitlines():
        if not line.strip():
            continue
        m = _NUM_LINE.match(line)
        if not m:
            return None                      # a continuation or comment line: the alignment is not trustworthy
        if int(m.group(1)) != len(found) + 1:
            return None
        found.append(" ".join((m.group(2) or "").split()))
    return found if len(found) == n and all(found) else None


def rebuild(text: str, spans: list[Any], translations: list[str]) -> tuple[str, list[dict[str, int]]]:
    """Replace every span by its translation; return the English text and the alignment units."""
    out: list[str] = []
    units: list[dict[str, int]] = []
    pos_o, pos_e = 0, 0
    for sp, tr in zip(spans, translations):
        gap = text[pos_o:sp.start]
        out.append(gap)
        pos_e += len(gap)
        out.append(tr)
        units.append({"o_start": sp.start, "o_end": sp.end, "e_start": pos_e, "e_end": pos_e + len(tr)})
        pos_e += len(tr)
        pos_o = sp.end
    out.append(text[pos_o:])
    return "".join(out), units


def anchor_to_english_span(o_start: int, o_end: int, units: list[dict[str, int]]) -> tuple[int, int] | None:
    """English char span covered by the units that overlap the original span (None if nothing overlaps)."""
    hit = [u for u in units if min(o_end, u["o_end"]) - max(o_start, u["o_start"]) > 0]
    if not hit:
        return None
    return min(u["e_start"] for u in hit), max(u["e_end"] for u in hit)


def map_gold_docfirst(gold: list[dict[str, Any]], docs: dict[str, dict[str, Any]], units_by_doc: dict[str, list[dict[str, int]]],
                      chunks: list[dict[str, Any]], min_overlap: float = 0.5) -> dict[str, int]:
    """Return {chunk_id: grade} on the chunks of the translated documents.

    `docs` are the ORIGINAL documents (the anchors are original text). For a translated document the anchor
    is mapped to its English span through the alignment units; an English document has no units and its chunks
    are matched with the original rule. A chunk is relevant if it covers >= min_overlap of the (English) span.
    """
    from ragbench.evalset import locate_anchor

    by_doc: dict[str, list[dict[str, Any]]] = {}
    for c in chunks:
        by_doc.setdefault(c["doc_id"], []).append(c)
    out: dict[str, int] = {}
    for g in gold:
        a_start, a_end = locate_anchor(docs[g["doc_id"]]["text"], g["anchor"])
        units = units_by_doc.get(g["doc_id"])
        if units is not None:
            span = anchor_to_english_span(a_start, a_end, units)
            if span is None:
                raise ValueError(f"anchor of {g['doc_id']} overlaps no translated unit: {g['anchor'][:50]!r}")
            a_start, a_end = span
        a_len = max(1, a_end - a_start)
        for c in by_doc.get(g["doc_id"], []):
            ov = min(a_end, c["char_end"]) - max(a_start, c["char_start"])
            if ov > 0 and ov / a_len >= min_overlap:
                out[c["chunk_id"]] = max(out.get(c["chunk_id"], 0), int(g["grade"]))
    if not out:
        raise ValueError("no chunk covers any gold anchor (check alignment / min_overlap)")
    return out
