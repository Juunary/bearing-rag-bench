"""Analyse retrieval on the Wikipedia + PDF corpus -> experiments/results/pdf_analysis.md.

[EN]
- Inputs: experiments/results/pdf_*.json (eval/queries_pdf.jsonl, 48 questions with PDF primary evidence) and
  v2pdf_*.json (the 90 v2 questions on the same 903-chunk corpus), plus the v2_* results on the Wikipedia corpus.
- Sections: (1) every setting on the PDF questions, overall, mono / cross, and by evidence kind (text, table, caption)
  and for the table questions whose header is in another chunk; (2) nDCG@10 per language pair; (3) paired comparisons
  on the PDF questions (interval by question; only 6 primary documents, so the cluster interval is printed with the
  number of clusters and is unreliable); (5) chunks with repeated table caption and header rows (pdfth_*) against the
  plain chunks; (4) the v2 questions with and without the 557 PDF chunks (paired by question,
  interval by primary-evidence document), and how often a PDF chunk enters the top 5 of a v2 question.
- Usage: uv run python experiments/analyze_pdf.py

[KO]
- 입력: experiments/results/pdf_*.json(eval/queries_pdf.jsonl, 주 근거가 PDF인 48문항), v2pdf_*.json(같은 903 청크
  코퍼스의 v2 90문항), 위키 코퍼스의 v2_* 결과.
- 구성: (1) PDF 질문에서 설정별 전체·단일/교차·근거 종류별(본문, 표, 캡션)과 머리글이 다른 청크에 있는 표 문항;
  (2) 언어쌍별 nDCG@10; (3) PDF 질문의 쌍체 비교(질문 단위 구간. 주 근거 문서가 6개뿐이라 군집 구간은 군집 수와 함께
  적고 신뢰하기 어렵다); (5) 표 캡션·머리글 반복 청크(pdfth_*)와 기본 청크 비교; (4) PDF 청크 557개가 있을 때와 없을 때의 v2 질문(질문별 쌍, 주 근거 문서 단위 구간)과 v2 질문의
  상위 5에 PDF 청크가 들어간 빈도.
- 사용: uv run python experiments/analyze_pdf.py
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
NAMES = ["b_bm25_kiwi", "b_dense", "b_rrf_rerank", "b_bm25_en", "b_rrf_en_rerank", "x2_rerank_en_text",
         "x12_dense_rerank", "x13_dense_en", "x13_dense_en_rerank_en_text", "x13_rrf_en_dense_en_rerank_en_text"]
PAIRS = [("x2_rerank_en_text", "b_rrf_rerank"), ("x13_dense_en_rerank_en_text", "x2_rerank_en_text"),
         ("x13_dense_en", "b_dense"), ("b_bm25_en", "b_bm25_kiwi"), ("x12_dense_rerank", "b_rrf_rerank")]


def load(name: str) -> dict | None:
    p = RES / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ndcg(d: dict) -> np.ndarray:
    return np.array([q["metrics"]["ndcg@10"] for q in d["per_query"]])


def main() -> None:
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_pdf.jsonl")}
    P = {n: load(f"pdf_{n}") for n in NAMES}
    P = {n: d for n, d in P.items() if d is not None}
    first = next(iter(P.values()))
    qids = [q["qid"] for q in first["per_query"]]
    kind = np.array([queries[i]["evidence_kind"] for i in qids])
    typ = np.array([queries[i]["type"] for i in qids])
    split = np.array(["table_header_split" in queries[i].get("note", "") for i in qids])
    clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
    cnt = {k: int((kind == k).sum()) for k in ("text", "table", "caption")}
    out = ["# Retrieval on Wikipedia + PDF (903 chunks)", "",
           f"## 1. PDF questions ({len(qids)}; text {cnt['text']}, table {cnt['table']}, caption {cnt['caption']}; table header in another chunk {int(split.sum())})", "",
           "| setting | R@5 | MRR@10 | nDCG@10 | mono | cross | text | table | caption | table, header split |", "|---|---|---|---|---|---|---|---|---|---|"]
    for n, d in P.items():
        o, x = d["metrics"]["overall"], ndcg(d)
        out.append(f"| {n} | {o['recall@5']:.3f} | {o['mrr@10']:.3f} | {o['ndcg@10']:.3f} | {x[typ == 'mono'].mean():.3f} | {x[typ == 'cross'].mean():.3f} | "
                   f"{x[kind == 'text'].mean():.3f} | {x[kind == 'table'].mean():.3f} | {x[kind == 'caption'].mean():.3f} | {x[split].mean():.3f} |")

    pairs_of: dict[str, list[int]] = {}
    for i, qid in enumerate(qids):
        pairs_of.setdefault(f"{queries[qid]['q_lang']}->{queries[qid]['gold'][0]['doc_lang']}", []).append(i)
    keys = sorted(pairs_of)
    out += ["", "## 2. nDCG@10 per language pair (8 questions each)", "", "| setting | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
    for n, d in P.items():
        x = ndcg(d)
        out.append(f"| {n} | " + " | ".join(f"{x[pairs_of[k]].mean():.2f}" for k in keys) + " |")

    out += ["", f"## 3. Paired comparisons on the PDF questions (nDCG@10, A - B; cluster interval over only {len(set(clusters))} documents)", "",
            "| A | B | mean diff | 95% CI (question) | 95% CI (document cluster) | better/worse/tie | sign-test p |", "|---|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        if a in P and b in P:
            c = compare(ndcg(P[a]) - ndcg(P[b]), clusters)
            out.append(f"| {a} | {b} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | "
                       f"{c['better']}/{c['worse']}/{c['tie']} | {c['sign_p']:.3f} |")

    v2q = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    pdf_ids = {json.loads(l)["doc_id"] for l in (REPO / "data" / "processed" / "docs_pdf.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    out += ["", "## 4. v2 questions (90) without and with the PDF chunks", "",
            "PDF chunks are not in the v2 gold, so a relevant PDF chunk in the ranking counts as a miss.", "",
            "| setting | nDCG@10 wiki | nDCG@10 wiki + pdf | diff | 95% CI (document cluster) | questions with a PDF chunk in top 5 |", "|---|---|---|---|---|---|"]
    for n in NAMES:
        a, b = load(f"v2pdf_{n}"), load(f"v2_{n}")
        if a is None or b is None:
            continue
        cl = [v2q[q["qid"]]["gold"][0]["doc_id"] for q in a["per_query"]]
        c = compare(ndcg(a) - ndcg(b), cl)
        intr = sum(any(cid.split("#")[0] in pdf_ids for cid in q["ranked"][:5]) for q in a["per_query"])
        out.append(f"| {n} | {ndcg(b).mean():.3f} | {ndcg(a).mean():.3f} | {c['mean']:+.3f} | {c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | {intr}/{len(cl)} |")
    TH = {n: load(f"pdfth_{n}") for n in NAMES}
    TH = {n: d for n, d in TH.items() if d is not None and n in P}
    if TH:
        out += ["", "## 5. Table caption and header rows repeated in chunks (chunking.table_header; PDF questions)", "",
                "| setting | nDCG@10 | with headers | diff (95% CI, question) | table (15) | with headers | header split (5) | with headers |",
                "|---|---|---|---|---|---|---|---|"]
        for n, d in TH.items():
            a, b = ndcg(d), ndcg(P[n])
            c = compare(a - b)
            out.append(f"| {n} | {b.mean():.3f} | {a.mean():.3f} | {c['mean']:+.3f} ({c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f}) | "
                       f"{b[kind == 'table'].mean():.3f} | {a[kind == 'table'].mean():.3f} | {b[split].mean():.3f} | {a[split].mean():.3f} |")
    text = "\n".join(out) + "\n"
    (RES / "pdf_analysis.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
