"""Judge stored generation results with a local LLM and classify every answer's outcome.

[EN]
- Role: for each answer of one or more generation result files, obtain faithfulness, answer relevance,
  context relevance and correctness judgements (src/ragbench/judge.py) and assign an outcome class.
- Outcome classes (which stage to fix):
  - ok: gold chunk in the prompt, answer correct and faithful.
  - generation_failure: gold chunk in the prompt, but the answer is incorrect or not faithful.
  - retrieval_failure: no gold chunk in the prompt and the model still answered (correctness is kept
    as a label: a wrong answer is expected, a correct one is lucky or from another valid chunk).
  - correct_refusal: refused and no gold chunk in the prompt.
  - over_refusal: refused although a gold chunk was in the prompt.
  Refusal = the NO_ANSWER sentinel or a natural-language refusal in the first sentence (the same rule
  as the output validation).
- Reported per file: rate of YES per dimension among the answers it applies to, the judge's context
  relevance versus the gold label (a check of the judge), outcome counts, and rates by language pair.
- A judgement whose verdict line is missing (reasoning cut off by the 80-token limit) is asked again once
  with three times the limit; a second failure stays unparsable (None) and is excluded from the rates.
- Usage: uv run python experiments/run_judge.py configs/s3_judge.json s3_gen_cite_v1 s3_gen_cite_refuse_v1

[KO]
- 역할: 생성 결과 파일의 답변마다 충실도·답변 관련성·컨텍스트 관련성·정확성 판정(src/ragbench/judge.py)을 받고
  결과 유형을 붙인다.
- 결과 유형(어느 단계를 고칠지):
  - ok: 정답 청크가 프롬프트에 있고 답이 맞고 충실하다.
  - generation_failure: 정답 청크가 프롬프트에 있는데 답이 틀렸거나 충실하지 않다.
  - retrieval_failure: 정답 청크가 프롬프트에 없는데 모델이 답했다(정확성은 라벨로 남김: 틀린 답이
    예상이고 맞았다면 우연이거나 다른 유효한 청크 덕분이다).
  - correct_refusal: 거절했고 정답 청크가 프롬프트에 없었다.
  - over_refusal: 정답 청크가 프롬프트에 있는데 거절했다.
  거절 = NO_ANSWER 센티널 또는 첫 문장의 자연어 거절(출력 검증과 같은 규칙).
- 파일별 보고: 해당되는 답변 중 항목별 YES 비율, 정답 라벨 대비 판정 모델의 컨텍스트 관련성(판정 모델
  점검), 결과 유형별 개수, 언어쌍별 비율.
- 판정 줄이 없는 응답(추론이 80토큰 한도에서 잘림)은 한도를 3배로 늘려 한 번 더 묻고, 그래도 실패하면 파싱
  불가(None)로 남겨 비율 계산에서 뺀다.
- 사용: uv run python experiments/run_judge.py configs/s3_judge.json s3_gen_cite_v1 s3_gen_cite_refuse_v1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.judge import JUDGE_PROMPT_VERSION, Judge, build_judge_messages, parse_verdict, select_passages  # noqa: E402
from ragbench.validation import validate_answer  # noqa: E402

DIMS = ("faithfulness", "answer_relevance", "context_relevance", "correctness")


def outcome(refused: bool, gold_in_ctx: bool, correct: bool | None, faithful: bool | None) -> str:
    if refused:
        return "over_refusal" if gold_in_ctx else "correct_refusal"
    if not gold_in_ctx:
        return "retrieval_failure"
    return "ok" if (correct and faithful) else "generation_failure"


def rate(vals: list) -> tuple[float | None, int]:
    vals = [v for v in vals if v is not None]
    return (sum(vals) / len(vals) if vals else None), len(vals)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("results", nargs="+", help="generation result names, e.g. s3_gen_cite_v1")
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)

    chunks = load_chunks(cfg.chunking)
    by_id = {c["chunk_id"]: c for c in chunks}
    queries = {q["qid"]: q for q in load_queries(REPO / cfg.eval_path)}
    cache = LLMCache(REPO / "logs" / "judge_cache.sqlite")
    judge = Judge(cfg.generation.model, cache=cache)
    n_calls = n_cached = n_retries = 0

    for name in args.results:
        src = json.loads((REPO / "experiments" / "results" / f"{name}.json").read_text(encoding="utf-8"))
        per_query = []
        # 평가셋은 생성 결과에 기록된 경로를 쓴다 (판정 설정의 기본값은 45문항 평가셋이라 v2 결과가 KeyError가 난다)
        queries = {q["qid"]: q for q in load_queries(REPO / src["config"].get("eval_path", cfg.eval_path))}
        for p in src["per_query"]:
            q = queries[p["qid"]]
            ctx_ids, answer = p["context_ids"], p["answer"]
            verdict = validate_answer(answer, ctx_ids)
            refused = verdict.reason in ("refusal_sentinel", "refusal_text")
            gold_in_ctx = bool(p["metrics"]["gold_in_context"])
            labels, reasons = {}, {}
            for dim in DIMS:
                if refused and dim != "context_relevance":
                    labels[dim], reasons[dim] = None, "n/a (refusal)"
                    continue
                if dim == "context_relevance":
                    msgs = build_judge_messages(dim, q["question"], passages=[by_id[i] for i in ctx_ids])
                elif dim == "faithfulness":
                    msgs = build_judge_messages(dim, q["question"], answer=answer, passages=select_passages(answer, ctx_ids, by_id))
                elif dim == "answer_relevance":
                    msgs = build_judge_messages(dim, q["question"], answer=answer)
                else:
                    msgs = build_judge_messages(dim, q["question"], answer=answer, references=[g["anchor"] for g in q["gold"]])
                out = judge.ask(msgs, max_new_tokens=cfg.generation.max_new_tokens)
                n_calls += 1
                n_cached += out["cached"]
                verdict_label = parse_verdict(out["text"])
                if verdict_label is None:      # the reasoning was cut off before the verdict line: ask once more with 3x the budget
                    out = judge.ask(msgs, max_new_tokens=cfg.generation.max_new_tokens * 3)
                    n_calls += 1
                    n_cached += out["cached"]
                    n_retries += 1
                    verdict_label = parse_verdict(out["text"])
                labels[dim], reasons[dim] = verdict_label, out["text"]
            cls = outcome(refused, gold_in_ctx, labels["correctness"], labels["faithfulness"])
            per_query.append({"qid": p["qid"], "group": p["group"], "question": p["question"], "answer": answer,
                              "refused": refused, "gold_in_context": gold_in_ctx, "labels": labels, "reasons": reasons, "outcome": cls})
            print(f"{name} {p['qid']} [{p['group']}] {cls:18} " + " ".join(f"{d[:4]}={'-' if labels[d] is None else int(labels[d])}" for d in DIMS))

        overall, groups = {}, defaultdict(lambda: defaultdict(list))
        for d in DIMS:
            r, n = rate([x["labels"][d] for x in per_query])
            overall[d], overall[f"{d}_n"] = r, n
        agree = [x["labels"]["context_relevance"] == x["gold_in_context"] for x in per_query if x["labels"]["context_relevance"] is not None]
        overall["judge_context_vs_gold_agreement"] = sum(agree) / len(agree) if agree else None
        overall["n"] = len(per_query)
        for x in per_query:
            for d in DIMS:
                groups[x["group"]][d].append(x["labels"][d])
        by_group = {g: {**{d: rate(v)[0] for d, v in dims.items()}, "n": len(dims["correctness"])} for g, dims in sorted(groups.items())}
        exp_cfg = cfg.to_dict()
        exp_cfg["exp_id"] = f"{cfg.exp_id}_{name.removeprefix('s3_gen_')}"
        exp_cfg["description"] = f"{cfg.description}; judged file: {name}"
        result = ExperimentResult(
            config=exp_cfg, environment=environment_snapshot(), metrics={"overall": overall, "by_group": by_group}, per_query=per_query,
            extra={"judged_result": name, "judge_model": cfg.generation.model, "judge_model_revision": judge.revision,
                   "judge_prompt_version": JUDGE_PROMPT_VERSION, "outcomes": dict(Counter(x["outcome"] for x in per_query)),
                   "judge_calls": n_calls, "judge_cache_hits": n_cached, "judge_retries_for_cut_off_verdict": n_retries,
                   "source_commit": src["environment"]["git_commit"]})
        path = result.save()
        print(f"== {name}: { {k: (round(v, 3) if isinstance(v, float) else v) for k, v in overall.items()} }")
        print(f"   outcomes: {result.extra['outcomes']} | saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
