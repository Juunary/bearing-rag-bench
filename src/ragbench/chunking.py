"""Chunking: fixed token budget, cut at paragraph/sentence boundaries, sentence-level overlap.

Decisions (2026-10-11): unit = tokens of the embedding model's tokenizer (BAAI/bge-m3, XLM-R
vocabulary) because the budget must match what the embedder actually sees; Korean needs ~2.6x
more tokens per character than English/German (measured 1.7 vs 4.1-4.4 chars/token), so a
character budget would give Korean chunks far less content. No title prefix in stage 1.

Algorithm (strategy "fixed"):
  1. Split the document text into paragraphs (one per line in docs.jsonl), each paragraph
     into sentences with a light multilingual regex. Each sentence keeps its char span.
  2. Greedily append sentences while the token count stays <= size. When the next sentence
     would overflow, emit the chunk and start a new one seeded with the trailing sentences of
     the previous chunk whose total tokens <= overlap (sentence-level overlap).
  3. A single sentence longer than `size` is hard-cut on token boundaries (rare: tables, lists).

Chunk ids are "{doc_id}#{idx}". The chunk *set* id encodes the configuration
(e.g. fixed_tok384_ov48) so different chunkings never mix.

Usage: uv run python -m ragbench.chunking [--size 384] [--overlap 48]
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
