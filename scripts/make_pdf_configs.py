"""Write configs/pdf/*.json: retrieval experiments on the Wikipedia + PDF corpus.

[EN]
- Role: the same retrieval settings as the v2 round (copied from scripts/make_v2_configs.py, so a setting cannot
  drift), run on chunking.corpus = "wiki_pdf" (903 chunks) with two question sets:
  - pdf_<name>: eval/queries_pdf.jsonl (48 questions whose primary evidence is in a PDF document);
  - v2pdf_<name>: eval/queries_v2.jsonl (90 Wikipedia questions) on the larger corpus, i.e. the effect of 557
    PDF chunks as distractors (v2 gold has no PDF chunk, so a relevant PDF chunk counts as a miss);
  - pdfth_<name>: the PDF questions on chunks that repeat the table caption and header row (chunking.table_header).
- Usage: uv run python scripts/make_pdf_configs.py; uv run python experiments/run_suite.py --glob 'configs/pdf/*.json'

[KO]
- 역할: v2 라운드와 같은 검색 설정(scripts/make_v2_configs.py에서 그대로 가져와 설정이 어긋나지 않게 함)을
  chunking.corpus = "wiki_pdf"(청크 903개)에서 두 질문셋으로 돌린다.
  - pdf_<이름>: eval/queries_pdf.jsonl(주 근거가 PDF 문서인 질문 48개)
  - v2pdf_<이름>: eval/queries_v2.jsonl(위키 질문 90개)을 큰 코퍼스에서. PDF 청크 557개가 방해 문서로 주는 영향
    (v2 gold에는 PDF 청크가 없어서 관련 있는 PDF 청크도 오답으로 센다).
  - pdfth_<이름>: 표 캡션·머리글 행을 반복한 청크(chunking.table_header)에서 PDF 질문.
- 사용: uv run python scripts/make_pdf_configs.py; uv run python experiments/run_suite.py --glob 'configs/pdf/*.json'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from make_v2_configs import EXPERIMENTS  # noqa: E402

OUT = REPO / "configs" / "pdf"
NAMES = ["b_bm25_kiwi", "b_dense", "b_rrf_rerank", "b_bm25_en", "b_rrf_en_rerank", "x2_rerank_en_text",
         "x12_dense_rerank", "x13_dense_en", "x13_dense_en_rerank_en_text", "x13_rrf_en_dense_en_rerank_en_text"]
SETS = {"pdf": ("eval/queries_pdf.jsonl", "48 PDF questions", {}), "v2pdf": ("eval/queries_v2.jsonl", "90 v2 questions", {}),
        # 표 머리글 반복 청크 (chunking.table_header): 위키 청크는 바뀌지 않으므로 PDF 질문에만 돌린다
        "pdfth": ("eval/queries_pdf.jsonl", "48 PDF questions, table headers repeated", {"table_header": True})}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for prefix, (eval_path, label, chunk_extra) in SETS.items():
        for name in NAMES:
            desc, retrieval, chunking = EXPERIMENTS[name]
            cfg = {"exp_id": f"{prefix}_{name}", "stage": prefix, "description": f"{desc} [corpus: wiki + pdf, eval: {label}]",
                   "eval_path": eval_path, "retrieval": {"top_k": 10, **retrieval}, "chunking": {**chunking, "corpus": "wiki_pdf", **chunk_extra}}
            (OUT / f"{prefix}_{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            n += 1
    print(f"wrote {n} configs to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
