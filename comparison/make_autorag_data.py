"""Write the AutoRAG inputs (corpus.parquet, qa.parquet) from the shared corpus and questions.

[EN]
- corpus: doc_id = our chunk id, contents = chunk text, metadata with a modification time (some AutoRAG modules read it).
- qa: qid, query, retrieval_gt = one group per gold chunk (so AutoRAG's own metrics count each gold chunk),
  generation_gt = the primary anchor sentence (AutoRAG needs the column; it is not used for scoring here).
- Usage: uv run python make_autorag_data.py

[KO]
- corpus: doc_id = 우리 청크 ID, contents = 청크 본문, metadata에 수정 시각(일부 AutoRAG 모듈이 읽는다).
- qa: qid, query, retrieval_gt = gold 청크마다 한 그룹(AutoRAG 자체 지표가 gold 청크를 하나씩 센다),
  generation_gt = 주 근거 문장(AutoRAG가 요구하는 열이며 여기서는 채점에 쓰지 않는다).
- 사용: uv run python make_autorag_data.py
"""

import datetime

import pandas as pd

from cmp_common import DATA, load_corpus, load_qa

now = datetime.datetime(2026, 10, 27)
corpus = pd.DataFrame([{"doc_id": c["id"], "contents": c["text"], "path": c["doc_id"], "start_end_idx": (0, len(c["text"])),
                        "metadata": {"last_modified_datetime": now, "lang": c["lang"], "source": c["doc_id"]}} for c in load_corpus()])
qa = pd.DataFrame([{"qid": q["qid"], "query": q["question"], "retrieval_gt": [[cid] for cid in q["gold"]], "generation_gt": [q["anchor"]]} for q in load_qa()])
(DATA / "autorag").mkdir(exist_ok=True)
corpus.to_parquet(DATA / "autorag" / "corpus.parquet")
qa.to_parquet(DATA / "autorag" / "qa.parquet")
print(len(corpus), "corpus rows;", len(qa), "qa rows")
