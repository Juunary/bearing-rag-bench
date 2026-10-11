"""HNSW parameter sweep: ANN recall vs exact search, latency, index size, build time.

[EN]
- Role: embed the chunk set once (cached), compute exact top-10 for a query set as ground truth,
  then for every (m, ef_construction) build an index and for every ef_search measure:
  recall@10 against exact, query latency p50/p95 (ms), index bytes, build seconds.
- Queries: eval/queries.jsonl if present, otherwise `--n-fallback` chunk-derived queries (first
  sentence of random chunks). The fallback is for pipeline checks; results are labelled with it.
- Why exact search as truth: HNSW is approximate; "recall" here means how many of the true
  nearest neighbours the graph returns, independent of any human relevance labels.
- Expectation: with ~350 vectors nearly every setting reaches recall 1.0; the sweep is kept
  because the measurement harness matters. --replicate (duplicate vectors with noise) was tried
  and dropped (2026-10-12): near-tie clusters make id-based recall meaningless (0.25-0.54 with no
  ef_search effect). Scale effects are listed as future work in the README.
- Output: experiments/results/s1_hnsw_sweep[_synthetic].json

[KO]
- 역할: 청크 임베딩을 한 번(캐시) 만들고, 질의 집합의 정확 top-10을 기준으로 삼아 (m, ef_construction)
  조합마다 인덱스를 만들고 ef_search마다 recall@10(정확 검색 대비), 지연 p50/p95(ms), 인덱스 바이트,
  빌드 시간을 잰다.
- 질의: eval/queries.jsonl이 있으면 그것, 없으면 `--n-fallback`개의 청크 유래 질의(무작위 청크의 첫
  문장). 폴백은 파이프라인 점검용이며 결과에 표시된다.
- 정확 검색을 기준으로 삼는 이유: HNSW는 근사다. 여기서 "recall"은 사람 라벨과 무관하게 그래프가 진짜
  최근접 이웃을 얼마나 돌려주는지다.
- 예상: 벡터 약 350개면 거의 모든 설정이 recall 1.0에 도달한다. 측정 도구 자체가 의미 있어 유지한다.
  --replicate(노이즈 복제)는 시도 후 폐기(2026-10-12): 근접 동점 군집에서는 ID 기준 recall이 무의미
  (0.25~0.54, ef_search 효과 없음). 규모 효과는 README의 다음 단계로 남긴다.
- 출력: experiments/results/s1_hnsw_sweep[_synthetic].json
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import random
import statistics
import sys
import tempfile
import time
from pathlib import Path

import hnswlib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.chunking import chunk_set_id, load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig, environment_snapshot, set_seed  # noqa: E402
from ragbench.embedding import Embedder  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

GRID_M = [8, 16, 32]
GRID_EFC = [64, 128, 256]
GRID_EF = [16, 64, 128, 256]
K = 10


def exact_topk(emb: np.ndarray, q: np.ndarray, k: int) -> np.ndarray:
    scores = q @ emb.T
    part = np.argpartition(-scores, k - 1, axis=1)[:, :k]
    rows = np.arange(len(q))[:, None]
    order = np.argsort(-scores[rows, part], axis=1)
    return part[rows, order]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-fallback", type=int, default=100)
    ap.add_argument("--replicate", type=int, default=1, help="duplicate vectors N times with noise (synthetic scale test)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    set_seed(args.seed)

    cfg = ChunkingConfig()
    chunks = load_chunks(cfg)
    embedder = Embedder("BAAI/bge-m3")
    emb, emb_info = embedder.encode_chunks_cached(chunks, chunk_set_id(cfg))

    eval_path = REPO / "eval" / "queries.jsonl"
    if eval_path.exists():
        queries = [json.loads(l)["question"] for l in open(eval_path, encoding="utf-8") if l.strip()]
        query_source = f"eval set ({len(queries)} queries)"
    else:
        rng = random.Random(args.seed)
        sample = rng.sample(chunks, min(args.n_fallback, len(chunks)))
        queries = [c["text"].split(". ")[0][:200] for c in sample]
        query_source = f"fallback: first sentence of {len(queries)} random chunks (no eval set yet)"
    qvec = embedder.encode(queries)

    if args.replicate > 1:
        rng = np.random.default_rng(args.seed)
        reps = [emb] + [emb + rng.normal(0, 0.02, emb.shape).astype(np.float32) for _ in range(args.replicate - 1)]
        emb = np.concatenate(reps)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    n = len(emb)
    truth = exact_topk(emb, qvec, K)

    # exact search timed one query at a time, the same way as the HNSW knn_query loop below
    exact_lat = []
    for qi in range(len(qvec)):
        t1 = time.perf_counter()
        exact_topk(emb, qvec[qi:qi + 1], K)
        exact_lat.append(time.perf_counter() - t1)
    exact_ms = statistics.median(exact_lat) * 1000

    rows = []
    for m, efc in itertools.product(GRID_M, GRID_EFC):
        idx = hnswlib.Index(space="ip", dim=emb.shape[1])
        t0 = time.perf_counter()
        idx.init_index(max_elements=n, M=m, ef_construction=efc, random_seed=args.seed)
        idx.add_items(emb, np.arange(n), num_threads=1)   # deterministic graph
        build = time.perf_counter() - t0
        with tempfile.NamedTemporaryFile(suffix=".hnsw", delete=False) as f:
            tmp = f.name
        idx.save_index(tmp); size = os.path.getsize(tmp); os.unlink(tmp)
        for ef in GRID_EF:
            idx.set_ef(max(ef, K))
            lat = []
            hits = 0
            for qi in range(len(qvec)):
                t1 = time.perf_counter()
                labels, _ = idx.knn_query(qvec[qi:qi + 1], k=K)
                lat.append(time.perf_counter() - t1)
                hits += len(set(labels[0].tolist()) & set(truth[qi].tolist()))
            rows.append({"m": m, "ef_construction": efc, "ef_search": ef,
                         "recall@10": hits / (K * len(qvec)),
                         "latency_ms_p50": statistics.median(lat) * 1000,
                         "latency_ms_p95": sorted(lat)[int(0.95 * (len(lat) - 1))] * 1000,
                         "index_bytes": size, "build_seconds": build})
            print(f"m={m:2d} efc={efc:3d} ef={ef:3d}  recall@10={rows[-1]['recall@10']:.3f}  "
                  f"p50={rows[-1]['latency_ms_p50']:.3f}ms  size={size/1024:.0f}KB  build={build:.3f}s")

    result = {
        "exp_id": "s1_hnsw_sweep" + ("_synthetic" if args.replicate > 1 else ""),
        "environment": environment_snapshot(),
        "setup": {"n_vectors": n, "dim": int(emb.shape[1]), "replicate": args.replicate, "k": K,
                  "query_source": query_source, "n_queries": len(qvec), "embedding": emb_info,
                  "model": embedder.model_name, "model_revision": embedder.revision,
                  "exact_latency_ms_p50": exact_ms, "exact_bytes": int(emb.nbytes)},
        "rows": rows,
    }
    out = REPO / "experiments" / "results" / f"{result['exp_id']}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"exact search p50: {exact_ms:.3f} ms/query, {emb.nbytes/1024:.0f}KB | saved -> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
