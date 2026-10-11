"""Compare the four model conditions of stage 4 and report training cost.

[EN]
- Conditions (same prompt cite_v1, same top-5 contexts, greedy decoding): base bf16 (stage 3 run),
  base 4-bit, QLoRA-tuned (4-bit base), LoRA-tuned (bf16 base).
- Sections: (1) automatic citation metrics, (2) paired bootstrap of the sentence-level citation
  rate: each tuned model against its matching untuned base (bf16 for LoRA, 4-bit for QLoRA), the
  quantisation effect, QLoRA against the bf16 base, and QLoRA against LoRA, (3) judged
  quality (faithfulness, answer relevance, correctness) so that a gain in format is not bought
  with worse answers, (4) training cost and loss.
- Paired bootstrap: resample the 45 questions 10000 times (seed 42) and report the 95% interval of
  the mean per-question difference.
- Usage: uv run python experiments/analyze_s4.py

[KO]
- 조건(같은 프롬프트 cite_v1, 같은 상위 5개 컨텍스트, greedy 디코딩): 기반 bf16(3단계 실행), 기반 4비트,
  QLoRA 학습(4비트 기반), LoRA 학습(bf16 기반).
- 구성: (1) 자동 인용 지표, (2) 문장 단위 인용률의 쌍체 부트스트랩(각 학습 모델을 짝이 되는 미학습 기반과 비교: LoRA는 bf16,
  QLoRA는 4비트. 그 외 양자화 효과, QLoRA 대 bf16 기반, QLoRA 대 LoRA), (3) 판정 품질(충실도, 답변 관련성, 정확성)로 형식 개선이 답 품질 악화로 얻어진 것이 아닌지 확인,
  (4) 학습 비용과 손실.
- 쌍체 부트스트랩: 질문 45개를 10000번 재표집(시드 42)해 질문별 차이 평균의 95% 구간을 보고한다.
- 사용: uv run python experiments/analyze_s4.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "experiments" / "results"
CONDITIONS = {"base bf16": "s3_gen_cite_v1", "base 4-bit": "s4_gen_base4bit", "QLoRA r16": "s4_gen_qlora_r16", "LoRA r16": "s4_gen_lora_r16"}
PAIRS = [("LoRA r16", "base bf16"), ("QLoRA r16", "base 4-bit"), ("base 4-bit", "base bf16"), ("QLoRA r16", "base bf16"), ("QLoRA r16", "LoRA r16")]


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def boot(diff: np.ndarray, n: int = 10000, seed: int = 42) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    means = diff[rng.integers(0, len(diff), size=(n, len(diff)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> None:
    R = {c: load(n) for c, n in CONDITIONS.items() if (RES / f"{n}.json").exists()}
    print("### 1. automatic metrics (n=45)\n")
    cols = ("has_citation", "citations_valid", "cites_gold", "sentence_coverage", "refused")
    print("| condition | " + " | ".join(cols) + " | answer tokens | generation s (p50) |\n|---|" + "---|" * (len(cols) + 2))
    for c, d in R.items():
        o = d["metrics"]["overall"]
        print(f"| {c} | " + " | ".join(f"{o[k]:.3f}" for k in cols) + f" | {d['timing']['tokens']['completion_mean']:.0f} | {d['timing']['generation_seconds']['p50']:.1f} |")

    print("\n### 2. sentence-level citation rate vs the matching untuned base (paired bootstrap)\n")
    print("| tuned/changed | vs | mean diff | 95% interval | better / worse questions |\n|---|---|---|---|---|")
    for a, b in PAIRS:
        if a not in R or b not in R:
            continue
        pa = {p["qid"]: p["metrics"]["sentence_coverage"] for p in R[a]["per_query"]}
        pb = {p["qid"]: p["metrics"]["sentence_coverage"] for p in R[b]["per_query"]}
        diff = np.array([pa[q] - pb[q] for q in pa])
        lo, hi = boot(diff)
        print(f"| {a} | {b} | {diff.mean():+.3f} | {lo:+.3f} .. {hi:+.3f} | {int((diff > 1e-9).sum())} / {int((diff < -1e-9).sum())} |")

    print("\n### 3. judged quality (Qwen3-8B judge; share of YES among applicable answers)\n")
    dims = ("faithfulness", "answer_relevance", "correctness")
    print("| condition | " + " | ".join(dims) + " | outcome classes |\n|---|" + "---|" * (len(dims) + 1))
    for c, n in CONDITIONS.items():
        jn = f"s3_judge_{n.removeprefix('s3_gen_')}"
        if not (RES / f"{jn}.json").exists():
            continue
        j = load(jn)
        o = j["metrics"]["overall"]
        print(f"| {c} | " + " | ".join(f"{o[d]:.3f} (n={o[d + '_n']})" for d in dims) + f" | {j['extra']['outcomes']} |")

    print("\n### 4. training\n")
    rows = []
    for name in ("s4_qlora_r16", "s4_lora_r16"):
        if (RES / f"{name}.json").exists():
            rows.append((name, load(name)))
    print("| run | trainable params | base weights GiB | peak GPU GiB | train time | tokens/s | train examples | val loss before -> final | adapter MB |\n|---|---|---|---|---|---|---|---|---|")
    for name, d in rows:
        e, o, t = d["extra"], d["metrics"]["overall"], d["timing"]
        print(f"| {name} | {e['trainable_params_m']:.1f}M | {e['base_gib']:.1f} | {e['peak_gpu_gib']:.1f} | {t['train_seconds'] / 60:.1f} min | {t['tokens_per_second']:.0f} | {o['n']} | "
              f"{o['val_loss_before']:.3f} -> {o['val_loss_final']:.3f} | {e['adapter_mb']:.0f} |")
    for name, d in rows:
        print(f"\n{name} validation loss by epoch: " + ", ".join(f"{k}={v:.3f}" for k, v in d["extra"]["val_loss_curve"].items()))


if __name__ == "__main__":
    main()
