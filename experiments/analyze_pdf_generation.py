"""Analyse answers to the 48 PDF questions under two judges -> experiments/results/pdf_generation_analysis.md.

[EN]
- Conditions: the base bf16 Qwen3-4B (prompt cite_v1, top 5) fed with (a) RRF + reranker, (b) the best PDF retrieval
  (RRF over English BM25 + English dense, reranker on English text), (c) the same with table caption and header rows
  repeated in chunks (chunking.table_header), (d) the same as (c) with the top 10 chunks in the prompt. Judges: Qwen3-8B and Granite 3.3 8B, same prompts.
- Sections: (1) per condition, automatic metrics (gold chunk in context, cites a gold chunk) and the judged rates of each
  judge; (2) correctness by evidence kind (text, table, caption) per judge; (3) paired comparisons per question
  (interval by question; only 6 primary documents, so no cluster interval).
- (4) the serving prompt cite_refuse_v1 (may refuse) with the top 5 and the top 10 of (c): automatic metrics only (refused,
  refused although a gold chunk was in the prompt, sentence coverage), not judged.
- Usage: uv run python experiments/analyze_pdf_generation.py

[KO]
- 조건: 기반 bf16 Qwen3-4B(cite_v1, 상위 5)에 (a) RRF + 리랭커, (b) PDF 최고 검색(영어 BM25 + 영어 dense RRF, 리랭커 영어
  입력), (c) 같은 검색에 표 캡션·머리글 반복 청크(chunking.table_header)를 준 답변, (d) (c)에서 프롬프트에 상위 10개를 넣은 답변. 판정은 Qwen3-8B와 Granite 3.3 8B(같은 프롬프트).
- 구성: (1) 조건별 자동 지표(정답 청크가 컨텍스트에 있음, 정답 청크 인용)와 판정 모델별 비율; (2) 근거 종류별(본문, 표, 캡션)
  판정 모델별 정확성; (3) 질문별 쌍체 비교(질문 단위 구간. 주 근거 문서가 6개뿐이라 군집 구간은 쓰지 않음).
- (4) 서비스 프롬프트 cite_refuse_v1(거절 가능)에 (c)의 상위 5와 상위 10을 준 답변: 자동 지표만(거절, 정답 청크가 프롬프트에
  있는데 거절, 문장 인용률), 판정하지 않음.
- 사용: uv run python experiments/analyze_pdf_generation.py
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
CONDS = [("RRF + reranker", "pdfg_b_rrf_rerank"), ("best PDF retrieval", "pdfg_x13_rrf_en_dense_en_rerank_en_text"),
         ("best PDF retrieval + table headers", "pdfg_th_x13_rrf_en_dense_en_rerank_en_text"),
         ("best PDF retrieval + table headers, top 10", "pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10")]
JUDGES = {"Qwen3-8B": "s3_judge", "Granite": "s3_judge_granite"}
DIMS = ("faithfulness", "correctness", "answer_relevance")
PAIRS = [("pdfg_x13_rrf_en_dense_en_rerank_en_text", "pdfg_b_rrf_rerank"),
         ("pdfg_th_x13_rrf_en_dense_en_rerank_en_text", "pdfg_x13_rrf_en_dense_en_rerank_en_text"),
         ("pdfg_th_x13_rrf_en_dense_en_rerank_en_text_k10", "pdfg_th_x13_rrf_en_dense_en_rerank_en_text")]
REFUSE = [("top 5", "pdfg_th_x13_rrf_en_dense_en_rerank_en_text_refuse"), ("top 10", "pdfg_th_x13_rrf_en_dense_en_rerank_en_text_refuse_k10")]
AUTO = ("refused", "over_refusal", "gold_in_context", "cites_gold", "sentence_coverage")


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def auto(g: dict, key: str) -> np.ndarray:
    if key == "over_refusal":                                   # 정답 청크가 프롬프트에 있는데 거절
        return auto(g, "refused") * auto(g, "gold_in_context")
    return np.array([float(q["metrics"][key]) for q in g["per_query"]])


def judged(j: dict, dim: str) -> np.ndarray:
    return np.array([np.nan if q["labels"].get(dim) is None else float(q["labels"][dim]) for q in j["per_query"]])


def main() -> None:
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_pdf.jsonl")}
    G = {n: load(n) for _, n in CONDS}
    J = {(jn, n): load(f"{prefix}_{n}") for jn, prefix in JUDGES.items() for _, n in CONDS}
    qids = [q["qid"] for q in G[CONDS[0][1]]["per_query"]]
    kind = np.array([queries[i]["evidence_kind"] for i in qids])
    out = ["# PDF questions: generation and judging (48 questions)", "",
           "## 1. Per condition", "",
           "| condition | gold in context | cites gold | " + " | ".join(f"{d} ({jn})" for d in DIMS for jn in JUDGES) + " |",
           "|---|---|---|" + "---|" * (len(DIMS) * len(JUDGES))]
    for label, n in CONDS:
        cells = [f"{auto(G[n], 'gold_in_context').mean():.3f}", f"{auto(G[n], 'cites_gold').mean():.3f}"]
        cells += [f"{np.nanmean(judged(J[(jn, n)], d)):.3f}" for d in DIMS for jn in JUDGES]
        out.append(f"| {label} | " + " | ".join(cells) + " |")

    # 프롬프트 길이·생성 시간: 컨텍스트 개수를 바꾸면 비용이 얼마나 느는지 (생성 시간은 캐시가 아닌 실제 생성값)
    out += ["", "Prompt tokens and generation seconds per answer (median):", "", "| condition | prompt tokens | seconds |", "|---|---|---|"]
    for label, n in CONDS:
        pq = G[n]["per_query"]
        out.append(f"| {label} | {np.median([q['prompt_tokens'] for q in pq]):.0f} | {np.median([q['seconds'] for q in pq]):.2f} |")

    out += ["", "## 2. Correctness by evidence kind", "", "| condition | judge | text | table | caption |", "|---|---|---|---|---|"]
    for label, n in CONDS:
        for jn in JUDGES:
            x = judged(J[(jn, n)], "correctness")
            out.append(f"| {label} | {jn} | " + " | ".join(f"{np.nanmean(x[kind == k]):.3f} (n={int((~np.isnan(x[kind == k])).sum())})"
                                                         for k in ("text", "table", "caption")) + " |")

    out += ["", "## 3. Paired comparisons (A - B, 95% interval by question; no multiplicity correction)", "",
            "| A | B | metric | mean diff | 95% CI | better/worse/tie | n |", "|---|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        rows = [(m, auto(G[a], m) - auto(G[b], m)) for m in ("gold_in_context", "cites_gold", "sentence_coverage")]
        rows += [(f"{d} ({jn})", judged(J[(jn, a)], d) - judged(J[(jn, b)], d)) for d in ("faithfulness", "correctness") for jn in JUDGES]
        for metric, d in rows:
            keep = ~np.isnan(d)
            c = compare(d[keep])
            out.append(f"| {a} | {b} | {metric} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | "
                       f"{c['better']}/{c['worse']}/{c['tie']} | {int(keep.sum())} |")
    R = {n: load(n) for _, n in REFUSE}
    out += ["", "## 4. Serving prompt cite_refuse_v1, top 5 vs top 10 (automatic metrics, not judged)", "",
            "| context | " + " | ".join(AUTO) + " |", "|---|" + "---|" * len(AUTO)]
    for label, n in REFUSE:
        out.append(f"| {label} | " + " | ".join(f"{auto(R[n], m).mean():.3f}" for m in AUTO) + " |")
    (_, a), (_, b) = REFUSE[1], REFUSE[0]
    out += ["", "| metric | top 10 - top 5 | 95% CI | top 10 higher/lower/tie |", "|---|---|---|---|"]
    for m in AUTO:
        c = compare(auto(R[a], m) - auto(R[b], m))
        out.append(f"| {m} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['better']}/{c['worse']}/{c['tie']} |")
    text = "\n".join(out) + "\n"
    (RES / "pdf_generation_analysis.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
