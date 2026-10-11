"""Regression check: compare a fresh experiment result with a frozen baseline.

[EN]
- Role: after any change (code, model, prompt, chunking, a library upgrade) rerun an experiment on
  the fixed eval set and decide whether quality got worse.
- Baseline = the metrics plus the per-question output of an earlier accepted run (ranked chunk ids for
  retrieval results, answers for generation results), stored in eval/baselines/<exp_id>.json.
- Verdict rule (decided 2026-10-12, based on the finding that this repository's retrieval and
  greedy generation are deterministic, so an unchanged system must reproduce its numbers exactly):
  - PASS: output and metrics identical to the baseline.
  - WARN: some output differs but no quality metric fell by more than the tolerance (0.02). Review
    the changes; if intended, update the baseline.
  - FAIL: a quality metric fell by more than the tolerance, or the question set changed.
- Higher-is-better metrics: all retrieval metrics; for generation has_citation, citations_valid,
  cites_gold, sentence_coverage, gold_in_context. "refused" is reported but never judged.
- The tolerance is small on purpose: with 45 questions one question moves a mean by about 0.02, so a
  drop larger than that is at least one clearly worse question.

[KO]
- 역할: 코드, 모델, 프롬프트, 청킹, 라이브러리 업그레이드 같은 변경 후에 고정된 평가셋으로 실험을 다시
  돌려 품질이 나빠졌는지 판정한다.
- 기준선 = 이전에 승인된 실행의 지표와 질문별 출력(검색 결과는 순위 청크 ID, 생성 결과는 답변). 
  eval/baselines/<exp_id>.json에 저장한다.
- 판정 규칙(2026-10-12 결정. 이 저장소의 검색과 greedy 생성이 결정적이므로 바뀌지 않은 시스템은 같은
  숫자를 정확히 재현해야 한다는 확인에 근거):
  - PASS: 출력과 지표가 기준선과 같다.
  - WARN: 출력이 일부 다르지만 품질 지표가 허용오차(0.02)보다 더 떨어지지 않았다. 변경을 검토하고 의도한
    것이면 기준선을 갱신한다.
  - FAIL: 품질 지표가 허용오차보다 더 떨어졌거나 질문 집합이 바뀌었다.
- 높을수록 좋은 지표: 검색은 전부, 생성은 has_citation, citations_valid, cites_gold, sentence_coverage,
  gold_in_context. refused는 보고만 하고 판정하지 않는다.
- 허용오차를 작게 둔 이유: 질문 45개에서 질문 하나가 평균을 약 0.02 움직이므로, 그보다 큰 하락은 분명히
  나빠진 질문이 하나 이상이라는 뜻이다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOLERANCE = 0.02
GEN_HIGHER_BETTER = ("has_citation", "citations_valid", "cites_gold", "sentence_coverage", "gold_in_context")
RET_HIGHER_BETTER = ("recall@5", "mrr@10", "ndcg@10")


def kind_of(result: dict[str, Any]) -> str:
    return "generation" if result["per_query"] and "answer" in result["per_query"][0] else "retrieval"


def extract_baseline(result: dict[str, Any]) -> dict[str, Any]:
    kind = kind_of(result)
    key = "answer" if kind == "generation" else "ranked"
    return {
        "exp_id": result["config"]["exp_id"], "kind": kind, "n": len(result["per_query"]),
        "metrics": {"overall": result["metrics"]["overall"]},
        "items": {p["qid"]: p[key] for p in result["per_query"]},
    }


@dataclass
class Report:
    status: str                        # PASS | WARN | FAIL
    lines: list[str] = field(default_factory=list)


def compare(new_result: dict[str, Any], baseline: dict[str, Any], tolerance: float = TOLERANCE) -> Report:
    new = extract_baseline(new_result)
    lines: list[str] = []
    if new["kind"] != baseline["kind"] or set(new["items"]) != set(baseline["items"]):
        return Report("FAIL", [f"question set or result kind changed: {baseline['kind']}/{baseline['n']} -> {new['kind']}/{new['n']}"])

    changed = [q for q in baseline["items"] if new["items"][q] != baseline["items"][q]]
    higher = RET_HIGHER_BETTER if new["kind"] == "retrieval" else GEN_HIGHER_BETTER
    worse, drifted = [], []
    for m, old in baseline["metrics"]["overall"].items():
        cur = new["metrics"]["overall"].get(m)
        if m == "n" or cur is None:
            continue
        d = cur - old
        if abs(d) > 1e-9:
            drifted.append(f"{m}: {old:.4f} -> {cur:.4f} ({d:+.4f})")
        if m in higher and d < -tolerance - 1e-9:
            worse.append(f"{m} fell by {-d:.4f} (> {tolerance})")
    if worse:
        return Report("FAIL", worse + drifted + [f"{len(changed)} of {baseline['n']} outputs differ"])
    if changed or drifted:
        return Report("WARN", drifted + [f"{len(changed)} of {baseline['n']} outputs differ: {', '.join(changed[:8])}{' ...' if len(changed) > 8 else ''}"])
    return Report("PASS", [f"identical to baseline ({baseline['n']} questions)"])
