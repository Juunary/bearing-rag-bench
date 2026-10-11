"""Run all eval questions through the serving pipeline twice (cold cache, then warm cache).

[EN]
- Role: end-to-end check of stage 3.5 with the real models: retrieval (BM25 + dense + RRF + reranker),
  Qwen3 generation, LLM cache, output validation and request logging.
- Pass 1 starts with an empty cache, pass 2 reuses it. Reported: cache hit rate and latency of both
  passes, how many answers are blocked and why, and whether the raw answers equal the stage-3
  generation results (same prompt, same context => must be identical).
- The cache file and the request log live under logs/ (git-ignored). The cache is deleted at the
  start so a run never inherits answers from an earlier model or prompt.
- Retrieval models run on cuda:0 and the generator on generation.device (cuda:1) to fit 12 GB cards.
- Usage: uv run python experiments/run_pipeline.py configs/s35_pipeline.json

[KO]
- 역할: 실제 모델로 3.5단계를 끝에서 끝까지 확인한다: 검색(BM25 + dense + RRF + 리랭커), Qwen3 생성, LLM
  캐시, 출력 검증, 요청 로깅.
- 1회차는 빈 캐시로 시작하고 2회차는 그 캐시를 재사용한다. 보고: 두 회차의 캐시 히트율과 지연, 차단된
  답변 수와 사유, 원본 답변이 3단계 생성 결과와 같은지(같은 프롬프트, 같은 컨텍스트 => 같아야 함).
- 캐시 파일과 요청 로그는 logs/ 아래(git 무시). 이전 모델·프롬프트의 답을 물려받지 않도록 시작할 때
  캐시를 지운다.
- 검색 모델은 cuda:0, 생성기는 generation.device(cuda:1)에 올려 12GB GPU에 맞춘다.
- 사용: uv run python experiments/run_pipeline.py configs/s35_pipeline.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks, primary_group  # noqa: E402
from ragbench.generation import Generator  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.metrics import aggregate  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever  # noqa: E402


def pct(vals: list[float], p: float) -> float:
    return sorted(vals)[int(p * (len(vals) - 1))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--stage3-result", default="s3_gen_cite_refuse_v1")
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    g = cfg.generation
    set_seed(cfg.seed)

    docs = {d["doc_id"]: d for d in load_docs()}
    chunks = load_chunks(cfg.chunking)
    queries = load_queries(REPO / cfg.eval_path)
    stage3 = {p["qid"]: p for p in json.loads((REPO / "experiments" / "results" / f"{args.stage3_result}.json").read_text(encoding="utf-8"))["per_query"]}

    retriever = build_retriever(cfg)
    retriever.index(chunks)
    generator = Generator(g.model, device=g.device)

    cache_path = REPO / "logs" / f"{cfg.exp_id}_cache.sqlite"
    for suffix in ("", "-wal", "-shm"):
        Path(str(cache_path) + suffix).unlink(missing_ok=True)
    log_path = REPO / "logs" / "requests.jsonl"
    cache, logger = LLMCache(cache_path), RequestLogger(log_path)
    pipe = RAGPipeline(retriever, chunks, generator, cache, logger, prompt_version=g.prompt_version,
                       context_k=g.context_k, max_new_tokens=g.max_new_tokens, config_id=cfg.exp_id)

    passes: dict[str, list] = {"cold": [], "warm": []}
    for name in ("cold", "warm"):
        for q in queries:
            r = pipe.answer(q["question"], lang=q["q_lang"], request_id=f"{cfg.exp_id}-{q['qid']}-{name}")
            passes[name].append((q, r))
        print(f"pass {name}: cache hits {cache.hits}, misses {cache.misses}, entries {len(cache)}")

    per_query, stats = [], {}
    for (q, cold), (_, warm) in zip(passes["cold"], passes["warm"]):
        gold = map_gold_to_chunks(q["gold"], docs, chunks, cfg.anchor_min_overlap)
        gold_in_ctx = any(c in gold for c in cold.context_ids)
        s3 = stage3[q["qid"]]
        match = cold.raw_answer == s3["answer"] and cold.context_ids == s3["context_ids"]
        per_query.append({
            "qid": q["qid"], "group": primary_group(q), "question": q["question"], "lang": q["q_lang"],
            "context_ids": cold.context_ids, "raw_answer": cold.raw_answer, "answer": cold.answer,
            "block_reason": cold.reason, "warm_identical": warm.answer == cold.answer,
            "cold_ms": {k: round(v, 1) for k, v in cold.timings_ms.items()}, "warm_ms": {k: round(v, 1) for k, v in warm.timings_ms.items()},
            "metrics": {"blocked": float(cold.blocked), "gold_in_context": float(gold_in_ctx), "matches_stage3": float(match),
                        "warm_cache_hit": float(warm.cache_hit), "warm_identical": float(warm.answer == cold.answer)},
        })
    reasons = Counter(p["block_reason"] for p in per_query if p["block_reason"])
    both = Counter((p["metrics"]["gold_in_context"], p["metrics"]["blocked"]) for p in per_query)
    agg = aggregate(per_query, "group")
    lat = lambda name, key: [r.timings_ms[key] for _, r in passes[name]]
    result = ExperimentResult(
        config=cfg.to_dict(), environment=environment_snapshot(),
        metrics={"overall": agg.pop("overall"), "by_group": agg}, per_query=per_query,
        timing={name: {k: {"p50": statistics.median(lat(name, k)), "p95": pct(lat(name, k), 0.95)} for k in ("retrieve", "generate", "total")}
                for name in passes},
        extra={"block_reasons": dict(reasons),
               "gold_in_context_x_blocked": {f"gold_in_context={int(a)},blocked={int(b)}": n for (a, b), n in sorted(both.items())},
               "cache_entries": len(cache), "cache_hits": cache.hits, "cache_misses": cache.misses,
               "model": g.model, "model_revision": generator.revision, "prompt_version": g.prompt_version,
               "log_file": str(log_path.relative_to(REPO)), "log_lines_total": len(logger.read())},
    )
    path = result.save()
    print("overall:", {k: round(v, 3) for k, v in result.metrics["overall"].items()})
    print("block reasons:", dict(reasons), "| gold_in_context x blocked:", result.extra["gold_in_context_x_blocked"])
    print("latency (ms) cold:", {k: round(v["p50"]) for k, v in result.timing["cold"].items()}, "warm:", {k: round(v["p50"]) for k, v in result.timing["warm"].items()})
    print(f"saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
