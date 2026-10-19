"""Latency, throughput and GPU memory of the serving pipeline with the real models (cold caches, then warm).

[EN]
- Role: measure what one request costs, stage by stage, for a serving config (configs/s35_pipeline.json =
  original retrieval, configs/s6_pipeline_en.json = English pivot with English reranker input).
- Method: build the real pipeline; the translation cache and the LLM cache are EMPTY in the cold pass (a
  filled translation cache would hide the query translation). N questions of the 90-question set are
  taken evenly over the set and asked one after another (the server also runs one request at a time).
  Cold pass = every stage runs; warm pass = the same questions again, answered from the caches.
- Per request: retrieval (includes query translation and reranking), query translation (generation
  seconds), reranking, generation, total, generated tokens per second. GPU memory after the cold pass:
  torch peak allocation per device and nvidia-smi used memory.
- Usage: uv run python experiments/bench_service.py configs/s35_pipeline.json [--n 30]

[KO]
- 역할: 서비스 설정(configs/s35_pipeline.json = 원문 검색, configs/s6_pipeline_en.json = 영어 피벗 +
  리랭커 영어 입력)에서 요청 하나의 비용을 단계별로 잰다.
- 방법: 실제 파이프라인을 만들고, 차가운 회차에서는 번역 캐시와 LLM 캐시를 비워 둔다(번역 캐시가 차 있으면
  질의 번역이 가려진다). 90문항에서 고르게 N개를 뽑아 하나씩 차례로 묻는다(서버도 한 번에 하나씩 처리).
  차가운 회차 = 모든 단계 실행, 따뜻한 회차 = 같은 질문을 캐시로 응답.
- 요청마다: 검색(질의 번역과 리랭킹 포함), 질의 번역(생성 시간), 리랭킹, 생성, 전체, 초당 생성 토큰.
  차가운 회차 뒤의 GPU 메모리: 장치별 torch 최대 할당과 nvidia-smi 사용량.
- 사용: uv run python experiments/bench_service.py configs/s35_pipeline.json [--n 30]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, environment_snapshot, set_seed  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.generation import Generator  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever, use_cold_translation_cache  # noqa: E402


def stats(xs: list[float]) -> dict[str, float]:
    xs = sorted(xs)
    return {"p50": statistics.median(xs), "p95": xs[int(0.95 * (len(xs) - 1))], "mean": statistics.fmean(xs), "max": xs[-1]} if xs else {}


def translate_ms(retriever) -> float:
    """Query translation cost of the last request: generation milliseconds, 0 when it came from the cache or there is none."""
    stack = [retriever]
    while stack:
        r = stack.pop()
        log = getattr(r, "query_log", None)
        if log:
            return 0.0 if log[-1].get("from_cache") or log[-1].get("skipped") else 1000 * log[-1]["seconds"]
        stack.extend(getattr(r, "retrievers", []))
        stack.extend(x for x in (getattr(r, "base", None), getattr(r, "en", None)) if x is not None)
    return 0.0


def smi() -> dict[str, int]:
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    return {f"cuda:{ln.split(',')[0].strip()}": int(ln.split(",")[1]) for ln in out.strip().splitlines()}


def main() -> None:
    import torch

    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--n", type=int, default=30)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    g = cfg.generation
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)
    base_mem = smi()
    queries = load_queries(REPO / "eval" / "queries_v2.jsonl")
    step = max(1, len(queries) // args.n)
    questions = [q["question"] for q in queries[::step][: args.n]]

    t0 = time.perf_counter()
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    n_tr = use_cold_translation_cache(retriever)
    t_retr = time.perf_counter() - t0
    t0 = time.perf_counter()
    generator = Generator(g.model, device=g.device)
    t_gen = time.perf_counter() - t0
    tmp = Path(tempfile.mkdtemp())
    pipe = RAGPipeline(retriever, chunks, generator, LLMCache(":memory:"), RequestLogger(tmp / "log.jsonl"),
                       prompt_version=g.prompt_version, context_k=g.context_k, max_new_tokens=g.max_new_tokens, config_id=f"bench:{cfg.exp_id}")
    rerankers = [r for r in (retriever, getattr(retriever, "base", None)) if hasattr(r, "last_rerank_seconds")]

    def run(label: str) -> dict:
        rows = []
        t_start = time.perf_counter()
        for qtext in questions:
            r = pipe.answer(qtext)
            rows.append({
                "retrieve_ms": r.timings_ms.get("retrieve", 0.0), "generate_ms": r.timings_ms.get("generate", 0.0), "total_ms": r.timings_ms["total"],
                "translate_ms": translate_ms(retriever),
                "rerank_ms": 1000 * rerankers[0].last_rerank_seconds if rerankers else 0.0,
                "completion_tokens": r.completion_tokens, "cache_hit": r.cache_hit, "blocked": r.blocked})
        wall = time.perf_counter() - t_start
        out = {"pass": label, "wall_s": wall, "queries_per_minute": 60 * len(questions) / wall,
               **{k: stats([x[k] for x in rows]) for k in ("retrieve_ms", "translate_ms", "rerank_ms", "generate_ms", "total_ms")},
               "blocked": sum(x["blocked"] for x in rows), "cache_hits": sum(x["cache_hit"] for x in rows)}
        gen_rows = [x for x in rows if not x["cache_hit"] and x["generate_ms"] > 0]
        out["generated_tokens_per_second"] = stats([1000 * x["completion_tokens"] / x["generate_ms"] for x in gen_rows])
        return out

    cold = run("cold")
    mem = {"torch_peak_gib": {f"cuda:{i}": round(torch.cuda.max_memory_allocated(i) / 2**30, 2) for i in range(torch.cuda.device_count())},
           "nvidia_smi_used_mib": smi(), "nvidia_smi_before_load_mib": base_mem}
    warm = run("warm")
    result = {"config": cfg.to_dict(), "environment": environment_snapshot(), "n_questions": len(questions), "translators": n_tr,
              "startup_s": {"retrieval_build_and_index": t_retr, "generator_load": t_gen}, "memory": mem, "cold": cold, "warm": warm}
    path = REPO / "experiments" / "results" / f"bench_service_{cfg.exp_id}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("n_questions", "startup_s", "memory")}, indent=1))
    for p in (cold, warm):
        print(f"\n[{p['pass']}] wall {p['wall_s']:.0f}s, {p['queries_per_minute']:.1f} questions/min, cache hits {p['cache_hits']}, blocked {p['blocked']}")
        for k in ("retrieve_ms", "translate_ms", "rerank_ms", "generate_ms", "total_ms"):
            print(f"  {k:12} p50 {p[k]['p50']:8.1f}  p95 {p[k]['p95']:8.1f}  mean {p[k]['mean']:8.1f}")
        if p["generated_tokens_per_second"]:
            print(f"  generated tokens/s p50 {p['generated_tokens_per_second']['p50']:.1f}")
    print("saved ->", path.relative_to(REPO))


if __name__ == "__main__":
    main()
