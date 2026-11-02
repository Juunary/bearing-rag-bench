"""Second judge of another model family (Granite 3.3 8B) against the Qwen3-8B judge -> experiments/results/judge_agreement.md.

[EN]
- Role: check how much the judged numbers depend on the judge. Both judges used the same prompts (judge_v1),
  greedy decoding, the same answers.
- Sections: (1) per result file and dimension, YES rate of each judge, raw agreement and Cohen's kappa on the
  answers both judges rated; (2) the 8 human-graded answers (stage 3, cite_refuse_v1), agreement counts per judge;
  (3) paired comparisons already reported with the Qwen judge, recomputed with Granite (A - B, document-cluster
  95% interval) so a conclusion that depends on the judge shows up.
- Usage: uv run python experiments/analyze_judge_agreement.py

[KO]
- 역할: 판정 수치가 판정 모델에 얼마나 좌우되는지 본다. 두 판정 모델은 같은 프롬프트(judge_v1), greedy,
  같은 답변을 썼다.
- 구성: (1) 결과 파일·항목별 각 판정 모델의 YES 비율, 단순 일치율, 두 모델이 모두 판정한 답변의 Cohen's kappa;
  (2) 사람이 채점한 답변 8개(3단계, cite_refuse_v1)에서 판정 모델별 일치 개수; (3) Qwen 판정으로 보고한 쌍체
  비교를 Granite 판정으로 다시 계산(A - B, 문서 군집 95% 구간). 판정 모델에 따라 바뀌는 결론이 드러난다.
- 사용: uv run python experiments/analyze_judge_agreement.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.stats import compare  # noqa: E402

RES = REPO / "experiments" / "results"
DIMS = ("faithfulness", "correctness", "answer_relevance")
JUDGES = {"qwen": "s3_judge", "granite": "s3_judge_granite"}
FILES = ["s3_gen_cite_refuse_v1", "v2g_base_bf16", "v2g_base_4bit", "v2g_qlora_s42", "v2g_lora_s42", "v2g_ret_b_rrf_en_rerank",
         "v2g_ret_x2_rerank_en_text", "v2g_cmp_li", "v2g_cmp_hs", "v2g_cmp_ar"]
# Qwen 판정으로 README에 보고한 비교들
PAIRS = [("v2g_ret_x2_rerank_en_text", "v2g_base_bf16"), ("v2g_ret_b_rrf_en_rerank", "v2g_base_bf16"),
         ("v2g_lora_s42", "v2g_base_bf16"), ("v2g_qlora_s42", "v2g_base_4bit"),
         ("v2g_ret_x2_rerank_en_text", "v2g_cmp_ar"), ("v2g_cmp_ar", "v2g_cmp_li"), ("v2g_cmp_ar", "v2g_cmp_hs")]


def judged(judge: str, name: str) -> dict | None:
    p = RES / f"{JUDGES[judge]}_{name.removeprefix('s3_gen_')}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def labels(d: dict, dim: str) -> np.ndarray:
    return np.array([np.nan if q["labels"].get(dim) is None else float(q["labels"][dim]) for q in d["per_query"]])


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    po = float((a == b).mean())
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def main() -> None:
    out = ["# Judge agreement: Qwen3-8B vs Granite 3.3 8B (same prompts, greedy)", "",
           "## 1. Per result file and dimension (answers both judges rated)", "",
           "| result | dimension | n | YES Qwen | YES Granite | agreement | Cohen's kappa |", "|---|---|---|---|---|---|---|"]
    for name in FILES:
        q, g = judged("qwen", name), judged("granite", name)
        if q is None or g is None:
            continue
        for dim in DIMS:
            a, b = labels(q, dim), labels(g, dim)
            keep = ~np.isnan(a) & ~np.isnan(b)
            a, b = a[keep], b[keep]
            out.append(f"| {name} | {dim} | {int(keep.sum())} | {a.mean():.3f} | {b.mean():.3f} | {(a == b).mean():.3f} | {kappa(a, b):.3f} |")

    human = json.loads((REPO / "eval" / "human_labels.json").read_text(encoding="utf-8"))
    out += ["", f"## 2. Human-graded answers ({len(human['labels'])}, {human['source']}; counts, no rate claimed)", "",
            "| judge | correctness | faithfulness | answer relevance |", "|---|---|---|---|"]
    to_bool = {"correctness": lambda s: None if s == "거절" else s == "맞음", "faithfulness": lambda s: s == "예", "answer_relevance": lambda s: s == "예"}
    for judge in JUDGES:
        d = judged(judge, human["source"])
        if d is None:
            continue
        by = {p["qid"]: p for p in d["per_query"]}
        cells = []
        for dim in ("correctness", "faithfulness", "answer_relevance"):
            agree = comp = 0
            for qid, lab in human["labels"].items():
                h, j = to_bool[dim](lab[dim]), by[qid]["labels"][dim]
                if h is not None and j is not None:
                    comp += 1
                    agree += h == j
            cells.append(f"{agree}/{comp}")
        out.append(f"| {judge} | " + " | ".join(cells) + " |")

    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    out += ["", "## 3. Paired comparisons under each judge (A - B, document-cluster 95% interval; questions both answers were judged on)", "",
            "| A | B | dimension | Qwen: mean diff (CI) | Granite: mean diff (CI) |", "|---|---|---|---|---|"]
    for a_name, b_name in PAIRS:
        cells = {}
        for judge in JUDGES:
            ja, jb = judged(judge, a_name), judged(judge, b_name)
            if ja is None or jb is None:
                break
            clusters = [queries[p["qid"]]["gold"][0]["doc_id"] for p in ja["per_query"]]
            for dim in ("faithfulness", "correctness"):
                d = labels(ja, dim) - labels(jb, dim)
                keep = ~np.isnan(d)
                c = compare(d[keep], [cl for cl, k in zip(clusters, keep) if k])
                cells[(judge, dim)] = f"{c['mean']:+.3f} ({c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f})"
        for dim in ("faithfulness", "correctness"):
            if ("granite", dim) in cells:
                out.append(f"| {a_name} | {b_name} | {dim} | {cells[('qwen', dim)]} | {cells[('granite', dim)]} |")
    text = "\n".join(out) + "\n"
    (RES / "judge_agreement.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
