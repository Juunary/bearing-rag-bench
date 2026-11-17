"""Claim check against human grades: how many wrong answers it catches, how many correct ones it blocks.

[EN]
- Input: the human gold set (eval/human_gold/items.jsonl, dev split by default; test only once the policy is fixed).
  Answered items only (correctness grades); refusals are not checked.
- For every answer: ragbench.claimcheck with the serving generator (Qwen3-4B-Instruct-2507, greedy) over the passages
  the answer was generated from (ragbench.humangold.context_passages).
- Reported per policy (strip, and block at several min_support values):
  - catch rate: share of answers graded 틀림 or 부분 that the policy blocks or changes;
  - false block rate: share of answers graded 맞음 that it blocks (strip that only removes sentences is counted separately);
  - median added seconds and model calls per answer.
- The two graded failure cases named in the README (torsional vibration -> needle roller bearing, electrical fluting ->
  fretting) are listed with their per-sentence verdicts.
- Outputs: experiments/results/claimcheck_<split>.json (per item reports) and claimcheck_<split>.md (tables).
- Usage: uv run python experiments/eval_claimcheck.py [--split dev] [--device cuda:1]

[KO]
- 입력: 사람 채점 정답 세트(기본 dev; test는 정책을 고정한 뒤 한 번만). 정확성 채점이 있는 답변만(거절은 검사 대상 아님).
- 답변마다 서비스 생성 모델(Qwen3-4B, greedy)로 claim check를 돌린다. 근거는 그 답을 만든 컨텍스트(humangold.context_passages).
- 정책별 보고(strip, 여러 min_support의 block): 오답 탐지율(틀림·부분 중 차단되거나 바뀐 비율), 오차단율(맞음 중 차단된 비율, strip이
  문장만 지운 경우는 따로 셈), 답변당 추가 시간 중앙값과 모델 호출 수.
- README에 적힌 채점된 실패 사례 두 개(비틀림 진동 -> 니들 롤러, 전식 플루팅 -> 프레팅)는 문장별 판정을 따로 적는다.
- 출력: experiments/results/claimcheck_<split>.json(항목별), claimcheck_<split>.md(표).
- 사용: uv run python experiments/eval_claimcheck.py [--split dev] [--device cuda:1]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.claimcheck import ClaimChecker, ClaimReport, Claim, apply_policy  # noqa: E402
from ragbench.humangold import context_passages, load_items  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

MODEL = "Qwen/Qwen3-4B-Instruct-2507"
RES = REPO / "experiments" / "results"
CASES = {"needle roller": ("니들", "needle"), "fluting": ("플루팅", "fluting")}
POLICIES = [("strip", 1.0), ("block", 1.0), ("block", 0.75), ("block", 0.5)]


def report_from_dict(d: dict) -> ClaimReport:
    return ClaimReport([Claim(**c) for c in d["claims"]], d["seconds"], d["model_calls"])


def summarize(rows: list[dict]) -> list[str]:
    wrong = [r for r in rows if r["label"] in ("틀림", "부분")]
    right = [r for r in rows if r["label"] == "맞음"]
    lines = [f"답변 {len(rows)}개 (맞음 {len(right)}, 부분·틀림 {len(wrong)}).", "",
             "| 정책 | 오답 탐지율 (부분·틀림 중 차단 또는 수정) | 그중 차단 | 오차단율 (맞음 중 차단) | 맞음 중 문장만 삭제 |", "|---|---|---|---|---|"]
    for policy, ms in POLICIES:
        res = {r["id"]: apply_policy(r["answer"], report_from_dict(r["report"]), policy, ms) for r in rows}
        changed = lambda r: res[r["id"]].blocked or res[r["id"]].text != r["answer"]  # noqa: E731
        name = policy if policy == "strip" else f"block (min_support {ms})"
        lines.append(f"| {name} | {sum(map(changed, wrong))}/{len(wrong)} | {sum(res[r['id']].blocked for r in wrong)}/{len(wrong)} | "
                     f"{sum(res[r['id']].blocked for r in right)}/{len(right)} | "
                     f"{sum(changed(r) and not res[r['id']].blocked for r in right)}/{len(right)} |")
    secs = [r["report"]["seconds"] for r in rows]
    calls = [r["report"]["model_calls"] for r in rows]
    lines += ["", f"답변당 검사 시간 중앙값 {statistics.median(secs):.2f} s, 모델 호출 중앙값 {statistics.median(calls)}회.", ""]
    lines += ["## 채점된 실패 사례", ""]
    for name, keys in CASES.items():
        for r in rows:
            if any(k in r["answer"] for k in keys):
                lines.append(f"- {r['id']} ({name}, 사람 {r['label']}): " + "; ".join(
                    f"{'O' if c['supported'] else ('X' if c['supported'] is False else '?')} {c['text'][:60]}" for c in r["report"]["claims"]))
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--device", default="cuda:1")
    args = ap.parse_args()
    from ragbench.generation import Generator
    items = [it for it in load_items(split=None if args.split == "all" else args.split) if it["label"]["kind"] == "correctness"]
    checker = ClaimChecker(Generator(MODEL, device=args.device), LLMCache(REPO / "logs" / "claimcheck_cache.sqlite"))
    chunk_sets: dict = {}
    rows = []
    for it in items:
        rep = checker.check(it["answer"], context_passages(it, chunk_sets))
        rows.append({"id": it["id"], "source": it["source"], "label": it["label"]["value"], "answer": it["answer"], "report": rep.to_dict()})
        print(it["id"], it["label"]["value"], f"support {rep.support_ratio:.2f}", rep.unsupported)
    (RES / f"claimcheck_{args.split}.json").write_text(json.dumps({"split": args.split, "model": MODEL, "rows": rows},
                                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# Claim check ({args.split})", "", *summarize(rows)]
    (RES / f"claimcheck_{args.split}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
