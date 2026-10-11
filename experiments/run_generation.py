"""Generate answers for every eval question from stored retrieval results -> results/<exp_id>.json.

[EN]
- Role: read the ranked chunk ids of an earlier retrieval experiment (generation.retrieval_result),
  put the top context_k chunks into the prompt, generate with the local model, parse the answer and
  save everything needed to inspect or grade it later (prompt, answer, token counts, latency).
- Why consume stored retrieval results: the prompt context is exactly what the retrieval metrics
  were measured on, retrieval models need not be loaded next to the LLM, and generation stays
  deterministic (greedy) and cheap to rerun.
- Automatic metrics (all 0/1 or a share, averaged over queries): refused, has_citation,
  citations_valid, cites_gold, sentence_coverage, gold_in_context (does the prompt contain a gold
  chunk at all - the retrieval-failure indicator). They check form and grounding, not correctness;
  correctness, faithfulness and relevance are graded in the evaluation step.
- Usage: uv run python experiments/run_generation.py configs/s3_gen_cite_v1.json [--limit 3]

[KO]
- 역할: 앞선 검색 실험(generation.retrieval_result)의 순위 청크 ID를 읽어 상위 context_k개를 프롬프트에
  넣고, 로컬 모델로 생성하고, 답변을 파싱해 나중에 확인·채점할 수 있게 전부 저장한다(프롬프트, 답변,
  토큰 수, 지연).
- 저장된 검색 결과를 쓰는 이유: 프롬프트 컨텍스트가 검색 지표를 잰 것과 정확히 같고, LLM 옆에 검색
  모델을 올릴 필요가 없으며, 생성이 결정적(greedy)이라 다시 돌리기 싸다.
- 자동 지표(0/1 또는 비율의 평균): refused, has_citation, citations_valid, cites_gold,
  sentence_coverage, gold_in_context(프롬프트에 정답 청크가 하나라도 있는가, 검색 실패 지표). 형식과
  근거 연결을 보는 것이지 정확성이 아니다. 정확성·충실도·관련성은 평가 단계에서 채점한다.
- 사용: uv run python experiments/run_generation.py configs/s3_gen_cite_v1.json [--limit 3]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks, primary_group  # noqa: E402
from ragbench.generation import Generator, build_messages, parse_answer  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.metrics import aggregate  # noqa: E402


def adapter_hash(adapter: str | None) -> str | None:
    if not adapter:
        return None
    import hashlib

    f = REPO / adapter / "adapter_model.safetensors"
    return hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--limit", type=int, help="only the first N questions (smoke test, result is not saved)")
    args = ap.parse_args()

    cfg = ExperimentConfig.load(args.config)
    g = cfg.generation
    set_seed(cfg.seed)
    docs = {d["doc_id"]: d for d in load_docs()}
    chunks = load_chunks(cfg.chunking)
    by_id = {c["chunk_id"]: c for c in chunks}

    retrieval = json.loads((REPO / "experiments" / "results" / f"{g.retrieval_result}.json").read_text(encoding="utf-8"))
    ranked_by_qid = {p["qid"]: p["ranked"] for p in retrieval["per_query"]}
    queries = load_queries(REPO / cfg.eval_path)
    if args.limit:
        queries = queries[: args.limit]

    gen = Generator(g.model, device=g.device, quantize_4bit=g.quantize_4bit, adapter=str(REPO / g.adapter) if g.adapter else None)
    per_query, latencies = [], []
    for q in queries:
        gold = map_gold_to_chunks(q["gold"], docs, chunks, cfg.anchor_min_overlap)
        ctx_ids = ranked_by_qid[q["qid"]][: g.context_k]
        messages = build_messages(g.prompt_version, q["question"], [by_id[i] for i in ctx_ids])
        out = gen.generate(messages, max_new_tokens=g.max_new_tokens)
        parsed = parse_answer(out["text"], ctx_ids, gold)
        latencies.append(out["seconds"])
        metrics = {k: float(parsed[k]) for k in ("refused", "has_citation", "citations_valid", "cites_gold", "sentence_coverage")}
        metrics["gold_in_context"] = float(any(i in gold for i in ctx_ids))
        per_query.append({
            "qid": q["qid"], "group": primary_group(q), "q_lang": q["q_lang"], "question": q["question"],
            "context_ids": ctx_ids, "gold": gold, "messages": messages, "answer": out["text"],
            "prompt_tokens": out["prompt_tokens"], "completion_tokens": out["completion_tokens"],
            "seconds": round(out["seconds"], 3), "parsed": parsed, "metrics": metrics,
        })
        print(f"{q['qid']} [{primary_group(q)}] {out['completion_tokens']:3d} tok {out['seconds']:.1f}s | {out['text'][:90]!r}")

    if args.limit:
        return
    agg = aggregate(per_query, "group")
    result = ExperimentResult(
        config=cfg.to_dict(), environment=environment_snapshot(),
        metrics={"overall": agg.pop("overall"), "by_group": agg}, per_query=per_query,
        timing={"generation_seconds": {"p50": statistics.median(latencies), "p95": sorted(latencies)[int(0.95 * (len(latencies) - 1))],
                                        "total": sum(latencies)},
                "tokens": {"prompt_mean": statistics.fmean(p["prompt_tokens"] for p in per_query),
                           "completion_mean": statistics.fmean(p["completion_tokens"] for p in per_query)}},
        extra={"model": g.model, "model_revision": gen.revision, "quantize_4bit": g.quantize_4bit, "adapter": g.adapter,
               "adapter_sha256": adapter_hash(g.adapter), "retrieval_result": g.retrieval_result,
               "retrieval_git_commit": retrieval["environment"]["git_commit"]},
    )
    path = result.save()
    print(f"overall: { {k: round(v, 3) for k, v in result.metrics['overall'].items()} }")
    print(f"saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
