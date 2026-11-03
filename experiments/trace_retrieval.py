"""Trace where given chunks drop out of one retrieval config for one question -> experiments/results/<name>.md.

[EN]
- Role: a refusal can come from retrieval (the chunk with the answer never reaches the generator) or from the
  corpus (no such chunk). For a question and a list of target chunks this prints the translated query and
  each target's rank in every stage of the config: English BM25 and English dense over the whole corpus,
  the RRF list (each part contributes its top `fusion_candidates`), the reranker pool (RRF top `rerank_top_n`)
  and the final order. The reranker also scores targets that did not reach its pool, to show where they would land.
- BM25 terms: the query tokens that occur in each target (English text), with their document frequency.
- Variants (--variant): extra English queries searched directly (no translation), to test a wording change.
- Only for configs of the form hybrid_rerank over English BM25 + English dense (the PDF-corpus best config).
- Usage: uv run python experiments/trace_retrieval.py --config configs/pdf/pdfth_x13_rrf_en_dense_en_rerank_en_text.json
  --question "..." --target id1 id2 --name d05_retrieval_trace [--variant "english query" ...]

[KO]
- 역할: 거절은 검색(답이 있는 청크가 생성 모델까지 가지 못함) 때문일 수도, 코퍼스(그런 청크가 없음) 때문일 수도 있다.
  질문 하나와 대상 청크 목록을 받아 번역된 질의와, 설정의 단계별 대상 청크 순위를 낸다: 전체 코퍼스에서의 영어 BM25·영어
  dense 순위, RRF 목록(각 검색기가 상위 `fusion_candidates`개를 넘김), 리랭커 후보(RRF 상위 `rerank_top_n`), 최종 순서.
  리랭커 후보에 못 든 대상도 리랭커로 점수를 매겨, 들어갔다면 몇 위였을지 보인다.
- BM25 단어: 질의 토큰 중 대상 청크(영어 텍스트)에 있는 것과 그 문서 빈도.
- 변형(--variant): 번역 없이 바로 검색하는 영어 질의. 표현을 바꾸면 순위가 달라지는지 확인한다.
- 영어 BM25 + 영어 dense 위의 hybrid_rerank 설정(PDF 코퍼스 최고 설정)만 대상이다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.retrieval.factory import build_retriever  # noqa: E402


def ranks(hits: list[tuple[str, float]]) -> dict[str, tuple[int, float]]:
    return {cid: (i, s) for i, (cid, s) in enumerate(hits, start=1)}


def trace(retriever, cfg: ExperimentConfig, n: int, en_query: str, targets: list[str], top: int) -> tuple[list[str], list[str]]:
    """Stage ranks for one English query (the parts are searched with it directly, no translation) and the final order."""
    r = cfg.retrieval
    bm25, dense = retriever.base.retrievers                     # 영어 BM25(EnglishBM25Retriever), 영어 dense(EnglishPivotRetriever)
    b = ranks(bm25.inner.search(en_query, n))
    d = ranks(dense.inner.search(en_query, n))
    fused: dict[str, float] = {}
    for part in (b, d):
        for cid, (rk, _) in part.items():
            if rk <= r.fusion_candidates:
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (r.rrf_k + rk)
    rrf = ranks(sorted(fused.items(), key=lambda x: -x[1]))
    pool = [cid for cid, (rk, _) in rrf.items() if rk <= r.rerank_top_n]
    # 리랭커: 후보 30개와 후보 밖 대상을 함께 채점하되, 최종 순위는 후보 안에서만 매긴다 (점수는 쌍마다 독립)
    extra = [t for t in targets if t not in pool]
    scores = dict(zip(pool + extra, retriever.ce.score(en_query, [retriever.chunk_text[c] for c in pool + extra])))
    final = sorted(pool, key=lambda c: -scores[c])
    fin = {c: i for i, c in enumerate(final, start=1)}

    def would(c: str) -> int:                                   # 후보에 들었다면 리랭커 순위 (후보 밖 대상 하나만 넣었을 때)
        return 1 + sum(scores[p] > scores[c] for p in pool)

    out = ["| chunk | BM25 rank | dense rank (cos) | RRF rank | in reranker pool | reranker score | final rank |",
           "|---|---|---|---|---|---|---|"]
    for c in targets + [x for x in final[:top] if x not in targets]:
        tag = "" if c in targets else " (final top)"
        fr = fin[c] if c in fin else f"- (would be {would(c)})"
        out.append(f"| {c}{tag} | {b[c][0]} | {d[c][0]} ({d[c][1]:.3f}) | {rrf[c][0] if c in rrf else '-'} | "
                   f"{'yes' if c in pool else 'no'} | {scores[c]:.3f} | {fr} |")
    out += ["", f"Cut-offs: RRF takes each part's top {r.fusion_candidates}; reranker pool = RRF top {r.rerank_top_n}; "
            f"generator reads the final top 5. Reranker score of final rank 5: {scores[final[4]]:.3f}.", ""]
    # BM25 단어: 질의 토큰이 대상 청크에 있는지 (BM25 토크나이저 그대로)
    tok = bm25.inner.tokenize
    q_tokens = list(dict.fromkeys(tok(en_query)))
    docs = {cid: set(tok(t)) for cid, t in retriever.chunk_text.items()}
    df = {t: sum(t in s for s in docs.values()) for t in q_tokens}
    out += ["Query tokens (document frequency in the English chunk texts): " + ", ".join(f"{t} ({df[t]})" for t in q_tokens), "",
            "| chunk | query tokens present |", "|---|---|"]
    for c in targets + final[:top]:
        out.append(f"| {c} | {', '.join(t for t in q_tokens if t in docs[c])} |")
    return out, final


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--target", nargs="+", required=True)
    ap.add_argument("--variant", action="append", default=[], help="extra English query, searched without translation")
    ap.add_argument("--name", required=True, help="output file stem in experiments/results/")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    # 실제 검색 경로로 한 번 돌려 번역(캐시)과 최종 순서를 얻고, 단계 추적이 같은 결과를 내는지 확인한다
    served = [cid for cid, _ in retriever.search(args.question, cfg.retrieval.top_k)]
    en_query = retriever.query_translator.translate(args.question, "query")["text"]
    out = [f"# Retrieval trace: {args.name}", "", f"Config: `{args.config.name}`", "", f"Question: {args.question}", "",
           f"Translated query: {en_query}", "", f"Served top {args.top}: {', '.join(served[:args.top])}", "",
           "## Translated query", ""]
    lines, final = trace(retriever, cfg, len(chunks), en_query, args.target, args.top)
    # 추적한 최종 순서가 실제 검색과 다르면 단계 순위를 믿을 수 없으므로 멈춘다
    if final[:args.top] != served[:args.top]:
        raise SystemExit(f"trace {final[:args.top]} != served {served[:args.top]}")
    out += lines
    for v in args.variant:
        out += ["", f"## Variant: {v}", "", *trace(retriever, cfg, len(chunks), v, args.target, args.top)[0]]
    text = "\n".join(out) + "\n"
    (REPO / "experiments" / "results" / f"{args.name}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
