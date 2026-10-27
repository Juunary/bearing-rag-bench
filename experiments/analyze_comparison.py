"""Compare this repository's retrieval with LlamaIndex, Haystack and AutoRAG -> experiments/results/cmp_analysis.md.

[EN]
- Inputs: experiments/results/cmp_*.json (written by comparison/run_frameworks.py and comparison/collect_autorag.py;
  every system returns ranked chunk ids over the same 346 chunks and the same 90 questions) and the repository's own
  v2_* results. All numbers come from ragbench.metrics; no framework metric is used.
- Sections: (1) every system; (2) paired comparisons (nDCG@10, A - B, interval
  by question and by primary-evidence document, sign test; pairs chosen after seeing the numbers, no multiplicity correction); (3) nDCG@10 per language pair;
  (4) generation and judged answers when v2g_cmp_* results exist.
- Latency is not comparable across rows: this repository's English-pivot rows include query translation, framework rows
  are single-process calls, AutoRAG rows are its own batch time divided by the number of questions.
- Usage: uv run python experiments/analyze_comparison.py

[KO]
- 입력: experiments/results/cmp_*.json(comparison/run_frameworks.py, comparison/collect_autorag.py가 생성. 모든
  시스템이 같은 346 청크·같은 90문항에 대해 청크 ID 순위를 반환)와 저장소의 v2_* 결과. 모든 숫자는
  ragbench.metrics로 계산하며 프레임워크 자체 지표는 쓰지 않는다.
- 구성: (1) 모든 시스템; (2) 쌍체 비교(nDCG@10, A - B, 질문 단위·주 근거 문서 단위 구간, 부호 검정; 비교 쌍은
  수치를 본 뒤 정했고 다중 비교 보정 없음); (3) 언어쌍별 nDCG@10; (4) v2g_cmp_* 결과가 있으면 생성·판정 답변.
- 지연은 행 사이에 비교할 수 없다. 이 저장소의 영어 피벗 행은 질의 번역을 포함하고, 프레임워크 행은 단일
  프로세스 호출, AutoRAG 행은 자체 배치 시간을 질문 수로 나눈 값이다.
- 사용: uv run python experiments/analyze_comparison.py
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

# (표시 이름, 결과 파일, 구분)
SYSTEMS = [
    ("this repo: BM25 whitespace", "v2_b_bm25_whitespace", "default"),
    ("this repo: BM25 kiwi", "v2_b_bm25_kiwi", "default"),
    ("this repo: dense bge-m3", "v2_b_dense", "default"),
    ("this repo: RRF", "v2_b_rrf", "default"),
    ("this repo: RRF + reranker", "v2_b_rrf_rerank", "tuned"),
    ("this repo: English BM25", "v2_b_bm25_en", "tuned"),
    ("this repo: English RRF + reranker (original text)", "v2_b_rrf_en_rerank", "tuned"),
    ("this repo: English RRF + reranker (English text)", "v2_x2_rerank_en_text", "tuned"),
    ("LlamaIndex: BM25", "cmp_li_bm25", "default"),
    ("LlamaIndex: vector", "cmp_li_vector", "default"),
    ("LlamaIndex: hybrid (reciprocal rerank fusion)", "cmp_li_hybrid_rrf", "default"),
    ("LlamaIndex: hybrid + reranker", "cmp_li_hybrid_rerank", "tuned"),
    ("Haystack: BM25", "cmp_hs_bm25", "default"),
    ("Haystack: dense", "cmp_hs_dense", "default"),
    ("Haystack: hybrid (RRF)", "cmp_hs_hybrid_rrf", "default"),
    ("Haystack: hybrid + reranker", "cmp_hs_hybrid_rerank", "tuned"),
    ("AutoRAG: BM25 space", "cmp_ar_bm25_space", "search"),
    ("AutoRAG: BM25 porter_stemmer", "cmp_ar_bm25_porter_stemmer", "search"),
    ("AutoRAG: BM25 ko_kiwi", "cmp_ar_bm25_ko_kiwi", "search"),
    ("AutoRAG: vector", "cmp_ar_vector", "search"),
    ("AutoRAG: hybrid RRF", "cmp_ar_hybrid_rrf", "search"),
    ("AutoRAG: hybrid CC (mm)", "cmp_ar_hybrid_cc_mm", "search"),
    ("AutoRAG: hybrid CC (z)", "cmp_ar_hybrid_cc_z", "search"),
    ("AutoRAG: hybrid CC (dbsf)", "cmp_ar_hybrid_cc_dbsf", "search"),
    ("AutoRAG: reranker FlagEmbedding (best pipeline)", "cmp_ar_rerank_flag", "search"),
    ("AutoRAG: reranker SentenceTransformer", "cmp_ar_rerank_st", "search"),
]

# 비교 쌍: 같은 구조끼리, 그리고 이 저장소 최고 구성과 (검색 수치를 본 뒤 정함)
PAIRS = [
    ("cmp_li_vector", "v2_b_dense"), ("cmp_hs_dense", "v2_b_dense"),
    ("cmp_li_bm25", "v2_b_bm25_whitespace"), ("cmp_hs_bm25", "v2_b_bm25_whitespace"),
    ("cmp_li_hybrid_rerank", "v2_b_rrf_rerank"), ("cmp_hs_hybrid_rerank", "v2_b_rrf_rerank"), ("cmp_ar_rerank_flag", "v2_b_rrf_rerank"),
    ("cmp_ar_rerank_flag", "cmp_li_hybrid_rerank"),
    ("v2_x2_rerank_en_text", "cmp_ar_rerank_flag"), ("v2_x2_rerank_en_text", "cmp_li_hybrid_rerank"), ("v2_x2_rerank_en_text", "cmp_hs_hybrid_rerank"),
    ("v2_b_bm25_en", "cmp_ar_bm25_ko_kiwi"),
]
GEN = [("this repo (English RRF + reranker, original text)", "v2g_ret_b_rrf_en_rerank"), ("this repo (English RRF + reranker, English text)", "v2g_ret_x2_rerank_en_text"),
       ("LlamaIndex hybrid + reranker", "v2g_cmp_li"), ("Haystack hybrid + reranker", "v2g_cmp_hs"), ("AutoRAG best pipeline", "v2g_cmp_ar")]


def load(name: str) -> dict | None:
    p = RES / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ndcg(d: dict) -> np.ndarray:
    return np.array([q["metrics"]["ndcg@10"] for q in d["per_query"]])


def main() -> None:
    R = {n: load(n) for _, n, _ in SYSTEMS}
    missing = [n for n, d in R.items() if d is None]
    if missing:
        raise SystemExit(f"missing results: {missing}")
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    qids = [q["qid"] for q in R["v2_b_dense"]["per_query"]]
    for n, d in R.items():
        if [q["qid"] for q in d["per_query"]] != qids:
            raise SystemExit(f"question order differs in {n}")
    types = np.array([queries[i]["type"] for i in qids])
    clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]

    out = ["# Comparison with LlamaIndex, Haystack and AutoRAG (90 questions, 346 chunks)", "",
           f"clusters (primary-evidence documents): {len(set(clusters))}", "",
           "## 1. All systems", "",
           "tier: default = framework defaults of the component, tuned = hybrid + reranker or English pivot, search = AutoRAG module of its search.", "",
           "| system | tier | R@5 | MRR@10 | nDCG@10 | mono | cross | p50 ms (not comparable) |", "|---|---|---|---|---|---|---|---|"]
    for label, n, tier in SYSTEMS:
        d = R[n]
        o, x = d["metrics"]["overall"], ndcg(d)
        out.append(f"| {label} | {tier} | {o['recall@5']:.3f} | {o['mrr@10']:.3f} | {o['ndcg@10']:.3f} | {x[types == 'mono'].mean():.3f} | "
                   f"{x[types == 'cross'].mean():.3f} | {d['timing']['query_latency_ms']['p50']:.1f} |")

    out += ["", f"## 2. Paired comparisons (nDCG@10, A - B; {len(PAIRS)} comparisons chosen after the retrieval numbers were known, no multiplicity correction)", "",
            "| A | B | mean diff | 95% CI (question) | 95% CI (document cluster) | better/worse/tie | sign-test p |", "|---|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        c = compare(ndcg(R[a]) - ndcg(R[b]), clusters)
        out.append(f"| {a} | {b} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | "
                   f"{c['better']}/{c['worse']}/{c['tie']} | {c['sign_p']:.3f} |")

    pairs_of: dict[str, list[int]] = {}
    for i, qid in enumerate(qids):
        pairs_of.setdefault(f"{queries[qid]['q_lang']}->{queries[qid]['gold'][0]['doc_lang']}", []).append(i)
    keys = sorted(pairs_of)
    out += ["", "## 3. nDCG@10 per language pair (10 questions each)", "", "| system | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for label, n, _ in SYSTEMS:
        if n in ("v2_b_rrf", "cmp_li_hybrid_rrf", "cmp_hs_hybrid_rrf", "cmp_ar_bm25_porter_stemmer", "cmp_ar_bm25_space", "cmp_ar_hybrid_cc_z", "cmp_ar_hybrid_cc_dbsf",
                 "cmp_ar_rerank_st", "cmp_ar_hybrid_rrf", "cmp_ar_hybrid_cc_mm"):
            continue
        x = ndcg(R[n])
        out.append(f"| {label} | " + " | ".join(f"{x[pairs_of[k]].mean():.2f}" for k in keys) + " |")

    gen_rows = [(label, n, load(n), load(f"s3_judge_{n}")) for label, n in GEN]
    gen_rows = [r for r in gen_rows if r[2] is not None and r[3] is not None]
    if gen_rows:
        out += ["", "## 4. Generation (base bf16 Qwen3-4B-Instruct-2507, prompt cite_v1, top 5) and judge (Qwen3-8B)", "",
                "See run_judge.py for the outcome classes. cites_gold = cited a gold chunk; judged rates are among the answers each dimension applies to.", ""]
        out += ["| retrieval feeding the generator | gold in context | cites_gold | faithfulness | correctness | answer relevance | refused |", "|---|---|---|---|---|---|---|"]
        for label, n, g, j in gen_rows:
            out.append(f"| {label} | {_fmt(g, 'gold_in_context')} | {_fmt(g, 'cites_gold')} | {_jfmt(j, 'faithfulness')} | {_jfmt(j, 'correctness')} | "
                       f"{_jfmt(j, 'answer_relevance')} | {_fmt(g, 'refused')} |")
    if gen_rows:
        out += _generation_pairs(qids, clusters)
    text = "\n".join(out) + "\n"
    (RES / "cmp_analysis.md").write_text(text, encoding="utf-8")
    print(text)


GEN_PAIRS = [("cmp_ar", "cmp_li"), ("cmp_ar", "cmp_hs"), ("cmp_li", "cmp_hs"),
             ("ret_x2_rerank_en_text", "cmp_ar"), ("ret_x2_rerank_en_text", "cmp_li"), ("ret_x2_rerank_en_text", "cmp_hs"),
             ("ret_b_rrf_en_rerank", "cmp_ar")]


def _generation_pairs(qids: list[str], clusters: list[str]) -> list[str]:
    """Per-question differences of answer metrics (A - B); judged metrics use the questions where both judgements apply."""
    from analyze_v2_generation import per_query_matrix

    out = ["", "## 5. Paired generation comparisons (A - B, 95% interval by primary-evidence document; pairs chosen after the generation means were known, no multiplicity correction)", "",
           "| A | B | metric | mean diff | 95% CI (document cluster) | better/worse/tie | n |", "|---|---|---|---|---|---|---|"]
    for a, b in GEN_PAIRS:
        ma, mb = per_query_matrix(a), per_query_matrix(b)
        if ma is None or mb is None:
            continue
        for metric in ("gold_in_context", "cites_gold", "faithfulness", "correctness"):
            d = ma[metric] - mb[metric]
            keep = ~np.isnan(d)
            c = compare(d[keep], [cl for cl, k in zip(clusters, keep) if k])
            out.append(f"| {a} | {b} | {metric} | {c['mean']:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | "
                       f"{c['better']}/{c['worse']}/{c['tie']} | {int(keep.sum())} |")
    return out


def _fmt(g: dict, key: str) -> str:
    v = _find(g.get("metrics", {}), key)
    return "n/a" if v is None else f"{v:.3f}"


def _jfmt(j: dict, key: str) -> str:
    v = _find(j.get("metrics", j), key)
    return "n/a" if v is None else f"{v:.3f}"


def _find(obj, key: str):
    """First numeric value stored under `key` anywhere in a nested result (the layouts of generation and judge files differ)."""
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], (int, float)):
            return float(obj[key])
        for v in obj.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


if __name__ == "__main__":
    main()
