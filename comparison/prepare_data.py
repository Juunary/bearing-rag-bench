"""Write the shared corpus and questions for the framework comparison (run with the main repository environment).

[EN]
- Output: comparison/data/corpus.jsonl (our 346 chunks: id, text, doc_id, lang) and comparison/data/qa.jsonl
  (the 90 questions with the gold already mapped to chunk ids and grades, plus the question language, type
  and primary-evidence document used for the cluster bootstrap).
- Why our chunks: every framework retrieves from the same 346 passages, so the comparison measures the
  retrieval pipelines, not different chunk boundaries (chunk size barely mattered in our own experiments).
  The frameworks' default chunkers are therefore NOT part of this comparison.
- Usage (from the repository root): uv run python comparison/prepare_data.py

[KO]
- 출력: comparison/data/corpus.jsonl(우리 청크 346개: id, 본문, doc_id, lang)과 comparison/data/qa.jsonl
  (90문항 + 청크 ID와 등급으로 매핑해 둔 gold, 질문 언어, 유형, 군집 부트스트랩에 쓰는 주 근거 문서).
- 우리 청크를 쓰는 이유: 모든 프레임워크가 같은 346개 문단에서 검색하므로 청크 경계가 아니라 검색 파이프라인의
  차이를 잰다(우리 실험에서 청크 크기는 거의 영향이 없었다). 따라서 프레임워크의 기본 청커는 비교 대상이 아니다.
- 사용(저장소 루트에서): uv run python comparison/prepare_data.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks, primary_group  # noqa: E402
from ragbench.ingest import load_docs  # noqa: E402

out = REPO / "comparison" / "data"
out.mkdir(parents=True, exist_ok=True)
docs = {d["doc_id"]: d for d in load_docs()}
chunks = load_chunks(ChunkingConfig())
with open(out / "corpus.jsonl", "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps({"id": c["chunk_id"], "text": c["text"], "doc_id": c["doc_id"], "lang": c["lang"]}, ensure_ascii=False) + "\n")
with open(out / "qa.jsonl", "w", encoding="utf-8") as f:
    for q in load_queries(REPO / "eval" / "queries_v2.jsonl"):
        gold = map_gold_to_chunks(q["gold"], docs, chunks, 0.5)
        f.write(json.dumps({"qid": q["qid"], "question": q["question"], "q_lang": q["q_lang"], "type": q["type"],
                            "group": primary_group(q), "primary_doc": q["gold"][0]["doc_id"], "gold": gold,
                            "anchor": q["gold"][0]["anchor"]}, ensure_ascii=False) + "\n")
print(len(chunks), "chunks;", sum(1 for _ in open(out / "qa.jsonl", encoding="utf-8")), "questions")
