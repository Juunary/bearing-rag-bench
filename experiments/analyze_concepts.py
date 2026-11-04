"""Concept-mediated retrieval against the best setting -> experiments/results/concept_analysis.md.

[EN]
- Sets: PDF questions (pdfth_*, 48, table-header chunks) and v2 questions (v2pdf_*, 90, wiki + pdf chunks). Baseline
  x13_rrf_en_dense_en_rerank_en_text; variants c_pool, c_pool_query, c_rrf_query (concept_mode) with data/concepts.
- Sections: (1) per set and setting: R@5, MRR@10, nDCG@10, queries with a matched concept (alias / dense), mean chunks
  added to the reranker pool, p50 latency; (2) paired nDCG difference vs the baseline on all queries, on matched queries
  and on unmatched queries (the last must be exactly zero: unmatched queries keep the baseline retrieval), question-level
  and document-cluster 95% intervals; (3) every matched query with its concepts and both nDCG values; (4) concept
  statistics: chunks per concept, queries matched per concept; (5) the 10 human-written questions: refusals, changed
  top 5, and the ranks of the D05 target chunks, read from eval/human_round2/user_questions_answers*.json.
- Usage: uv run python experiments/analyze_concepts.py

[KO]
- 세트: PDF 질문(pdfth_*, 48, 표 머리글 청크)과 v2 질문(v2pdf_*, 90, 위키 + PDF 청크). 기준선 x13_rrf_en_dense_en_rerank_en_text,
  변형 c_pool·c_pool_query·c_rrf_query(concept_mode, data/concepts).
- 구성: (1) 세트·설정별 R@5·MRR@10·nDCG@10, 개념이 매칭된 질문 수(별칭/dense), 리랭커 후보에 더한 청크 수 평균, p50 지연;
  (2) 기준선 대비 nDCG 쌍체 차이를 전체·매칭 질문·비매칭 질문(정확히 0이어야 함)으로 나눠 질문 단위·문서 군집 95% 구간과 함께;
  (3) 매칭 질문 목록(개념, 두 nDCG); (4) 개념별 청크 수·매칭 질문 수; (5) 사람이 쓴 질문 10개: 거절, 상위 5 변화, D05 대상 청크 순위
  (eval/human_round2/user_questions_answers*.json).
- 사용: uv run python experiments/analyze_concepts.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.stats import compare  # noqa: E402

RES = REPO / "experiments" / "results"
HR = REPO / "eval" / "human_round2"
BEST = "x13_rrf_en_dense_en_rerank_en_text"
MODES = ["pool", "pool30", "pool_query", "rrf_query"]     # pool30 = pool with concept_pool_n 30
SETS = {"pdfth": ("eval/queries_pdf.jsonl", "PDF questions (48, table-header chunks)"),
        "v2pdf": ("eval/queries_v2.jsonl", "v2 questions (90, wiki + pdf chunks)")}
D05_TARGETS = ["luh-diss-pelzer-2022#19", "de_wellendichtring#0", "luh-diss-pelzer-2022#28", "luh-diss-pelzer-2022#40", "luh-diss-pelzer-2022#43"]


def load(name: str) -> dict | None:
    p = RES / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def metric(d: dict, key: str) -> np.ndarray:
    return np.array([q["metrics"][key] for q in d["per_query"]])


def matched(d: dict) -> np.ndarray:
    return np.array([bool(q.get("concept", {}).get("ids")) for q in d["per_query"]])


def ci(c: dict, key: str) -> str:
    return f"{c[key][0]:+.3f} .. {c[key][1]:+.3f}"


def main() -> None:
    out = ["# Concept-mediated retrieval (data/concepts, 26 pages) against the best setting", ""]
    for prefix, (eval_path, label) in SETS.items():
        base = load(f"{prefix}_{BEST}")
        V = {m: load(f"{prefix}_c_{m}_{BEST}") for m in MODES}
        V = {m: d for m, d in V.items() if d is not None}
        if base is None or not V:
            out += [f"## {label}", "", "(results missing)", ""]
            continue
        queries = {q["qid"]: q for q in load_queries(REPO / eval_path)}
        qids = [q["qid"] for q in base["per_query"]]
        clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
        b_ndcg = metric(base, "ndcg@10")
        out += [f"## {label}", "", "### 1. Per setting", "",
                "| setting | R@5 | MRR@10 | nDCG@10 | matched queries (alias / dense) | pool additions, mean | p50 ms |", "|---|---|---|---|---|---|---|"]
        rows = [("baseline (x13)", base, None)] + [(f"c_{m}", d, m) for m, d in V.items()]
        for name, d, m in rows:
            ex = d["extra"]
            mq = f"{ex.get('concept_queries_matched', 0)} ({ex.get('concept_queries_alias', 0)} / {ex.get('concept_queries_dense', 0)})" if m else "-"
            adds = np.mean([len(q.get("concept", {}).get("pool_added", [])) for q in d["per_query"]]) if m else 0.0
            out.append(f"| {name} | {metric(d, 'recall@5').mean():.3f} | {metric(d, 'mrr@10').mean():.3f} | {metric(d, 'ndcg@10').mean():.3f} | {mq} | "
                       f"{adds:.1f} | {d['timing']['query_latency_ms']['p50']:.0f} |")

        out += ["", "### 2. nDCG@10, variant - baseline (95% interval: question-level / document-cluster)", "",
                "| variant | subset | n | mean diff | question CI | cluster CI | better/worse/tie |", "|---|---|---|---|---|---|---|"]
        for m, d in V.items():
            diff = metric(d, "ndcg@10") - b_ndcg
            mk = matched(d)
            for sub, mask in (("all", np.ones(len(diff), bool)), ("matched", mk), ("unmatched", ~mk)):
                if mask.sum() == 0:
                    continue
                cl = [c for c, keep in zip(clusters, mask) if keep]
                c = compare(diff[mask], cl)
                cc = ci(c, "ci_cluster") if "ci_cluster" in c else "-"
                out.append(f"| c_{m} | {sub} | {int(mask.sum())} | {c['mean']:+.3f} | {ci(c, 'ci_iid')} | {cc} | {c['better']}/{c['worse']}/{c['tie']} |")

        out += ["", "### 3. Matched queries", "", "| qid | concepts (how) | baseline nDCG | " + " | ".join(f"c_{m}" for m in V) + " |",
                "|---|---|---|" + "---|" * len(V)]
        first = next(iter(V.values()))
        for i, q in enumerate(first["per_query"]):
            c = q.get("concept", {})
            if not c.get("ids"):
                continue
            how = ", ".join([f"{k} (alias: {'; '.join(v)})" for k, v in c["alias"].items()] + [f"{k} (dense {s:.2f})" for k, s in c["dense"]])
            out.append(f"| {q['qid']} | {how} | {b_ndcg[i]:.3f} | " + " | ".join(f"{metric(d, 'ndcg@10')[i]:.3f}" for d in V.values()) + " |")

        out += ["", "### 4. Concepts", "", "| concept | chunks | queries matched |", "|---|---|---|"]
        stats = first["timing"]["index"]
        per_chunk = {}
        for v in stats.values():
            if isinstance(v, dict) and "chunks_per_concept" in v:
                per_chunk = v["chunks_per_concept"]
        hits = Counter(cid for q in first["per_query"] for cid in q.get("concept", {}).get("ids", []))
        for cid, n in sorted(per_chunk.items(), key=lambda x: -x[1]):
            out.append(f"| {cid} | {n} | {hits.get(cid, 0)} |")
        out.append("")

    # 5. 사람이 쓴 질문 10개
    base_u = json.loads((HR / "user_questions_answers.json").read_text(encoding="utf-8"))["rows"]
    out += ["## Human-written questions (10, cite_refuse_v1)", "", "| variant | refused | top-5 changed | D05 targets in reranker pool | D05 target ranks (top 10) | D05 outcome |", "|---|---|---|---|---|---|"]
    out.append(f"| baseline | {sum(r['blocked'] for r in base_u)} | - | - | - | {'refused' if next(r for r in base_u if r['qid'] == 'D05')['blocked'] else 'answered'} |")
    for m in MODES:
        p = HR / f"user_questions_answers_c_{m}.json"
        if not p.exists():
            continue
        rows = json.loads(p.read_text(encoding="utf-8"))["rows"]
        d05 = next(r for r in rows if r["qid"] == "D05")
        changed = sum(r["best_top5"] != b["best_top5"] for r, b in zip(rows, base_u))
        in_pool = [t for t in D05_TARGETS if t in d05.get("best_rerank_pool", [])]
        ranks = {t: (d05.get("best_ranked10", []).index(t) + 1 if t in d05.get("best_ranked10", []) else None) for t in D05_TARGETS}
        rk = ", ".join(f"{t.split('#')[0][-6:]}#{t.split('#')[1]}={r if r else '-'}" for t, r in ranks.items())
        out.append(f"| c_{m} | {sum(r['blocked'] for r in rows)} | {changed} | {len(in_pool)}/{len(D05_TARGETS)} | {rk} | {'refused' if d05['blocked'] else 'answered'} |")
    out += ["", "Per question (blocked = the answer was replaced by the fixed message):", "", "| qid | baseline | " + " | ".join(f"c_{m}" for m in MODES) + " |", "|---|---|" + "---|" * len(MODES)]
    variants = {m: {r["qid"]: r for r in json.loads((HR / f"user_questions_answers_c_{m}.json").read_text(encoding="utf-8"))["rows"]}
                for m in MODES if (HR / f"user_questions_answers_c_{m}.json").exists()}
    for b in base_u:
        cells = []
        for m in MODES:
            r = variants.get(m, {}).get(b["qid"])
            if r is None:
                cells.append("-")
            else:
                cells.append(("blocked" if r["blocked"] else "answered") + (" (top-5 changed)" if r["best_top5"] != b["best_top5"] else "") +
                             (f" [{', '.join(r['concept']['ids'])}]" if r.get("concept", {}) and r["concept"].get("ids") else ""))
        out.append(f"| {b['qid']} | {'blocked' if b['blocked'] else 'answered'} | " + " | ".join(cells) + " |")
    text = "\n".join(out) + "\n"
    (RES / "concept_analysis.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
