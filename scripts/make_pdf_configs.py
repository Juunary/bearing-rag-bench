"""Write configs/pdf/*.json: retrieval experiments on the Wikipedia + PDF corpus.

[EN]
- Role: the same retrieval settings as the v2 round (copied from scripts/make_v2_configs.py, so a setting cannot
  drift), run on chunking.corpus = "wiki_pdf" (903 chunks) with two question sets:
  - pdf_<name>: eval/queries_pdf.jsonl (48 questions whose primary evidence is in a PDF document);
  - v2pdf_<name>: eval/queries_v2.jsonl (90 Wikipedia questions) on the larger corpus, i.e. the effect of 557
    PDF chunks as distractors (v2 gold has no PDF chunk, so a relevant PDF chunk counts as a miss);
  - pdfth_<name>: the PDF questions on chunks that repeat the table caption and header row (chunking.table_header).
  - pdfth_c_<mode>_x13_... and v2pdf_c_<mode>_x13_...: the best setting plus the concept bundle (data/concepts) in each
    concept_mode (pool / pool_query / rrf_query), to compare against pdfth_x13_... and v2pdf_x13_....
- Usage: uv run python scripts/make_pdf_configs.py; uv run python experiments/run_suite.py --glob 'configs/pdf/*.json'

[KO]
- 역할: v2 라운드와 같은 검색 설정(scripts/make_v2_configs.py에서 그대로 가져와 설정이 어긋나지 않게 함)을
  chunking.corpus = "wiki_pdf"(청크 903개)에서 두 질문셋으로 돌린다.
  - pdf_<이름>: eval/queries_pdf.jsonl(주 근거가 PDF 문서인 질문 48개)
  - v2pdf_<이름>: eval/queries_v2.jsonl(위키 질문 90개)을 큰 코퍼스에서. PDF 청크 557개가 방해 문서로 주는 영향
    (v2 gold에는 PDF 청크가 없어서 관련 있는 PDF 청크도 오답으로 센다).
  - pdfth_<이름>: 표 캡션·머리글 행을 반복한 청크(chunking.table_header)에서 PDF 질문.
  - pdfth_c_<mode>_x13_..., v2pdf_c_<mode>_x13_...: 최고 설정 + 개념 묶음(data/concepts)을 concept_mode(pool / pool_query /
    rrf_query)마다 하나씩. pdfth_x13_..., v2pdf_x13_...과 비교한다.
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
# 개념 경유 검색: 최고 설정(x13)에 개념 묶음을 세 방식으로 붙인다. PDF 질문은 표 머리글 청크(pdfth), v2 질문은 v2pdf 세트와 짝을 이룬다
BEST = "x13_rrf_en_dense_en_rerank_en_text"
CONCEPT = {f"c_{mode}_{BEST}": (f"{EXPERIMENTS[BEST][0]} + concept bundle ({mode})",
                                {**EXPERIMENTS[BEST][1], "concept_bundle": "data/concepts", "concept_mode": mode}, EXPERIMENTS[BEST][2])
           for mode in ("pool", "pool_query", "rrf_query")}
# pool 후보 수 ablation: 10(기본) 대신 30
CONCEPT[f"c_pool30_{BEST}"] = (f"{EXPERIMENTS[BEST][0]} + concept bundle (pool, 30 candidates)",
                               {**EXPERIMENTS[BEST][1], "concept_bundle": "data/concepts", "concept_mode": "pool", "concept_pool_n": 30}, EXPERIMENTS[BEST][2])
CONCEPT_SETS = ("pdfth", "v2pdf")


def write(prefix: str, name: str, spec: tuple) -> None:
    eval_path, label, chunk_extra = SETS[prefix]
    desc, retrieval, chunking = spec
    cfg = {"exp_id": f"{prefix}_{name}", "stage": prefix, "description": f"{desc} [corpus: wiki + pdf, eval: {label}]",
           "eval_path": eval_path, "retrieval": {"top_k": 10, **retrieval}, "chunking": {**chunking, "corpus": "wiki_pdf", **chunk_extra}}
    (OUT / f"{prefix}_{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for prefix in SETS:
        for name in NAMES:
            write(prefix, name, EXPERIMENTS[name])
            n += 1
    for prefix in CONCEPT_SETS:
        for name, spec in CONCEPT.items():
            write(prefix, name, spec)
            n += 1
    print(f"wrote {n} configs to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
