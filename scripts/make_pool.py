"""Build the relevance-judgement pool: chunks retrieved by any v2 configuration that are not gold yet.

[EN]
- Role: the gold of the 90 questions comes from one annotator's anchor sentences, so a chunk that answers
  the question but is not gold counts as a wrong answer (an unfair penalty). Pooling collects, for every
  question, the top `--depth` chunks of EVERY v2 retrieval configuration on the 384-token chunk set, removes
  the chunks that are already gold, and asks independent judges for a label.
- Blind: the judge file holds only an id, the question and the chunk text (no config, rank, document id).
- Controls: for every shard, known gold chunks (expected label >= 1) and random chunks of other documents
  (expected label 0) are mixed in under ordinary ids so the judges' accuracy can be measured.
- Chunk-size variants (c256, c512) use other chunk ids and are excluded.
- Output: eval/pool/pool_index.json (id -> qid, chunk_id, control kind; NOT given to the judges) and
  eval/pool/label_input_<k>.jsonl (judge input, `--shards` files).
- Usage: uv run python scripts/make_pool.py [--depth 5] [--shards 5]

[KO]
- 역할: 90문항의 gold는 한 명의 근거 문장에서 나왔으므로, 질문에 답하는데 gold가 아닌 청크는 오답으로 센다
  (부당한 감점). 풀링은 질문마다 384토큰 청크 세트의 모든 v2 검색 설정의 상위 `--depth`개를 모으고, 이미
  gold인 청크를 빼고, 독립 판정자에게 라벨을 요청한다.
- 블라인드: 판정 파일에는 id, 질문, 청크 본문만 있다(설정, 순위, 문서 id 없음).
- 대조군: 샤드마다 알려진 gold 청크(기대 라벨 >= 1)와 다른 문서의 무작위 청크(기대 라벨 0)를 평범한 id로 섞어
  판정자의 정확도를 잴 수 있게 한다.
- 청크 크기 변형(c256, c512)은 청크 id가 달라 제외한다.
- 출력: eval/pool/pool_index.json(id -> qid, chunk_id, 대조군 종류; 판정자에게는 주지 않음)과
  eval/pool/label_input_<k>.jsonl(판정 입력, `--shards`개).
- 사용: uv run python scripts/make_pool.py [--depth 5] [--shards 5]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--shards", type=int, default=5)
    ap.add_argument("--controls-per-shard", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    docs = {d["doc_id"]: d for d in load_docs()}
    chunks = load_chunks(ChunkingConfig())
    text = {c["chunk_id"]: c["text"] for c in chunks}
    queries = load_queries(REPO / "eval" / "queries_v2.jsonl")
    gold = {q["qid"]: set(map_gold_to_chunks(q["gold"], docs, chunks)) for q in queries}

    used, pool = [], {q["qid"]: set() for q in queries}
    for p in sorted((REPO / "experiments" / "results").glob("v2_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("config", {}).get("stage") != "v2" or d["config"].get("chunking", {}).get("size", 384) != 384:
            continue                       # 검색 실행만, 그리고 384토큰 청크 세트만
        used.append(p.stem)
        for q in d["per_query"]:
            pool[q["qid"]] |= set(q["ranked"][: args.depth]) - gold[q["qid"]]

    items = [{"qid": qid, "chunk_id": cid, "control": None} for qid in gold for cid in sorted(pool[qid])]
    # 대조군: 알려진 gold 청크(양성)와 질문의 정답 문서가 아닌 다른 문서의 무작위 청크(음성)
    qlist = {q["qid"]: q for q in queries}
    controls = []
    for k in range(args.shards * args.controls_per_shard):
        qid = rng.choice(sorted(gold))
        if k % 2 == 0:
            controls.append({"qid": qid, "chunk_id": rng.choice(sorted(gold[qid])), "control": "gold"})
        else:
            gold_docs = {g["doc_id"] for g in qlist[qid]["gold"]}
            cid = rng.choice([c["chunk_id"] for c in chunks if c["doc_id"] not in gold_docs and c["chunk_id"] not in pool[qid]])
            controls.append({"qid": qid, "chunk_id": cid, "control": "random"})
    rng.shuffle(items)
    rows = items + controls
    rng.shuffle(rows)
    out_dir = REPO / "eval" / "pool"
    out_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    shards = [[] for _ in range(args.shards)]
    for n, r in enumerate(rows):
        pid = f"p{n:04d}"
        index[pid] = r
        shards[n % args.shards].append({"id": pid, "question": qlist[r["qid"]]["question"], "chunk_text": text[r["chunk_id"]]})
    for k, rows_k in enumerate(shards):
        with open(out_dir / f"label_input_{k}.jsonl", "w", encoding="utf-8") as f:
            for r in rows_k:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out_dir / "pool_index.json").write_text(json.dumps({"configs": used, "depth": args.depth, "items": index}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"configs pooled: {len(used)}; candidates (not gold): {len(items)} over {len(gold)} questions "
          f"(mean {len(items) / len(gold):.1f}); controls: {len(controls)}; shards: {[len(s) for s in shards]}")


if __name__ == "__main__":
    main()
