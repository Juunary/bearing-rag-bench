"""Answer the questions a person wrote (human review round 2, part D) and pool candidate chunks for labelling.

[EN]
- Role: the person's own questions have no gold labels yet. This runs the serving setup on them and collects
  the chunks a person should label: the top 5 of the best PDF-corpus retrieval (English BM25 + English dense,
  reranker on English text, table headers repeated) and the top 5 of RRF + reranker on the same corpus.
- Answers: the base bf16 Qwen3-4B with the serving prompt cite_refuse_v1 (may refuse when the passages do not
  answer) on the top 5 chunks of the best retrieval. The query translator shares the generator's weights.
- Output: eval/human_round2/user_questions_answers.json
- Usage: uv run python scripts/answer_user_questions.py

[KO]
- 역할: 사람이 직접 쓴 질문은 아직 정답 라벨이 없다. 서비스 구성으로 답을 만들고, 사람이 라벨을 붙일 청크를 모은다:
  PDF 코퍼스 최고 검색(영어 BM25 + 영어 dense, 리랭커 영어 입력, 표 머리글 반복)의 상위 5와 같은 코퍼스 RRF + 리랭커의 상위 5.
- 답변: 기반 bf16 Qwen3-4B, 서비스 프롬프트 cite_refuse_v1(근거가 없으면 거절할 수 있음), 최고 검색 상위 5개 청크.
  질의 번역기는 생성 모델 가중치를 함께 쓴다.
- 출력: eval/human_round2/user_questions_answers.json
- 사용: uv run python scripts/answer_user_questions.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.generation import Generator  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever, share_translator_model  # noqa: E402

DIR = REPO / "eval" / "human_round2"
BEST = REPO / "configs" / "pdf" / "pdfth_x13_rrf_en_dense_en_rerank_en_text.json"
BASE = REPO / "configs" / "pdf" / "pdfth_b_rrf_rerank.json"
PROMPT, MODEL = "cite_refuse_v1", "Qwen/Qwen3-4B-Instruct-2507"


def main() -> None:
    questions = json.loads((DIR / "labels.json").read_text(encoding="utf-8"))["user_questions"]
    best, base = ExperimentConfig.load(BEST), ExperimentConfig.load(BASE)
    set_seed(best.seed)
    chunks = load_chunks(best.chunking)
    r_best, r_base = build_retriever(best), build_retriever(base)
    r_best.index(chunks)
    r_base.index(chunks)
    generator = Generator(MODEL, device="cuda:1")
    share_translator_model(r_best, generator)
    share_translator_model(r_base, generator)
    pipe = RAGPipeline(r_best, chunks, generator, LLMCache(REPO / "logs" / "human_round2_cache.sqlite"),
                       RequestLogger(REPO / "logs" / "human_round2_requests.jsonl"), prompt_version=PROMPT, context_k=5,
                       max_new_tokens=256, config_id=f"human_round2:{best.exp_id}")
    rows = []
    for q in questions:
        resp = pipe.answer(q["question"])
        base_ids = [cid for cid, _ in r_base.search(q["question"], 5)]
        pool = list(dict.fromkeys(list(resp.context_ids) + base_ids))
        rows.append({**q, "answer": resp.answer, "blocked": resp.blocked, "reason": resp.reason,
                     "best_top5": list(resp.context_ids), "baseline_top5": base_ids, "pool": pool})
        print(q["qid"], "blocked" if resp.blocked else "", len(pool), resp.answer[:120].replace("\n", " "))
    out = {"best_config": BEST.name, "baseline_config": BASE.name, "prompt_version": PROMPT, "model": MODEL,
           "chunk_set": "wiki_pdf_th", "rows": rows}
    (DIR / "user_questions_answers.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
