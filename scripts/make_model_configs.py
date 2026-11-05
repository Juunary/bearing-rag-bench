"""Write configs/modelswap/*.json: the best pipelines with the embedding model or the reranker swapped for a 2026 model.

[EN]
- Role: one factor at a time. For two question sets the best retrieval setting is kept and exactly one model is
  replaced: the dense leg's embedding model (bge-m3 -> Qwen3-Embedding-0.6B / EmbeddingGemma 2) or the reranker
  (bge-reranker-v2-m3 -> Qwen3-Reranker-0.6B / 4B). Prompts, pooling and dtype follow each model card.
  - v2m_<variant>: eval/queries_v2.jsonl (90 questions), Wikipedia corpus, base x2_rerank_en_text
    (English BM25 + original-text dense, reranker on English text); baseline result v2_x2_rerank_en_text.
  - pdfm_<variant>: eval/queries_pdf.jsonl (48 questions), Wikipedia + PDF corpus with table headers, base
    x13_rrf_en_dense_en_rerank_en_text (English BM25 + English dense, reranker on English text); baseline pdfth_x13_....
- Usage: uv run python scripts/make_model_configs.py; uv run python experiments/run_suite.py --glob 'configs/modelswap/*.json'

[KO]
- 역할: 한 번에 요인 하나. 두 질문셋에서 최고 검색 설정을 그대로 두고 모델 하나만 바꾼다: dense 다리의 임베딩 모델(bge-m3 ->
  Qwen3-Embedding-0.6B / EmbeddingGemma 2) 또는 리랭커(bge-reranker-v2-m3 -> Qwen3-Reranker-0.6B / 4B). 프롬프트·풀링·dtype은
  모델 카드를 따른다.
  - v2m_<변형>: eval/queries_v2.jsonl(90문항), 위키 코퍼스, 기준 x2_rerank_en_text; 기준선 결과 v2_x2_rerank_en_text.
  - pdfm_<변형>: eval/queries_pdf.jsonl(48문항), 위키 + PDF 표 머리글 코퍼스, 기준 x13_rrf_en_dense_en_rerank_en_text; 기준선 pdfth_x13_....
- 사용: uv run python scripts/make_model_configs.py; uv run python experiments/run_suite.py --glob 'configs/modelswap/*.json'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from make_v2_configs import EXPERIMENTS  # noqa: E402

OUT = REPO / "configs" / "modelswap"
QWEN_EMB_PREFIX = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:"
VARIANTS = {
    "emb_qwen3_0.6b": ("embedding Qwen3-Embedding-0.6B (last-token pooling, instruction prefix, bf16)",
                       {"embedding_model": "Qwen/Qwen3-Embedding-0.6B", "embedding_pooling": "last", "embedding_query_prefix": QWEN_EMB_PREFIX,
                        "embedding_dtype": "bf16"}),
    "emb_gemma2": ("embedding EmbeddingGemma 2 (mean pooling, task prefixes, bf16)",
                   {"embedding_model": "google/embeddinggemma-2", "embedding_pooling": "mean", "embedding_query_prefix": "task: search result | query: ",
                    "embedding_doc_prefix": "title: none | text: ", "embedding_dtype": "bf16"}),
    "rr_qwen3_0.6b": ("reranker Qwen3-Reranker-0.6B (yes/no logits, bf16, cuda:1)",
                      {"rerank_model": "Qwen/Qwen3-Reranker-0.6B", "rerank_kind": "qwen3", "rerank_device": "cuda:1"}),
    "rr_qwen3_4b": ("reranker Qwen3-Reranker-4B (yes/no logits, bf16, cuda:1)",
                    {"rerank_model": "Qwen/Qwen3-Reranker-4B", "rerank_kind": "qwen3", "rerank_device": "cuda:1"}),
}
SETS = {"v2m": ("x2_rerank_en_text", "eval/queries_v2.jsonl", "90 v2 questions", {"corpus": "wiki"}),
        "pdfm": ("x13_rrf_en_dense_en_rerank_en_text", "eval/queries_pdf.jsonl", "48 PDF questions, table headers repeated",
                 {"corpus": "wiki_pdf", "table_header": True})}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for prefix, (base, eval_path, label, chunking) in SETS.items():
        desc, retrieval, base_chunking = EXPERIMENTS[base]
        for name, (vdesc, override) in VARIANTS.items():
            cfg = {"exp_id": f"{prefix}_{name}", "stage": prefix, "description": f"{desc}; {vdesc} [eval: {label}]",
                   "eval_path": eval_path, "retrieval": {"top_k": 10, **retrieval, **override}, "chunking": {**base_chunking, **chunking}}
            (OUT / f"{prefix}_{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            n += 1
    print(f"wrote {n} configs to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
