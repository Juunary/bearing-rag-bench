"""Build the stage 4 training set: questions from chunks, retrieved contexts, filtered self-distilled answers.

[EN]
- Role: produce data/sft/train.jsonl and val.jsonl (prompt messages + target answer) that teach
  citation completeness, plus data/sft/stats.json with the yield of every filter.
- Pipeline (each phase writes a resumable file under data/sft/_work/):
  1. sources: chunks that are not gold chunks of the evaluation set, not junk; ko chunks are kept
     (up to 40) because the corpus has few; question language cycles ko/en/de, so most examples are
     cross-language.
  2. questions: the base model (Qwen3-4B-Instruct-2507) writes one question per chunk (greedy).
  3. question filter: script/language check, no reference to "the passage", cosine similarity to
     every evaluation question < 0.80 (bge-m3) and to earlier training questions < 0.92.
  4. retrieval: the same RRF + reranker pipeline as the evaluation (top-5). The source chunk must be
     among the five, so the target answer can cite it; other examples are dropped.
  5. answers: n=4 samples per prompt (temperature 0.7, top-p 0.9) with the evaluation prompt
     cite_v1; the first sample that passes the answer filter (sftdata.answer_ok) is the target.
  6. split: 90% train / 10% validation (validation loss only monitors training; the 45 evaluation
     questions are the real test).
- Separation from the evaluation set: no evaluation gold chunk is a source, and no training
  question is close to an evaluation question. Training prompts may still contain an evaluation
  gold chunk as one of the five retrieved passages (it is context, never the cited target).
- Usage: uv run python experiments/build_sft_data.py [--n-sources 240]

[KO]
- 역할: 인용 완결성을 가르치는 data/sft/train.jsonl, val.jsonl(프롬프트 메시지 + 목표 답변)과 필터별
  통과량을 담은 data/sft/stats.json을 만든다.
- 파이프라인(각 단계는 data/sft/_work/ 아래에 이어서 실행 가능한 파일을 쓴다):
  1. 출처: 평가셋 정답 청크가 아니고 잡음이 아닌 청크. 코퍼스에 적은 ko 청크는 최대 40개 유지. 질문 언어는
     ko/en/de를 순환해 대부분 교차 언어 예시가 된다.
  2. 질문: 기반 모델(Qwen3-4B-Instruct-2507)이 청크마다 질문 하나를 쓴다(greedy).
  3. 질문 필터: 문자·언어 검사, "본문" 지시 금지, 모든 평가 질문과 코사인 유사도 < 0.80(bge-m3), 앞선 학습
     질문과 < 0.92.
  4. 검색: 평가와 같은 RRF + 리랭커 파이프라인(상위 5). 출처 청크가 5개 안에 있어야 목표 답변이 그것을
     인용할 수 있으므로 없는 예시는 버린다.
  5. 답변: 평가 프롬프트 cite_v1로 프롬프트당 4개 샘플(온도 0.7, top-p 0.9). 답변 필터(sftdata.answer_ok)를
     처음 통과하는 샘플이 목표다.
  6. 분할: 학습 90% / 검증 10%(검증 손실은 학습 모니터링용이고 진짜 시험은 평가 질문 45개).
- 평가셋과의 분리: 평가 정답 청크는 출처가 되지 않고, 평가 질문과 가까운 학습 질문은 없다. 다만 학습 프롬프트에는
  검색된 5개 문단의 하나로 평가 정답 청크가 들어갈 수 있다(컨텍스트일 뿐 인용 대상이 아니다).
- 사용: uv run python experiments/build_sft_data.py [--n-sources 240]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, environment_snapshot, set_seed  # noqa: E402
from ragbench.embedding import Embedder  # noqa: E402
from ragbench.evalset import load_queries, map_gold_to_chunks  # noqa: E402
from ragbench.generation import Generator, build_messages  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402
from ragbench.retrieval.factory import build_retriever  # noqa: E402
from ragbench.sftdata import is_junk_chunk, parse_question, pick_answer, question_messages, question_ok  # noqa: E402
from ragbench.generation import parse_answer  # noqa: E402

OUT = REPO / "data" / "sft"
WORK = OUT / "_work"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if path.exists() else []


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sources", type=int, default=240)
    ap.add_argument("--samples", type=int, default=4)
    ap.add_argument("--max-ko", type=int, default=40)
    ap.add_argument("--sim-eval", type=float, default=0.80)
    ap.add_argument("--sim-train", type=float, default=0.92)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    set_seed(args.seed)
    env = environment_snapshot()      # taken before any file is written, so the commit is not marked dirty by our own outputs

    cfg = ExperimentConfig.load(REPO / "configs" / "s35_pipeline.json")
    docs = {d["doc_id"]: d for d in load_docs()}
    chunks = load_chunks(cfg.chunking)
    by_id = {c["chunk_id"]: c for c in chunks}
    eval_q = load_queries(REPO / cfg.eval_path)
    eval_gold = set()
    for q in eval_q:
        eval_gold |= set(map_gold_to_chunks(q["gold"], docs, chunks, cfg.anchor_min_overlap))

    # 1. sources
    rng = random.Random(args.seed)
    cands = [c for c in chunks if c["chunk_id"] not in eval_gold and not is_junk_chunk(c)]
    ko = [c for c in cands if c["lang"] == "ko"]
    rest = [c for c in cands if c["lang"] != "ko"]
    rng.shuffle(ko); rng.shuffle(rest)
    sources = ko[: args.max_ko] + rest[: max(0, args.n_sources - min(len(ko), args.max_ko))]
    rng.shuffle(sources)
    langs = ["ko", "en", "de"]
    funnel = {"chunks_total": len(chunks), "eval_gold_chunks_excluded": len(eval_gold), "source_candidates": len(cands), "sources_selected": len(sources)}

    # 2. questions (LLM on cuda:1; retrieval models stay on cuda:0)
    gen = Generator(cfg.generation.model, device="cuda:1")
    qpath = WORK / "questions.jsonl"
    done = {r["source_id"]: r for r in read_jsonl(qpath)}
    rows = []
    for i, c in enumerate(sources):
        qlang = langs[i % 3]
        if c["chunk_id"] in done:
            rows.append(done[c["chunk_id"]]); continue
        text = gen.generate(question_messages(c["text"], qlang), max_new_tokens=80)["text"]
        rows.append({"source_id": c["chunk_id"], "chunk_lang": c["lang"], "q_lang": qlang, "raw": text, "question": parse_question(text)})
        if (i + 1) % 20 == 0:
            write_jsonl(qpath, rows); print(f"questions {i + 1}/{len(sources)}", flush=True)
    write_jsonl(qpath, rows)

    # 3. question filters
    embedder = Embedder("BAAI/bge-m3")
    ev = embedder.encode([q["question"] for q in eval_q])
    kept, reasons, embs = [], Counter(), []
    for r in rows:
        ok, why = question_ok(r["question"], r["q_lang"])
        if not ok:
            reasons[why] += 1; continue
        v = embedder.encode([r["question"]])[0]
        if float((ev @ v).max()) >= args.sim_eval:
            reasons["too_similar_to_eval"] += 1; continue
        if embs and float((np.stack(embs) @ v).max()) >= args.sim_train:
            reasons["duplicate_training_question"] += 1; continue
        embs.append(v); kept.append(r)
    funnel.update(questions_generated=len(rows), questions_rejected=dict(reasons), questions_kept=len(kept))
    print("after question filters:", len(kept), dict(reasons), flush=True)

    # 4. retrieval
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    withctx = []
    for r in kept:
        hits = retriever.search(r["question"], cfg.generation.context_k)
        ids = [h[0] for h in hits]
        if r["source_id"] in ids:
            withctx.append({**r, "context_ids": ids})
    funnel["source_in_top5"] = len(withctx)
    print("source chunk in top-5:", len(withctx), "of", len(kept), flush=True)

    # 5. answers
    apath = WORK / "answers.jsonl"
    cached = {r["source_id"]: r for r in read_jsonl(apath)}
    examples, raw_cov, chosen_cov, any_pass = [], [], [], 0
    results = []
    for i, r in enumerate(withctx):
        if r["source_id"] in cached:
            res = cached[r["source_id"]]
        else:
            messages = build_messages("cite_v1", r["question"], [by_id[x] for x in r["context_ids"]])
            cands_ = gen.sample(messages, n=args.samples, max_new_tokens=cfg.generation.max_new_tokens, seed=args.seed + i)
            res = {**r, "messages": messages, "candidates": cands_}
            results.append(res)
            if len(results) % 10 == 0:
                write_jsonl(apath, list(cached.values()) + results); print(f"answers {i + 1}/{len(withctx)}", flush=True)
        answer = pick_answer(res["candidates"], res["context_ids"], res["source_id"], res["q_lang"])
        raw_cov += [parse_answer(a, res["context_ids"], {res["source_id"]})["sentence_coverage"] for a in res["candidates"]]
        if answer is not None:
            any_pass += 1
            chosen_cov.append(1.0)
            examples.append({"id": f"sft-{len(examples):04d}", "source_id": res["source_id"], "q_lang": res["q_lang"], "chunk_lang": res["chunk_lang"],
                             "question": res["question"], "context_ids": res["context_ids"], "messages": res["messages"], "answer": answer})
    write_jsonl(apath, list(cached.values()) + results)
    funnel.update(questions_with_a_passing_sample=any_pass, mean_sentence_coverage_of_all_raw_samples=round(float(np.mean(raw_cov)), 3),
                  share_of_prompts_where_a_sample_passes=round(any_pass / max(1, len(withctx)), 3))

    # 6. split
    rng.shuffle(examples)
    n_val = max(12, len(examples) // 10)
    val, train = examples[:n_val], examples[n_val:]
    write_jsonl(OUT / "train.jsonl", train)
    write_jsonl(OUT / "val.jsonl", val)
    stats = {"funnel": funnel, "train": len(train), "val": len(val),
             "train_by_q_lang": dict(Counter(e["q_lang"] for e in train)), "train_by_chunk_lang": dict(Counter(e["chunk_lang"] for e in train)),
             "train_cross_language_share": round(sum(e["q_lang"] != e["chunk_lang"] for e in train) / max(1, len(train)), 3),
             "base_model": cfg.generation.model, "base_model_revision": gen.revision, "seed": args.seed, "sampling": {"n": args.samples, "temperature": 0.7, "top_p": 0.9},
             "environment": env}
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "environment"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
