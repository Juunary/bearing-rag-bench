"""Write configs/v2/*.json: every retrieval experiment on the 90-question set (baselines + improvements).

[EN]
- Role: one place that lists the experiments of the improvement round, so the set is explicit and
  reproducible. Each config only differs from its stage-1/5 relative in eval_path (eval/queries_v2.jsonl)
  and in the one knob it tests; exp_id = v2_<name>.
- Groups: baselines (b_*), x1 three-way RRF, x2 reranker candidates and input language, x3 glossary,
  x4 stemming, x5 query expansion, x6 chunk size and contextual prefix, x11 translation cost.
- Usage: uv run python scripts/make_v2_configs.py; run them with experiments/run_suite.py.

[KO]
- 역할: 개선 라운드의 실험을 한 곳에 나열해 구성이 명시적이고 재현되게 한다. 각 설정은 1·5단계 원형과
  eval_path(eval/queries_v2.jsonl)와 시험하는 값 하나만 다르다. exp_id = v2_<이름>.
- 묶음: 기준선(b_*), x1 3중 RRF, x2 리랭커 후보 수·입력 언어, x3 용어집, x4 어간 추출, x5 질의 확장,
  x6 청크 크기·맥락 접두사, x11 번역 비용.
- 사용: uv run python scripts/make_v2_configs.py; 실행은 experiments/run_suite.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "configs" / "v2"

KIWI = {"bm25_tokenizer": "kiwi"}
EN = {"bm25_tokenizer": "whitespace", "bm25_english_pivot": True}
HYB = {"embedding_model": "BAAI/bge-m3", "rrf_k": 60, "fusion_candidates": 50}
RR = {"rerank_model": "BAAI/bge-reranker-v2-m3", "rerank_top_n": 30}

# name: (description, retrieval dict, chunking dict)
EXPERIMENTS: dict[str, tuple[str, dict, dict]] = {
    # --- baselines ---
    "b_bm25_whitespace": ("BM25 whitespace tokenizer, original text", {"method": "bm25", "bm25_tokenizer": "whitespace"}, {}),
    "b_bm25_kiwi": ("BM25 kiwi tokenizer, original text", {"method": "bm25", **KIWI}, {}),
    "b_bm25_subword": ("BM25 bge-m3 subword tokenizer, original text", {"method": "bm25", "bm25_tokenizer": "subword"}, {}),
    "b_dense": ("dense bge-m3 + HNSW", {"method": "dense", "embedding_model": "BAAI/bge-m3"}, {}),
    "b_rrf": ("RRF over BM25 kiwi + dense", {"method": "hybrid", **KIWI, **HYB}, {}),
    "b_rrf_rerank": ("RRF over BM25 kiwi + dense, reranker top 30", {"method": "hybrid_rerank", **KIWI, **HYB, **RR}, {}),
    "b_bm25_en": ("English-pivot BM25 (chunk-first translation)", {"method": "bm25", **EN}, {}),
    "b_rrf_en": ("RRF over English-pivot BM25 + dense", {"method": "hybrid", **EN, **HYB}, {}),
    "b_rrf_en_rerank": ("RRF over English-pivot BM25 + dense, reranker top 30", {"method": "hybrid_rerank", **EN, **HYB, **RR}, {}),
    # --- x1: three-way RRF (English BM25 + original BM25 + dense) ---
    "x1_rrf3": ("3-way RRF: English BM25 + kiwi BM25 + dense", {"method": "hybrid", **EN, **HYB, "bm25_include_original": True}, {}),
    "x1_rrf3_rerank": ("3-way RRF then reranker top 30", {"method": "hybrid_rerank", **EN, **HYB, **RR, "bm25_include_original": True}, {}),
    # --- x2: reranker candidates and input language ---
    "x2_rerank_n50": ("English-pivot RRF, reranker top 50", {"method": "hybrid_rerank", **EN, **HYB, **{**RR, "rerank_top_n": 50}}, {}),
    "x2_rerank_n100": ("English-pivot RRF, reranker top 100", {"method": "hybrid_rerank", **EN, **HYB, **{**RR, "rerank_top_n": 100}}, {}),
    "x2_rerank_en_text": ("English-pivot RRF, reranker reads English chunks and English query (top 30)",
                          {"method": "hybrid_rerank", **EN, **HYB, **RR, "rerank_text": "english"}, {}),
    "x2_orig_rerank_n100": ("kiwi RRF (no translation), reranker top 100", {"method": "hybrid_rerank", **KIWI, **HYB, **{**RR, "rerank_top_n": 100}}, {}),
    # --- x3: glossary term hints in the translation prompts (needs chunks_en_*_gl.jsonl) ---
    "x3_bm25_en_gl": ("English-pivot BM25, translations with glossary hints", {"method": "bm25", **EN, "translate_glossary": True}, {}),
    "x3_rrf_en_rerank_gl": ("English-pivot RRF + reranker, glossary translations",
                            {"method": "hybrid_rerank", **EN, **HYB, **RR, "translate_glossary": True}, {}),
    # --- x4: English stemming / stopwords ---
    "x4_bm25_en_stem": ("English-pivot BM25, Snowball stemmer", {"method": "bm25", **{**EN, "bm25_tokenizer": "en_stem"}}, {}),
    "x4_bm25_en_stem_stop": ("English-pivot BM25, stemmer + stopwords", {"method": "bm25", **{**EN, "bm25_tokenizer": "en_stem_stop"}}, {}),
    # --- x5: query expansion on the English-pivot BM25 ---
    "x5_bm25_en_multi": ("English-pivot BM25, translation + 2 alternative wordings fused by RRF", {"method": "bm25", **EN, "query_expansion": "multi"}, {}),
    "x5_bm25_en_hyde": ("English-pivot BM25, HyDE (hypothetical passage)", {"method": "bm25", **EN, "query_expansion": "hyde"}, {}),
    # --- x6: chunk size (original text) and contextual prefix ---
    "x6_dense_c256": ("dense, chunks 256/48", {"method": "dense", "embedding_model": "BAAI/bge-m3"}, {"size": 256}),
    "x6_dense_c512": ("dense, chunks 512/48", {"method": "dense", "embedding_model": "BAAI/bge-m3"}, {"size": 512}),
    "x6_bm25_kiwi_c256": ("BM25 kiwi, chunks 256/48", {"method": "bm25", **KIWI}, {"size": 256}),
    "x6_bm25_kiwi_c512": ("BM25 kiwi, chunks 512/48", {"method": "bm25", **KIWI}, {"size": 512}),
    "x6_rrf_rerank_c256": ("kiwi RRF + reranker, chunks 256/48", {"method": "hybrid_rerank", **KIWI, **HYB, **RR}, {"size": 256}),
    "x6_rrf_rerank_c512": ("kiwi RRF + reranker, chunks 512/48", {"method": "hybrid_rerank", **KIWI, **HYB, **RR}, {"size": 512}),
    "x6_dense_ctx": ("dense, title and section path prefix", {"method": "dense", "embedding_model": "BAAI/bge-m3", "contextual_prefix": True}, {}),
    "x6_bm25_kiwi_ctx": ("BM25 kiwi, title and section path prefix", {"method": "bm25", **KIWI, "contextual_prefix": True}, {}),
    "x6_rrf_rerank_ctx": ("kiwi RRF + reranker, title and section path prefix",
                          {"method": "hybrid_rerank", **KIWI, **HYB, **RR, "contextual_prefix": True}, {}),
    # --- x11: translation cost ---
    "x11_bm25_en_skip": ("English-pivot BM25, English-looking queries are not translated", {"method": "bm25", **EN, "translate_skip_english": True}, {}),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]            # 이름을 주면 그 설정만 쓴다 (예: 모델 이름이 확인된 뒤 추가하는 설정)
    for name, (desc, retrieval, chunking) in EXPERIMENTS.items():
        if only and name not in only:
            continue
        cfg = {"exp_id": f"v2_{name}", "stage": "v2", "description": desc + " [eval: queries_v2, 90 questions]",
               "eval_path": "eval/queries_v2.jsonl", "retrieval": {"top_k": 10, **retrieval}}
        if chunking:
            cfg["chunking"] = chunking
        (OUT / f"v2_{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(only) or len(EXPERIMENTS)} configs to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
