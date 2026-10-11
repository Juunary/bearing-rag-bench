"""Chunking: fixed token budget, cut at paragraph/sentence boundaries, sentence-level overlap.

[EN]
- Role: docs.jsonl -> chunks_{set_id}.jsonl with chunk_id "{doc_id}#{idx}", text, char offsets
  (needed to map eval anchors), token count and section path.
- Decisions (2026-10-11):
  - Unit = tokens of the embedding model's tokenizer (BAAI/bge-m3, XLM-R vocab) so the budget
    equals what the embedder sees. Measured 1.7 chars/token for Korean vs 4.1-4.4 for en/de: a
    character budget would give Korean chunks ~2.6x less content.
  - Size 384, overlap 48 (stage 1 baseline; 256/512 compared in stage 2).
  - Cut at paragraph/sentence boundaries, not hard token cuts, so anchor sentences rarely
    straddle chunks. Hard cut only when one sentence exceeds the budget (lists, tables).
  - Overlap is sentence-level: the next chunk starts with the trailing sentences of the previous
    one, bounded by `overlap` tokens AND by what still fits under `size`.
  - No title/section prefix in stage 1 (kept for the stage 2 contextual-retrieval comparison).
- Algorithm: split paragraphs -> sentences (light multilingual regex; over-splitting German
  "z. B." only adds cut candidates) -> greedy packing -> emit with exact char spans.
- Chunk set id (e.g. fixed_tok384_ov48) keeps different chunkings in separate files.
- Usage: uv run python -m ragbench.chunking [--size 384] [--overlap 48]

[KO]
- 역할: docs.jsonl -> chunks_{set_id}.jsonl. 청크 ID "{doc_id}#{idx}", 본문, 문자 오프셋(평가셋 anchor
  매핑에 필요), 토큰 수, 절 경로를 담는다.
- 결정(2026-10-11):
  - 단위 = 임베딩 모델 토크나이저(BAAI/bge-m3, XLM-R 어휘)의 토큰. 예산이 임베더가 보는 길이와 일치한다.
    측정값: 한국어 1.7자/토큰 vs en/de 4.1~4.4자/토큰. 문자 기준이면 한국어 청크 내용이 약 2.6배 적어진다.
  - 크기 384, 오버랩 48(1단계 기준선, 2단계에서 256/512 비교).
  - 토큰 수에서 딱 자르지 않고 문단·문장 경계에서 자른다. 근거 문장이 청크 경계에 걸치는 일을 줄인다.
    한 문장이 예산을 넘을 때만(목록·표) hard cut.
  - 오버랩은 문장 단위: 다음 청크가 이전 청크의 끝 문장들로 시작. `overlap` 토큰과 `size` 잔여분 둘 다로 제한.
  - 1단계는 제목/절 제목을 붙이지 않는다(2단계 contextual retrieval 비교를 위해 남겨 둠).
- 알고리즘: 문단 -> 문장(가벼운 다국어 정규식; 독일어 "z. B."가 과분할돼도 자를 후보만 늘어남)
  -> 탐욕적 채우기 -> 정확한 문자 범위로 출력.
- 청크 세트 ID(예: fixed_tok384_ov48)로 청킹 설정별 파일을 분리한다.
- 사용: uv run python -m ragbench.chunking [--size 384] [--overlap 48]
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ragbench.config import ChunkingConfig
from ragbench.ingest import DOCS_PATH, REPO, load_docs

PROCESSED = REPO / "data" / "processed"

# Sentence end: terminal punctuation (Latin or CJK) followed by whitespace. Over-splits German
# abbreviations ("z. B.") which only adds cut candidates, never loses text.
SENT_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")

TokenCounter = Callable[[str], int]


@dataclass
class Span:
    text: str
    start: int   # char offset in doc["text"]
    end: int
    n_tokens: int


def chunk_set_id(cfg: ChunkingConfig) -> str:
    return f"{cfg.strategy}_{'tok' if cfg.unit == 'token' else 'chr'}{cfg.size}_ov{cfg.overlap}"


def get_token_counter(cfg: ChunkingConfig):
    """Returns (count_fn, hard_cut_fn). Char unit needs no tokenizer."""
    if cfg.unit == "char":
        return len, lambda text, limit: [text[i:i + limit] for i in range(0, len(text), limit)]
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg.tokenizer)

    def count(text: str) -> int:
        return len(tok(text, add_special_tokens=False)["input_ids"])

    def hard_cut(text: str, limit: int) -> list[str]:
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        offs = enc["offset_mapping"]
        pieces = []
        for i in range(0, len(offs), limit):
            s = offs[i][0]
            e = offs[min(i + limit, len(offs)) - 1][1]
            pieces.append(text[s:e])
        return pieces

    return count, hard_cut


def split_sentences(text: str, count: TokenCounter, hard_cut, limit: int) -> list[Span]:
    """Paragraph -> sentence spans with absolute char offsets; oversized sentences hard-cut."""
    spans: list[Span] = []
    pos = 0
    for para in text.split("\n"):
        p_start = text.index(para, pos) if para else pos
        pos = p_start + len(para)
        if not para.strip():
            continue
        cursor = p_start
        for sent in SENT_SPLIT_RE.split(para):
            if not sent.strip():
                continue
            s_start = text.index(sent, cursor)
            cursor = s_start + len(sent)
            n = count(sent)
            if n <= limit:
                spans.append(Span(sent, s_start, cursor, n))
            else:
                sub_cursor = s_start
                for piece in hard_cut(sent, limit):
                    ps = text.index(piece, sub_cursor)
                    sub_cursor = ps + len(piece)
                    spans.append(Span(piece, ps, sub_cursor, count(piece)))
    return spans


def pack(spans: list[Span], size: int, overlap: int) -> list[list[Span]]:
    chunks: list[list[Span]] = []
    cur: list[Span] = []
    cur_tokens = 0
    for sp in spans:
        if cur and cur_tokens + sp.n_tokens > size:
            chunks.append(cur)
            # seed next chunk with trailing sentences within the overlap budget, but never so
            # many that the incoming sentence no longer fits in `size`
            budget = min(overlap, size - sp.n_tokens)
            tail: list[Span] = []
            t = 0
            for prev in reversed(cur):
                if t + prev.n_tokens > budget:
                    break
                tail.insert(0, prev)
                t += prev.n_tokens
            cur, cur_tokens = tail, t
        cur.append(sp)
        cur_tokens += sp.n_tokens
    if cur:
        chunks.append(cur)
    return chunks


def section_path_at(doc: dict[str, Any], offset: int) -> list[str]:
    """Section whose text contains the char offset (sections are joined with '\\n\\n')."""
    pos = 0
    for s in doc["sections"]:
        end = pos + len(s["text"])
        if offset < end:
            return s["path"]
        pos = end + 2
    return doc["sections"][-1]["path"] if doc["sections"] else []


def chunk_document(doc: dict[str, Any], cfg: ChunkingConfig, count, hard_cut) -> list[dict[str, Any]]:
    spans = split_sentences(doc["text"], count, hard_cut, cfg.size)
    out = []
    for idx, group in enumerate(pack(spans, cfg.size, cfg.overlap)):
        start, end = group[0].start, group[-1].end
        text = doc["text"][start:end]
        out.append({
            "chunk_id": f"{doc['doc_id']}#{idx}", "doc_id": doc["doc_id"], "lang": doc["lang"],
            "idx": idx, "text": text, "char_start": start, "char_end": end,
            "n_tokens": count(text), "section_path": section_path_at(doc, start),
            "section_path_end": section_path_at(doc, max(start, end - 1)),   # chunks may span sections
        })
    return out


def chunks_path(cfg: ChunkingConfig) -> Path:
    return PROCESSED / f"chunks_{chunk_set_id(cfg)}.jsonl"


def build_chunks(cfg: ChunkingConfig, docs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    docs = docs or load_docs(DOCS_PATH)
    count, hard_cut = get_token_counter(cfg)
    chunks = []
    for d in docs:
        chunks.extend(chunk_document(d, cfg, count, hard_cut))
    return chunks


def load_chunks(cfg: ChunkingConfig) -> list[dict[str, Any]]:
    path = chunks_path(cfg)
    if not path.exists():
        chunks = build_chunks(cfg)
        save_chunks(chunks, path)
        return chunks
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_chunks(chunks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="fixed")
    ap.add_argument("--unit", default="token")
    ap.add_argument("--size", type=int, default=384)
    ap.add_argument("--overlap", type=int, default=48)
    args = ap.parse_args()
    cfg = ChunkingConfig(strategy=args.strategy, unit=args.unit, size=args.size, overlap=args.overlap)
    chunks = build_chunks(cfg)
    path = chunks_path(cfg)
    save_chunks(chunks, path)
    by_lang: dict[str, list[int]] = {}
    for c in chunks:
        by_lang.setdefault(c["lang"], []).append(c["n_tokens"])
    for lang, toks in sorted(by_lang.items()):
        toks_s = sorted(toks)
        print(f"{lang}: {len(toks):4d} chunks, tokens min {toks_s[0]} median {toks_s[len(toks)//2]} max {toks_s[-1]}, mean {sum(toks)/len(toks):.0f}")
    print(f"wrote {len(chunks)} chunks -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
