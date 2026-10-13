"""Document-first translation: translate whole documents sentence span by sentence span -> data/processed/docs_en/<doc_id>.json.

[EN]
- Role: build step of the "translate the document, then chunk" variant (compare with
  build_english_chunks.py, "chunk, then translate"). Units are the chunker's own sentence spans, so each
  original span has exactly one English span; paragraph breaks, blank lines and list lines stay in place.
- Requests: consecutive lines are packed into windows of about 350 source tokens and sent as numbered
  sentences with the document title and section path as context (ragbench.docfirst, ragbench.translate).
  A window whose answer does not have exactly the numbers 1..n (or was cut off) is retried line by line,
  then sentence by sentence; a sentence that still fails stays in the original language. Every unit
  records the level that produced it ("window" | "line" | "sentence" | "original") and the report counts them.
- English documents are not touched. Output: one JSON per translated document (resumable), merged later by
  the retrieval runner. Two GPUs: run with --shard 0/2 --device cuda:0 and --shard 1/2 --device cuda:1.
- Usage: uv run python experiments/build_english_docs.py [--shard I/N] [--device cuda:0] [--limit N]

[KO]
- 역할: "문서를 먼저 번역하고 청킹" 방식의 빌드 단계(build_english_chunks.py의 "청킹 후 번역"과 비교).
  단위는 청커가 쓰는 문장 구간이라 원문 구간마다 영어 구간이 정확히 하나 있고, 문단 구분·빈 줄·목록 줄은
  제자리에 남는다.
- 요청: 연속된 줄을 원문 약 350토큰 창으로 묶어 문서 제목·절 경로를 문맥으로 붙인 번호 문장으로 보낸다
  (ragbench.docfirst, ragbench.translate). 답에 번호 1..n이 정확히 없거나 잘린 창은 줄 단위로, 다시 문장
  단위로 재시도하고, 그래도 실패한 문장은 원문 언어로 남긴다. 단위마다 만든 단계("window" | "line" |
  "sentence" | "original")를 기록하고 보고서에 센다.
- 영어 문서는 건드리지 않는다. 출력은 번역 문서당 JSON 하나(이어 실행 가능)이며 검색 러너가 합친다.
  GPU 2장: --shard 0/2 --device cuda:0, --shard 1/2 --device cuda:1로 나눠 실행.
- 사용: uv run python experiments/build_english_docs.py [--shard I/N] [--device cuda:0] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import get_token_counter, section_path_at, split_sentences  # noqa: E402
from ragbench.config import ChunkingConfig, set_seed  # noqa: E402
from ragbench.docfirst import group_lines, make_windows, numbered_text, parse_numbered, rebuild  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.translate import Translator  # noqa: E402

OUT_DIR = REPO / "data" / "processed" / "docs_en"


def try_translate(tr: Translator, doc: dict, spans: list, idx: list[int]) -> list[str] | None:
    """Translate the spans `idx` as one numbered request; None if the answer is cut off or not exactly 1..n."""
    r = tr.translate_numbered(numbered_text([spans[i].text for i in idx]), doc["title"], section_path_at(doc, spans[idx[0]].start))
    if r["truncated"]:
        return None
    return parse_numbered(r["text"], len(idx))


def translate_doc(tr: Translator, doc: dict, cfg: ChunkingConfig, count, hard_cut) -> dict:
    # 청커와 같은 함수로 문장 구간을 만든다 (그래야 원문 구간 하나 = 영어 구간 하나)
    spans = split_sentences(doc["text"], count, hard_cut, cfg.size)
    windows = make_windows(group_lines(doc["text"], spans), spans)
    translations: list[str] = [""] * len(spans)
    level: list[str] = [""] * len(spans)

    def put(idx: list[int], texts: list[str], how: str) -> None:
        for i, t in zip(idx, texts):
            translations[i], level[i] = t, how

    for window in windows:
        flat = [i for line in window for i in line]
        got = try_translate(tr, doc, spans, flat)
        if got:
            put(flat, got, "window")
            continue
        for line in window:                       # 창 실패 -> 줄 단위 재시도
            got = try_translate(tr, doc, spans, line)
            if got:
                put(line, got, "line")
                continue
            for i in line:                        # 줄 실패 -> 문장 단위 재시도
                got = try_translate(tr, doc, spans, [i])
                if got:
                    put([i], got, "sentence")
                else:                             # 끝내 실패하면 원문 문장을 그대로 두고 표시한다
                    put([i], [spans[i].text], "original")
    text_en, units = rebuild(doc["text"], spans, translations)
    for u, how in zip(units, level):
        u["level"] = how
    return {"doc_id": doc["doc_id"], "lang": doc["lang"], "text_en": text_en, "units": units,
            "levels": dict(Counter(level)), "n_spans": len(spans)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0/1", help="I/N: this process takes documents with index %% N == I")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--limit", type=int, default=None, help="smoke test: translate only the first N documents of the shard")
    args = ap.parse_args()
    i_shard, n_shard = (int(x) for x in args.shard.split("/"))
    set_seed(42)

    cfg = ChunkingConfig()
    count, hard_cut = get_token_counter(cfg)
    docs = sorted((d for d in load_docs() if d["lang"] != "en"), key=lambda d: d["doc_id"])
    mine = [d for k, d in enumerate(docs) if k % n_shard == i_shard]
    if args.limit:
        mine = mine[:args.limit]
    tr = Translator(REPO / "logs" / f"translate_docfirst_cache_{i_shard}of{n_shard}.sqlite", device=args.device)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    for k, doc in enumerate(mine, 1):
        out_path = OUT_DIR / f"{doc['doc_id']}.json"
        if out_path.exists() and not args.limit:      # 이미 끝난 문서는 건너뛴다 (이어 실행)
            print(f"[{k}/{len(mine)}] {doc['doc_id']} exists, skipped", flush=True)
            continue
        res = translate_doc(tr, doc, cfg, count, hard_cut)
        target = out_path if not args.limit else OUT_DIR / f"_smoke_{doc['doc_id']}.json"
        target.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        print(f"[{k}/{len(mine)}] {doc['doc_id']:40} spans={res['n_spans']:4d} levels={res['levels']} "
              f"elapsed={time.perf_counter() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
