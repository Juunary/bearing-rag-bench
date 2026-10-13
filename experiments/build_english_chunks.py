"""Translate the non-English chunks to English -> data/processed/chunks_en_<chunk set id>.jsonl.

[EN]
- Role: offline step of the English-pivot BM25. Same chunk ids as the original chunk set, so the
  evaluation set, gold mapping and metrics are untouched; only the text used by BM25 changes.
- English chunks are copied unchanged (never sent to the model). Korean and German chunks are
  translated with ragbench.translate (Qwen3-4B-Instruct-2507, greedy, cached in SQLite, resumable).
- Output rows: chunk_id, lang, text (English), translated (bool), truncated (bool), seconds.
- Usage: uv run python experiments/build_english_chunks.py [--limit N] [--device cuda:0]

[KO]
- 역할: 영어 피벗 BM25의 오프라인 단계. 원래 청크 세트와 청크 ID가 같아서 평가셋, gold 매핑, 지표는
  그대로이고 BM25가 쓰는 텍스트만 바뀐다.
- 영어 청크는 그대로 복사한다(모델에 보내지 않음). 한국어·독일어 청크는 ragbench.translate
  (Qwen3-4B-Instruct-2507, greedy, SQLite 캐시, 이어 실행 가능)로 번역한다.
- 출력 행: chunk_id, lang, text(영어), translated, truncated, seconds.
- 사용: uv run python experiments/build_english_chunks.py [--limit N] [--device cuda:0]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import chunk_set_id, load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig, set_seed  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.translate import Translator  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="translate only the first N non-English chunks (smoke test)")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--cache", default=str(REPO / "logs" / "translate_cache.sqlite"))
    args = ap.parse_args()
    set_seed(42)

    # 청크는 기존 청킹 설정 그대로 읽는다 (청크 ID가 같아야 평가셋·gold가 그대로 유효)

    cfg = ChunkingConfig()
    chunks = load_chunks(cfg)
    out_path = REPO / "data" / "processed" / f"chunks_en_{chunk_set_id(cfg)}.jsonl"
    tr = Translator(args.cache, device=args.device)

    # 영어 청크는 모델에 보내지 않고 원문 그대로 쓴다 (번역 오류가 끼어들 여지를 없앰)
    todo = [c for c in chunks if c["lang"] != "en"]
    if args.limit:
        todo = todo[:args.limit]
    # 청크 하나씩 번역. 캐시 덕분에 중간에 끊겨도 같은 명령으로 이어서 실행된다
    done, t0 = {}, time.perf_counter()
    for i, c in enumerate(todo, 1):
        r = tr.translate(c["text"], "passage")
        done[c["chunk_id"]] = r
        print(f"[{i}/{len(todo)}] {c['chunk_id']:40} {c['lang']} {c['n_tokens']:4d} tok -> {r['completion_tokens']:4d} tok "
              f"{r['seconds']:5.1f}s{' CACHED' if r['from_cache'] else ''}{' TRUNCATED' if r['truncated'] else ''}", flush=True)
    # --limit은 속도·품질 확인용이라 부분 결과로 파일을 덮어쓰지 않는다
    if args.limit:
        print("smoke test only; no output file written")
        return

    # 원래 청크 순서대로 출력: 번역한 것은 영어 텍스트, 영어 청크는 원문 + translated=False
    rows = []
    for c in chunks:
        r = done.get(c["chunk_id"])
        rows.append({"chunk_id": c["chunk_id"], "lang": c["lang"], "text": r["text"] if r else c["text"],
                     "translated": r is not None, "truncated": bool(r and r["truncated"]),
                     "seconds": r["seconds"] if r else 0.0})
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # 잘린 번역 수를 보고한다 (0이 아니면 BM25 입력이 불완전하다는 뜻)
    n_trunc = sum(r["truncated"] for r in rows)
    print(f"wrote {len(rows)} rows -> {out_path.relative_to(REPO)}; translated {len(done)}, truncated {n_trunc}, "
          f"wall {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
