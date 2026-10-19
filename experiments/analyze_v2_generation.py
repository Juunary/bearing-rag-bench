"""Analyse generation and judging of the improvement round (90 questions) -> experiments/results/v2_generation_analysis.md.

[EN]
- Conditions: base bf16, base 4-bit, QLoRA and LoRA (seeds 42, 43, 44) trained on the decontaminated
  general set, QLoRA and LoRA trained on the cross-language-only set, and the base model fed with the
  English-pivot retrieval result. Judge = Qwen3-8B (AI, 8 human-graded answers in stage 3 showed it is only
  an approximation).
- Metrics are split by independence from the training objective. The training answers were selected by
  `sentence_coverage == 1`, so sentence_coverage is the selection metric (its rise is expected); cites_gold,
  judged faithfulness / correctness / relevance and answer-language are independent of the selection.
- Sections: (1) every condition; (2) seed spread: mean and sd over the three seeds for QLoRA and LoRA;
  (3) paired comparisons per question with the interval by question and by primary-evidence document
  (the seed-averaged tuned model against its own untuned base, and QLoRA against LoRA); (4) the
  cross-language-only set against the general set on cross-language questions; (5) retrieval effect on
  the answers; (6) answer language.
- Usage: uv run python experiments/analyze_v2_generation.py

[KO]
- 조건: 기반 bf16, 기반 4비트, 오염 없는 일반 세트로 학습한 QLoRA·LoRA(시드 42·43·44), 교차 언어 전용 세트로
  학습한 QLoRA·LoRA, 영어 피벗 검색 결과를 받은 기반 모델. 판정 = Qwen3-8B(AI이며, 3단계의 사람 채점 8개로
  근사치임을 확인).
- 지표는 학습 목표와의 독립성으로 나눈다. 학습 답변은 `sentence_coverage == 1`로 골랐으므로
  sentence_coverage는 선택 기준 지표(상승이 당연)이고, cites_gold, 판정 충실도·정확성·관련성, 답변 언어는
  선택과 독립이다.
- 구성: (1) 모든 조건; (2) 시드 산포: QLoRA·LoRA의 세 시드 평균과 표준편차; (3) 질문별 쌍체 비교와 질문 단위·
  주 근거 문서 단위 구간(시드 평균한 학습 모델 대 자기 미학습 기반, QLoRA 대 LoRA); (4) 교차 언어 질문에서
  교차 언어 전용 세트 대 일반 세트; (5) 검색이 답에 미친 효과; (6) 답변 언어.
- 사용: uv run python experiments/analyze_v2_generation.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.stats import compare  # noqa: E402

RES = REPO / "experiments" / "results"
HANGUL = re.compile(r"[가-힣]")
AUTO = ("sentence_coverage", "cites_gold", "citations_valid", "refused")
JUDGE = ("faithfulness", "correctness", "answer_relevance")
QL = {"qlora": [f"qlora_s{s}" for s in (42, 43, 44)], "lora": [f"lora_s{s}" for s in (42, 43, 44)]}


def load(name: str) -> dict | None:
    p = RES / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def per_query_matrix(name: str) -> dict[str, np.ndarray] | None:
    """metric -> array over questions (NaN where the judge says 'not applicable')."""
    g, j = load(f"v2g_{name}"), load(f"s3_judge_v2g_{name}")
    if g is None:
        return None
    m = {k: np.array([q["metrics"][k] for q in g["per_query"]], dtype=float) for k in AUTO}
    m["gold_in_context"] = np.array([q["metrics"]["gold_in_context"] for q in g["per_query"]], dtype=float)
    for d in JUDGE:
        m[d] = np.array([np.nan if (j is None or q["labels"].get(d) is None) else float(q["labels"][d]) for q in j["per_query"]]) if j else np.full(len(g["per_query"]), np.nan)
    lang = []
    for q in g["per_query"]:
        a = q["answer"]
        lang.append(float(bool(HANGUL.search(a))) if q["q_lang"] == "ko" else float(not HANGUL.search(a)) if a.strip() else 0.0)
    m["answer_language_ok"] = np.array(lang)
    return m


def fmt(x: np.ndarray) -> str:
    return "-" if np.all(np.isnan(x)) else f"{np.nanmean(x):.3f} (n={int((~np.isnan(x)).sum())})"


def main() -> None:
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    names = ["base_bf16", "base_4bit", *QL["qlora"], *QL["lora"], "xqlora_s42", "xlora_s42", "ret_b_rrf_en_rerank"]
    M = {n: per_query_matrix(n) for n in names}
    M = {n: m for n, m in M.items() if m is not None}
    first = load(f"v2g_{next(iter(M))}")
    qids = [q["qid"] for q in first["per_query"]]
    clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
    cross = np.array([queries[i]["type"] == "cross" for i in qids])
    cols = (*AUTO, "gold_in_context", *JUDGE, "answer_language_ok")
    out = ["# v2 generation analysis (90 questions)", "",
           "Selection metric (training answers were chosen by it): sentence_coverage. Independent of the selection: cites_gold, judged metrics, answer language.", "",
           "## 1. Every condition", "", "| condition | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for n, m in M.items():
        out.append(f"| {n} | " + " | ".join(fmt(m[c]) for c in cols) + " |")

    out += ["", "## 2. Seed spread (mean ± sd over the seeds present)", "", "| method | seeds | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for meth, ns in QL.items():
        have = [n for n in ns if n in M]
        if not have:
            continue
        cells = []
        for c in cols:
            vals = [np.nanmean(M[n][c]) for n in have if not np.all(np.isnan(M[n][c]))]
            cells.append("-" if not vals else f"{np.mean(vals):.3f} ± {np.std(vals, ddof=1) if len(vals) > 1 else 0:.3f}")
        out.append(f"| {meth} | {len(have)} | " + " | ".join(cells) + " |")

    def seed_avg(meth: str, metric: str) -> np.ndarray | None:
        have = [M[n][metric] for n in QL[meth] if n in M]
        return None if not have else np.nanmean(np.stack(have), axis=0) if not np.all(np.isnan(np.stack(have))) else None

    out += ["", "## 3. Paired comparisons (A - B per question; seed-averaged where the condition has seeds)", "",
            "| A | B | metric | mean diff | 95% CI (question) | 95% CI (cluster) | better/worse/tie |", "|---|---|---|---|---|---|---|"]
    comps = [("qlora (seed avg)", "base_4bit", "qlora", "base_4bit"), ("lora (seed avg)", "base_bf16", "lora", "base_bf16"),
             ("qlora (seed avg)", "base_bf16", "qlora", "base_bf16"), ("qlora (seed avg)", "lora (seed avg)", "qlora", "lora")]
    for la, lb, a, b in comps:
        for metric in ("sentence_coverage", "cites_gold", "faithfulness", "correctness"):
            xa = seed_avg(a, metric) if a in QL else (M[a][metric] if a in M else None)
            xb = seed_avg(b, metric) if b in QL else (M[b][metric] if b in M else None)
            if xa is None or xb is None:
                continue
            ok = ~np.isnan(xa) & ~np.isnan(xb)
            if ok.sum() < 5:
                continue
            c = compare((xa - xb)[ok], [cl for cl, k in zip(clusters, ok) if k])
            out.append(f"| {la} | {lb} | {metric} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | {c['better']}/{c['worse']}/{c['tie']} |")

    out += ["", "## 4. Cross-language-only training set vs general set (cross-language questions only; one seed each)", "",
            "| method | training set | " + " | ".join(("sentence_coverage", "cites_gold", "faithfulness", "correctness", "answer_language_ok")) + " |", "|---|---|---|---|---|---|---|"]
    for meth, general, x in (("qlora", "qlora_s42", "xqlora_s42"), ("lora", "lora_s42", "xlora_s42")):
        for label, n in (("general", general), ("cross-only", x)):
            if n in M:
                out.append(f"| {meth} | {label} | " + " | ".join(fmt(M[n][c][cross]) for c in ("sentence_coverage", "cites_gold", "faithfulness", "correctness", "answer_language_ok")) + " |")

    out += ["", "## 5. Retrieval effect on the answers (base bf16 model)", "", "| contexts from | gold_in_context | cites_gold | faithfulness | correctness | answer_relevance |", "|---|---|---|---|---|---|"]
    for label, n in (("RRF + reranker (original)", "base_bf16"), ("English-pivot RRF + reranker", "ret_b_rrf_en_rerank")):
        if n in M:
            out.append(f"| {label} | " + " | ".join(fmt(M[n][c]) for c in ("gold_in_context", "cites_gold", "faithfulness", "correctness", "answer_relevance")) + " |")
    if "base_bf16" in M and "ret_b_rrf_en_rerank" in M:
        for metric in ("gold_in_context", "correctness"):
            xa, xb = M["ret_b_rrf_en_rerank"][metric], M["base_bf16"][metric]
            ok = ~np.isnan(xa) & ~np.isnan(xb)
            c = compare((xa - xb)[ok], [cl for cl, k in zip(clusters, ok) if k])
            out.append(f"\n- {metric}, English pivot minus original: {c['mean']:+.3f}, CI question {c['ci_iid'][0]:+.3f}..{c['ci_iid'][1]:+.3f}, CI cluster {c['ci_cluster'][0]:+.3f}..{c['ci_cluster'][1]:+.3f}, better/worse/tie {c['better']}/{c['worse']}/{c['tie']}")

    out += ["", "## 6. Answer language (ko: Hangul present; en/de: no Hangul; German vs English is not distinguished)", "",
            "| condition | ko questions | en questions | de questions |", "|---|---|---|---|"]
    ql = np.array([queries[i]["q_lang"] for i in qids])
    for n, m in M.items():
        out.append(f"| {n} | " + " | ".join(f"{m['answer_language_ok'][ql == l].mean():.2f}" for l in ("ko", "en", "de")) + " |")
    text = "\n".join(out) + "\n"
    (RES / "v2_generation_analysis.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
