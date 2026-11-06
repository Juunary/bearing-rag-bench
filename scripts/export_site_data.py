"""Export what happens inside the pipeline for every published question -> docs/data/*.json (GitHub Pages).

[EN]
- Role: the site (docs/) shows, for one question at a time, each stage of the serving pipeline with real data:
  input validation, query translation, English BM25 and dense candidates, RRF fusion, reranker order, the
  5 passages given to the generator, the stored answer with its citations, output validation and the grades.
- Sets: v2 (90 questions, Wikipedia corpus, retrieval v2_x2_rerank_en_text = the chat server's retrieval,
  answers v2g_ret_x2_rerank_en_text), pdf (48 questions, Wikipedia + PDF corpus, pdfth_x13_rrf_en_dense_en_rerank_en_text,
  answers pdfg_th_x13_rrf_en_dense_en_rerank_en_text) and user (10 questions the grader wrote, same retrieval,
  answers eval/human_round2/user_questions_answers.json) and service (50 practical questions answered by the current chat-server
  config configs/s7_pipeline_kb.json via scripts/answer_questions.py -> eval/service/s7_answers.json: when a question matched a
  knowledge-bundle page the record carries the match and the bundle pages instead of retrieval stages). Answers and grades are
  read from stored results, not regenerated.
- Retrieval is run again here (translations come from logs/translate_cache.sqlite, so no LLM is loaded) to record
  every stage; the final top 10 must equal the stored retrieval result of the same config, otherwise the export stops.
- Stage timings are measured in this run on this machine; translation and generation seconds are the stored
  original values (the cache keeps them).
- Output: docs/data/<set>.json (questions) and docs/data/chunks.json (texts of every chunk shown).
- Usage: uv run python scripts/export_site_data.py

[KO]
- 역할: 사이트(docs/)에서 질문 하나씩, 서비스 파이프라인의 각 단계를 실제 데이터로 보여준다: 입력 검증, 질의 번역, 영어
  BM25·dense 후보, RRF 융합, 리랭커 순서, 생성 모델에 넣은 5개 문단, 저장된 답변과 인용, 출력 검증, 채점.
- 세트: v2(90문항, 위키 코퍼스, 검색 v2_x2_rerank_en_text = 채팅 서버 검색, 답변 v2g_ret_x2_rerank_en_text), pdf(48문항,
  위키 + PDF 코퍼스, pdfth_x13_rrf_en_dense_en_rerank_en_text, 답변 pdfg_th_x13_rrf_en_dense_en_rerank_en_text), user(채점자가
  쓴 10문항, 같은 검색, 답변 eval/human_round2/user_questions_answers.json). 답변과 채점은 저장된 결과를 읽고 다시 만들지 않는다.
- 검색은 단계를 기록하려고 여기서 다시 돌린다(번역은 logs/translate_cache.sqlite에서 읽어 LLM을 올리지 않음). 최종 상위 10이
  같은 설정의 저장된 검색 결과와 다르면 멈춘다.
- 단계 시간은 이 실행에서 이 컴퓨터로 잰 값이고, 번역·생성 시간은 저장된 원래 값이다(캐시에 남아 있음).
- 출력: docs/data/<set>.json(질문), docs/data/chunks.json(화면에 나오는 청크 텍스트).
- 사용: uv run python scripts/export_site_data.py
"""

from __future__ import annotations

import ast
import gc
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.generation import PROMPTS, parse_answer  # noqa: E402
from ragbench.ingest import REPO, load_corpus  # noqa: E402
from ragbench.retrieval.factory import _english_chunks_path, build_retriever  # noqa: E402
from ragbench.validation import Verdict, validate_answer, validate_question  # noqa: E402

RES = REPO / "experiments" / "results"
OUT = REPO / "docs" / "data"
SHOW = 10                                   # 단계마다 화면에 보여 줄 순위 수
SETS = [
    {"set": "v2", "config": "configs/v2/v2_x2_rerank_en_text.json", "eval": "eval/queries_v2.jsonl",
     "answers": "v2g_ret_x2_rerank_en_text"},
    {"set": "pdf", "config": "configs/pdf/pdfth_x13_rrf_en_dense_en_rerank_en_text.json", "eval": "eval/queries_pdf.jsonl",
     "answers": "pdfg_th_x13_rrf_en_dense_en_rerank_en_text"},
    {"set": "user", "config": "configs/pdf/pdfth_x13_rrf_en_dense_en_rerank_en_text.json", "eval": None, "answers": None},
    {"set": "service", "config": "configs/s7_pipeline_kb.json", "eval": None, "answers": None, "served": "eval/service/s7_answers.json"},
]
PART_LABEL = {"bm25": "BM25 (English)", "dense": "dense (bge-m3)"}


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def ids(x) -> list[str]:
    # 검색 결과 파일은 순위 목록을 문자열로 저장한 경우가 있다
    return ast.literal_eval(x) if isinstance(x, str) else list(x)


def human_grades() -> dict[tuple[str, str], dict]:
    """(qid, answer text) -> human labels of round 2 part B (the same answer may stand for several conditions)."""
    s = json.loads((REPO / "eval" / "human_round2" / "sample.json").read_text(encoding="utf-8"))
    lab = json.loads((REPO / "eval" / "human_round2" / "labels.json").read_text(encoding="utf-8"))["labels"]
    return {(b["qid"], b["answer"]): {k: v for k, v in lab[b["item"]].items()} for b in s["part_b"]}


def stages(retriever, cfg: ExperimentConfig, question: str) -> dict:
    """Run every stage of the retriever once and keep ranks, scores and wall time."""
    r = cfg.retrieval
    out: dict = {}
    t = time.perf_counter()
    verdict, cleaned = validate_question(question)
    out["input"] = {"ok": verdict.ok, "reason": verdict.reason, "ms": (time.perf_counter() - t) * 1000}
    tr = retriever.query_translator.translate(cleaned, "query")
    out["translation"] = {"text": tr["text"], "seconds": tr["seconds"], "from_cache": tr.get("from_cache", False)}
    parts = []
    for p in retriever.base.retrievers:
        kind = "bm25" if "bm25" in p.name else "dense"
        t = time.perf_counter()
        hits = p.search(cleaned, r.fusion_candidates)
        ms = (time.perf_counter() - t) * 1000
        # 영어 피벗 dense는 번역 청크를, 원문 dense는 원문 청크를 임베딩한다
        english = kind == "bm25" or p.name.endswith("_en")
        parts.append({"kind": kind, "label": PART_LABEL[kind], "english": english, "name": p.name, "ms": ms,
                      "hits": [[cid, round(s, 4)] for cid, s in hits]})
    out["parts"] = parts
    # RRF 융합만의 시간: 위에서 받은 후보로 같은 식을 계산하고, 검색기의 RRF 결과와 같은지 확인한다
    t = time.perf_counter()
    score: dict[str, float] = {}
    for p in parts:
        for rank, (cid, _) in enumerate(p["hits"], start=1):
            score[cid] = score.get(cid, 0.0) + 1.0 / (r.rrf_k + rank)
    local = sorted(score.items(), key=lambda x: -x[1])[:r.rerank_top_n]
    rrf_ms = (time.perf_counter() - t) * 1000
    fused = retriever.base.search(cleaned, r.rerank_top_n)
    if [c for c, _ in local] != [c for c, _ in fused]:
        raise SystemExit(f"RRF recomputation differs for {question!r}")
    out["rrf"] = {"ms": rrf_ms, "k": r.rrf_k,
                  "hits": [[cid, round(s, 5), retriever.base.last_provenance[cid]] for cid, s in fused]}
    final = retriever.search(cleaned, r.rerank_top_n)
    out["rerank"] = {"ms": retriever.last_rerank_seconds * 1000, "top_n": r.rerank_top_n,
                     "hits": [[cid, round(s, 4)] for cid, s in final]}
    return out


def trim(st: dict, gold: set[str]) -> dict:
    """Keep the top SHOW of every list (RRF: the whole reranker pool, to show rank changes) plus the rank of every gold chunk."""
    def rank_of(hits):
        pos = {h[0]: i for i, h in enumerate(hits, start=1)}
        return {g: pos.get(g) for g in sorted(gold)}
    for p in st["parts"]:
        p["n"] = len(p["hits"])
        p["gold_rank"] = rank_of(p["hits"])
        p["hits"] = p["hits"][:SHOW]
    for key in ("rrf", "rerank"):
        st[key]["n"] = len(st[key]["hits"])
        st[key]["gold_rank"] = rank_of(st[key]["hits"])
    st["rerank"]["hits"] = st["rerank"]["hits"][:SHOW]
    return st


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    human = human_grades()
    users = json.loads((REPO / "eval" / "human_round2" / "labels.json").read_text(encoding="utf-8"))["user_questions"]
    user_ans = json.loads((REPO / "eval" / "human_round2" / "user_questions_answers.json").read_text(encoding="utf-8"))
    chunk_text: dict[str, dict] = {}
    meta = {"prompts": PROMPTS, "sets": {}}
    built: dict[str, tuple] = {}
    for spec in SETS:
        cfg = ExperimentConfig.load(REPO / spec["config"])
        set_seed(cfg.seed)
        if spec["config"] not in built:
            built.clear()
            gc.collect()
            chunks = load_chunks(cfg.chunking)
            retriever = build_retriever(cfg)
            retriever.index(chunks)
            with open(_english_chunks_path(cfg), encoding="utf-8") as f:
                en = {c["chunk_id"]: c for c in map(json.loads, filter(str.strip, f))}
            titles = {d["doc_id"]: d["title"] for d in load_corpus(cfg.chunking.corpus)}
            built[spec["config"]] = (chunks, retriever, en, titles)
        chunks, retriever, en, titles = built[spec["config"]]
        by_id = {c["chunk_id"]: c for c in chunks}

        if spec["set"] == "service":
            # 서비스 설정으로 답한 질문: 경로 kb면 번들 매칭·페이지를, rag면 검색 단계를 기록한다
            from ragbench.kb import KnowledgeBundle
            served = json.loads((REPO / spec["served"]).read_text(encoding="utf-8"))
            kb = KnowledgeBundle(REPO / cfg.generation.kb_bundle, embedder=None, context=cfg.generation.kb_context)
            page_of = {p["chunk_id"]: c for c, p in zip(kb.pages, kb.passages.values())}
            items = [{"qid": r["qid"], "question": r["question"], "q_lang": "ko", "group": r.get("scope", "in"), "gold": {},
                      "answer": r["answer"], "raw_answer": r.get("raw_answer"), "context_ids": r["context_ids"], "blocked": r["blocked"], "reason": r["reason"],
                      "path": r["path"], "kb_match": r["kb_match"], "stored_top": r["context_ids"] if r["path"] == "rag" else [],
                      "gen": {"seconds": r["timings_ms"].get("generate", 0) / 1000, "prompt_tokens": r["prompt_tokens"], "completion_tokens": r["completion_tokens"]}}
                     for r in served["rows"]]
            prompt, judged = served.get("prompt_version", cfg.generation.prompt_version), None
            for cid, c in page_of.items():
                chunk_text[cid] = {"doc": f"kb_{c.id}", "title": c.title, "lang": "ko", "text": c.description}
        elif spec["set"] == "user":
            rows = {r["qid"]: r for r in user_ans["rows"]}
            items = [{"qid": u["qid"], "question": u["question"], "q_lang": "ko", "group": "ko", "gold": {},
                      "answer": rows[u["qid"]]["answer"], "context_ids": rows[u["qid"]]["best_top5"],
                      "human": {k: u[k] for k in ("correctness", "refusal", "note") if k in u},
                      "blocked": rows[u["qid"]]["blocked"], "reason": rows[u["qid"]]["reason"],
                      "stored_top": rows[u["qid"]]["best_top5"]} for u in users]
            prompt, judged = user_ans["prompt_version"], None
        else:
            queries = {q["qid"]: q for q in load_queries(REPO / spec["eval"])}
            gen = load(spec["answers"])
            jq = {q["qid"]: q for q in load(f"s3_judge_{spec['answers']}")["per_query"]}
            jg = {q["qid"]: q for q in load(f"s3_judge_granite_{spec['answers']}")["per_query"]}
            stored = {q["qid"]: ids(q["ranked"]) for q in load(cfg.exp_id)["per_query"]}
            items = []
            for g in gen["per_query"]:
                q = queries[g["qid"]]
                items.append({"qid": g["qid"], "question": q["question"], "q_lang": q["q_lang"], "group": g["group"],
                              "gold": g["gold"], "answer": g["answer"], "context_ids": g["context_ids"],
                              "gen": {"seconds": g["seconds"], "prompt_tokens": g["prompt_tokens"],
                                      "completion_tokens": g["completion_tokens"]},
                              "judges": {"qwen": jq[g["qid"]]["labels"], "granite": jg[g["qid"]]["labels"],
                                         "outcome": jq[g["qid"]]["outcome"]},
                              "human": human.get((g["qid"], g["answer"])),
                              "evidence_kind": q.get("evidence_kind"), "stored_top": stored[g["qid"]]})
            prompt, judged = gen["config"]["generation"]["prompt_version"], True

        # 첫 질의의 모델 준비 시간이 단계 시간에 섞이지 않게 한 번 먼저 돌린다 (번역이 캐시에 있는 질문이라 LLM을 올리지 않음)
        retriever.search(items[0]["question"], cfg.retrieval.top_k)
        out = []
        for it in items:
            if it.get("path") == "kb":
                # 번들 경로: 검색 단계가 없다. 매칭 결과와 컨텍스트 페이지만 기록한다
                st = None
            else:
                st = trim(stages(retriever, cfg, it["question"]), set(it["gold"]))
                served_top = [h[0] for h in st["rerank"]["hits"]]
                # 다시 돌린 검색이 저장된 결과와 같아야 화면의 단계 데이터가 그 답변의 실제 경로다
                k = len(it["stored_top"])
                if served_top[:k] != it["stored_top"][:k] or it["context_ids"] != served_top[:len(it["context_ids"])]:
                    raise SystemExit(f"{spec['set']} {it['qid']}: rerun {served_top[:k]} != stored {it['stored_top'][:k]}")
            parsed = parse_answer(it["answer"], it["context_ids"], set(it["gold"]))
            if "blocked" in it:
                # 서비스 경로의 답변: 저장된 것은 사용자에게 보인 문구(차단되면 고정 문구)라 저장된 판정을 그대로 쓴다
                v = Verdict(not it["blocked"], it["reason"])
                if it["blocked"]:
                    parsed = {**parsed, "refused": it["reason"] in ("refusal_sentinel", "refusal_text"), "cited": []}
            else:
                v = validate_answer(it["answer"], it["context_ids"])
            rec = {k2: it[k2] for k2 in ("qid", "question", "q_lang", "group", "gold", "answer", "context_ids", "raw_answer", "path") if k2 in it}
            rec.update({"stages": st, "output": {"ok": v.ok, "reason": v.reason, "cited": sorted(set(parsed["cited"])),
                                                 "refused": parsed["refused"]}})
            if spec["set"] == "service":
                mt = it["kb_match"] or {"alias": {}, "dense": [], "ids": [], "related": [], "canonical_names": []}
                pages = [{"id": page_of[c].id, "cid": c, "title": page_of[c].title} for c in it["context_ids"] if c in page_of] if it["path"] == "kb" \
                    else [{"id": c.id, "cid": p["chunk_id"], "title": c.title} for c, p in zip(kb.pages, kb.passages.values())]
                rec["kb"] = {"match": {k3: mt.get(k3) for k3 in ("alias", "dense", "ids", "related", "canonical_names")}, "passages": pages,
                             "verified": kb.verified, "dense_best": it.get("dense_best")}
            for k2 in ("gen", "judges", "human", "evidence_kind"):
                if it.get(k2) is not None:
                    rec[k2] = it[k2]
            out.append(rec)
            shown = set(it["gold"]) | set(it["context_ids"])
            if st is not None:
                shown |= {h[0] for p in st["parts"] for h in p["hits"]} | {h[0] for h in st["rrf"]["hits"][:SHOW]} | {h[0] for h in st["rerank"]["hits"]}
            for cid in shown:
                if cid not in chunk_text and cid in by_id:
                    c = by_id[cid]
                    e = en[cid]
                    chunk_text[cid] = {"doc": c["doc_id"], "title": titles[c["doc_id"]], "lang": c["lang"], "text": c["text"],
                                       **({"en": e["text"]} if e.get("translated") else {})}
            print(spec["set"], it["qid"], "ok")
        meta["sets"][spec["set"]] = {"config": cfg.exp_id, "n_chunks": len(chunks), "corpus": cfg.chunking.corpus,
                                     "table_header": cfg.chunking.table_header, "answers": spec["answers"] or spec.get("served", "user_questions_answers"),
                                     "prompt": prompt, "judged": bool(judged), "n": len(out),
                                     "retrieval": {"fusion_candidates": cfg.retrieval.fusion_candidates, "rrf_k": cfg.retrieval.rrf_k,
                                                   "rerank_top_n": cfg.retrieval.rerank_top_n, "context_k": 5,
                                                   "rerank_model": cfg.retrieval.rerank_model,
                                                   "embedding_model": cfg.retrieval.embedding_model}}
        (OUT / f"{spec['set']}.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "chunks.json").write_text(json.dumps(chunk_text, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print({s: m["n"] for s, m in meta["sets"].items()}, "chunks", len(chunk_text))


if __name__ == "__main__":
    main()
