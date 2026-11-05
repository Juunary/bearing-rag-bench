"""Model swap (2026 embedding / reranker models) against the best pipelines -> experiments/results/model_swap.md.

[EN]
- Sets: v2 (90 questions, baseline v2_x2_rerank_en_text) and PDF (48 questions, table-header chunks, baseline
  pdfth_x13_rrf_en_dense_en_rerank_en_text). Variants from scripts/make_model_configs.py: emb_qwen3_0.6b, emb_gemma2,
  rr_qwen3_0.6b, rr_qwen3_4b (one model replaced at a time).
- Per set: R@5, MRR@10, nDCG@10, mono / cross nDCG, paired nDCG difference vs the baseline with question-level and
  document-cluster 95% intervals, better/worse/tie, index build seconds, query p50 ms, embedding dimension / model revision.
- Usage: uv run python experiments/analyze_models.py

[KO]
- 세트: v2(90문항, 기준선 v2_x2_rerank_en_text), PDF(48문항, 표 머리글 청크, 기준선 pdfth_x13_rrf_en_dense_en_rerank_en_text).
  변형은 scripts/make_model_configs.py의 emb_qwen3_0.6b, emb_gemma2, rr_qwen3_0.6b, rr_qwen3_4b(한 번에 모델 하나만 교체).
- 세트별: R@5·MRR@10·nDCG@10, 단일/교차 언어 nDCG, 기준선 대비 nDCG 쌍체 차이(질문 단위·문서 군집 95% 구간), 나아짐/나빠짐/동일,
  색인 시간, 질의 p50, 임베딩 차원·모델 리비전.
- 사용: uv run python experiments/analyze_models.py
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
VARIANTS = ["emb_qwen3_0.6b", "emb_gemma2", "rr_qwen3_0.6b", "rr_qwen3_4b"]
SETS = {"v2m": ("v2_x2_rerank_en_text", "eval/queries_v2.jsonl", "v2 questions (90, Wikipedia corpus)"),
        "pdfm": ("pdfth_x13_rrf_en_dense_en_rerank_en_text", "eval/queries_pdf.jsonl", "PDF questions (48, Wikipedia + PDF, table headers)")}


def load(name: str) -> dict | None:
    p = RES / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def metric(d: dict, key: str) -> np.ndarray:
    return np.array([q["metrics"][key] for q in d["per_query"]])


def models(d: dict) -> str:
    r = d["config"]["retrieval"]
    return f"{r['embedding_model'].split('/')[-1]} / {(r.get('rerank_model') or '-').split('/')[-1]}"


def main() -> None:
    out = ["# Model swap: 2026 embedding and reranker models in the best pipelines", "",
           "One model replaced at a time; prompts, pooling and dtype follow the model cards (scripts/make_model_configs.py).", ""]
    for prefix, (base_name, eval_path, label) in SETS.items():
        base = load(base_name)
        if base is None:
            continue
        queries = {q["qid"]: q for q in load_queries(REPO / eval_path)}
        qids = [q["qid"] for q in base["per_query"]]
        typ = np.array([queries[i]["type"] for i in qids])
        clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
        b = metric(base, "ndcg@10")
        out += [f"## {label}", "", "| setting | embedding / reranker | R@5 | MRR@10 | nDCG@10 | mono | cross | nDCG diff vs baseline | question CI | cluster CI | better/worse/tie | index s | query p50 ms |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        rows = [("baseline", base)] + [(v, load(f"{prefix}_{v}")) for v in VARIANTS]
        for name, d in rows:
            if d is None:
                out.append(f"| {name} | (missing) | | | | | | | | | | | |")
                continue
            n = metric(d, "ndcg@10")
            diff = "" if name == "baseline" else ""
            if name != "baseline":
                c = compare(n - b, clusters)
                diff = f"{c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | {c['better']}/{c['worse']}/{c['tie']}"
            else:
                diff = "- | - | - | -"
            idx = d["timing"]["index"]
            build = sum(v.get("build_seconds", 0) + v.get("encode_seconds", 0) for v in idx.values() if isinstance(v, dict)) if isinstance(idx, dict) else 0
            out.append(f"| {name} | {models(d)} | {metric(d, 'recall@5').mean():.3f} | {metric(d, 'mrr@10').mean():.3f} | {n.mean():.3f} | "
                       f"{n[typ == 'mono'].mean():.3f} | {n[typ == 'cross'].mean():.3f} | {diff} | {build:.0f} | {d['timing']['query_latency_ms']['p50']:.0f} |")
        out.append("")
    text = "\n".join(out) + "\n"
    (RES / "model_swap.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
