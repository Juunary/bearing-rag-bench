"""Judge calibration against people: which judge model and prompt agree best with the human gold set.

[EN]
- Input: answered items of eval/human_gold/items.jsonl (correctness grades; adjudicated values applied), dev split by
  default. Test is used once, after the judge is chosen.
- Judges: one model at a time (Qwen3-8B, then Granite 3.3 8B; both do not fit together), prompts judge_v1 (YES/NO)
  and judge_v2 (CORRECT/PARTIAL/INCORRECT), the Reference being ragbench.humangold.reference_texts (gold sentences, or
  the guide page for practical questions).
- Reported per (model, prompt): kappa and agreement with people on two classes (부분 = 틀림), for judge_v2 also on three
  classes, the 2x2 confusion, sensitivity (human 맞음 judged YES) and specificity (human 부분/틀림 judged NO). These two
  are what ragbench.stats.corrected_rate needs to correct a judge's YES rate on other answers.
- The human-human kappa of experiments/results/human_agreement.md is the ceiling to compare with.
- Outputs: experiments/results/judge_calibration_<split>.json and .md.
- Usage: uv run python experiments/calibrate_judge.py [--split dev] [--models Qwen/Qwen3-8B,ibm-granite/granite-3.3-8b-instruct]

[KO]
- 입력: 사람 정답 세트의 답변 항목(정확성 채점, 합의 값 반영), 기본 dev. test는 판정 모델을 고른 뒤 한 번만.
- 판정 모델은 하나씩 올린다(Qwen3-8B 다음 Granite, 둘은 같이 안 들어감). 프롬프트는 judge_v1(YES/NO)과 judge_v2(3등급), 기준 근거는
  humangold.reference_texts(정답 문장, 실무 질문은 안내 페이지).
- (모델, 프롬프트)마다: 사람과의 2분류(부분 = 틀림) kappa·일치율, judge_v2는 3분류도, 2x2 혼동행렬, 민감도(사람 맞음을 YES)와
  특이도(사람 부분·틀림을 NO). 이 둘이 stats.corrected_rate로 다른 답변의 판정 YES 비율을 보정하는 데 쓰인다.
- 비교 상한은 experiments/results/human_agreement.md의 사람끼리 kappa.
- 출력: experiments/results/judge_calibration_<split>.json, .md
- 사용: uv run python experiments/calibrate_judge.py [--split dev] [--models Qwen/Qwen3-8B,ibm-granite/granite-3.3-8b-instruct]
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.humangold import binary, load_items, reference_texts  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.judge import GRADE_TO_HUMAN, V2_MAX_NEW_TOKENS, Judge, build_judge_messages, parse_grade, parse_verdict  # noqa: E402
from ragbench.stats import cohen_kappa  # noqa: E402

RES = REPO / "experiments" / "results"
V1_MAX_NEW = 80


def judge_items(judge: Judge, items: list[dict], version: str) -> list[dict]:
    out = []
    for it in items:
        msgs = build_judge_messages("correctness", it["question"], answer=it["answer"], references=reference_texts(it), version=version)
        if version == "judge_v2":
            r = judge.ask(msgs, max_new_tokens=V2_MAX_NEW_TOKENS)
            g = parse_grade(r["text"])
            grade, yes = (GRADE_TO_HUMAN[g] if g else None), (None if g is None else g == "CORRECT")
        else:
            r = judge.ask(msgs, max_new_tokens=V1_MAX_NEW)
            yes = parse_verdict(r["text"])
            if yes is None:                      # 판정 줄이 잘리면 run_judge.py와 같이 3배 한도로 한 번 더
                r = judge.ask(msgs, max_new_tokens=V1_MAX_NEW * 3)
                yes = parse_verdict(r["text"])
            grade = None
        out.append({"id": it["id"], "human": it["label"]["value"], "yes": yes, "grade": grade, "reply": r["text"]})
    return out


def scores(rows: list[dict]) -> dict:
    ok = [r for r in rows if r["yes"] is not None]
    h = [binary(r["human"]) for r in ok]
    j = [r["yes"] for r in ok]
    tp = sum(a and b for a, b in zip(h, j))
    tn = sum((not a) and (not b) for a, b in zip(h, j))
    fp = sum((not a) and b for a, b in zip(h, j))
    fn = sum(a and (not b) for a, b in zip(h, j))
    out = {"n": len(rows), "unparsable": len(rows) - len(ok), "kappa2": cohen_kappa(h, j) if ok else float("nan"),
           "agree2": (tp + tn) / len(ok) if ok else float("nan"), "tp": tp, "tn": tn, "fp": fp, "fn": fn,
           "sensitivity": tp / (tp + fn) if tp + fn else float("nan"), "specificity": tn / (tn + fp) if tn + fp else float("nan"),
           "judge_yes_rate": sum(j) / len(j) if j else float("nan"), "human_yes_rate": sum(h) / len(h) if h else float("nan")}
    g3 = [r for r in rows if r["grade"] is not None]
    if g3:
        out["kappa3"] = cohen_kappa([r["human"] for r in g3], [r["grade"] for r in g3])
        out["agree3"] = sum(r["human"] == r["grade"] for r in g3) / len(g3)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--models", default="Qwen/Qwen3-8B,ibm-granite/granite-3.3-8b-instruct")
    ap.add_argument("--versions", default="judge_v1,judge_v2")
    args = ap.parse_args()
    items = [it for it in load_items(split=None if args.split == "all" else args.split) if it["label"]["kind"] == "correctness"]
    cache = LLMCache(REPO / "logs" / "judge_cache.sqlite")
    result = {"split": args.split, "n_items": len(items), "runs": {}}
    for model in args.models.split(","):
        judge = Judge(model, cache=cache)
        for version in args.versions.split(","):
            rows = judge_items(judge, items, version)
            result["runs"][f"{model}|{version}"] = {"model": model, "version": version, "revision": judge.revision,
                                                    "scores": scores(rows), "rows": rows}
            print(model, version, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in scores(rows).items()})
        del judge
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass
    (RES / f"judge_calibration_{args.split}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# 판정 모델 보정 ({args.split}, 답변 {len(items)}개)", "",
             "| 모델 | 프롬프트 | kappa (부분 = 틀림) | 일치율 | kappa (3분류) | 민감도 | 특이도 | 판정 YES 비율 | 사람 맞음 비율 | 파싱 불가 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for run in result["runs"].values():
        s = run["scores"]
        lines.append(f"| {run['model'].split('/')[-1]} | {run['version']} | {s['kappa2']:.3f} | {s['agree2']:.3f} | "
                     f"{s.get('kappa3', float('nan')):.3f} | {s['sensitivity']:.3f} | {s['specificity']:.3f} | "
                     f"{s['judge_yes_rate']:.3f} | {s['human_yes_rate']:.3f} | {s['unparsable']} |")
    lines += ["", "비교 상한: `experiments/results/human_agreement.md`의 사람끼리 kappa."]
    (RES / f"judge_calibration_{args.split}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
