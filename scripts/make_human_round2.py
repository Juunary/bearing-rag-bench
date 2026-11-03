"""Draw the second human review sample (questions, answers, faithfulness) -> eval/human_round2/sample.json.

[EN]
- Role: pick the items a person checks by hand, with a fixed seed, so the sample and its weights can be
  reproduced and the grades can be compared with the two judge models afterwards.
- Scope: questions in Korean or English whose gold sentences are all in Korean or English documents
  (German is left out because the reviewer reads Korean and English). Refused answers are not sampled.
- Part A, question review: 12 v2 questions (3 per language pair ko/en x ko/en) and 12 PDF questions
  (6 per pair ko->en, en->en, spread over text, table and caption). Drawn independently of part B.
- Part B, answer grading: answers of every generation result judged by both judges (v2g_*, pdfg_*), at
  most three answers per question; identical answer texts to the same question (different conditions) are
  one item that lists every condition. Drawn by the correctness verdicts of the two judges: 14 where they
  disagree, 12 where both say YES, 4 where both say NO (fewer if the stratum is smaller). The stratum
  sizes are stored so agreement can be reweighted to the whole pool.
- Part C, faithfulness: 10 of the part B answers that cite passages, those where the judges disagree on
  faithfulness first; the cited passages are shown.
- Usage: uv run python scripts/make_human_round2.py

[KO]
- 역할: 사람이 직접 볼 항목을 고정 시드로 뽑아, 표본과 가중치를 재현할 수 있고 채점 후 두 판정 모델과
  비교할 수 있게 한다.
- 범위: 질문이 한국어·영어이고 정답 문장이 모두 한국어·영어 문서에 있는 항목(검수자가 한국어·영어를
  읽으므로 독일어 제외). 거절 답변은 뽑지 않는다.
- A, 질문 검수: v2 12개(ko/en x ko/en 언어쌍마다 3개), PDF 12개(ko->en, en->en 쌍마다 6개, 본문·표·캡션
  고르게). B와 따로 뽑는다.
- B, 답변 채점: 두 판정 모델이 모두 판정한 생성 결과 전부(v2g_*, pdfg_*)에서 질문당 최대 3개(같은 질문에 답변 문자열이 같으면
  조건이 달라도 항목 하나로 묶고 조건을 모두 적음), 두 판정
  모델의 정확성 판정으로 층을 나눠 뽑는다: 불일치 14, 둘 다 YES 12, 둘 다 NO 4(층이 작으면 그만큼). 층
  크기를 저장해 전체로 가중 환산할 수 있게 한다.
- C, 충실도: B 중 인용이 있는 답 10개(충실도 판정이 엇갈린 것 우선). 인용한 청크 원문을 함께 보여준다.
- 사용: uv run python scripts/make_human_round2.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.generation import CITE_RE  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

SEED = 20261103
RES = REPO / "experiments" / "results"
OUT = REPO / "eval" / "human_round2" / "sample.json"
# 두 판정 모델이 모두 판정한 생성 결과 (Granite 판정 파일이 있는 것)
CONDS = [("pdf" if n.startswith("pdfg") else "v2", n) for n in
         sorted(f.name[len("s3_judge_granite_"):-5] for f in RES.glob("s3_judge_granite_*.json"))
         if n.startswith(("v2g_", "pdfg_")) and (RES / f"s3_judge_{n}.json").exists()]
PER_QUESTION = 3
B_TARGET = {"disagree": 14, "both_yes": 12, "both_no": 4}
READABLE = {"ko", "en"}


def readable(q: dict) -> bool:
    return q["q_lang"] in READABLE and all(g["doc_lang"] in READABLE for g in q["gold"])


def load(name: str) -> dict:
    return json.loads((RES / f"{name}.json").read_text(encoding="utf-8"))


def main() -> None:
    rng = random.Random(SEED)
    queries = {"v2": {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")},
               "pdf": {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_pdf.jsonl")}}

    # B: 조건별 답변 풀과 두 판정 모델의 정확성으로 층을 나눈다
    pool = []
    for evalset, name in CONDS:
        gen = load(name)
        qw = {q["qid"]: q for q in load(f"s3_judge_{name}")["per_query"]}
        gr = {q["qid"]: q for q in load(f"s3_judge_granite_{name}")["per_query"]}
        for g in gen["per_query"]:
            q = queries[evalset][g["qid"]]
            a, b = qw[g["qid"]]["labels"], gr[g["qid"]]["labels"]
            if g["parsed"]["refused"] or not readable(q) or a.get("correctness") is None or b.get("correctness") is None:
                continue
            stratum = "disagree" if a["correctness"] != b["correctness"] else ("both_yes" if a["correctness"] else "both_no")
            pool.append({"evalset": evalset, "condition": name, "qid": g["qid"], "stratum": stratum,
                         "chunking": gen["config"]["chunking"], "answer": g["answer"], "context_ids": g["context_ids"],
                         "judge_qwen": {d: a.get(d) for d in ("correctness", "faithfulness", "answer_relevance")},
                         "judge_granite": {d: b.get(d) for d in ("correctness", "faithfulness", "answer_relevance")}})
    # 같은 질문·같은 답변 문자열은 판정 입력이 같으므로 항목 하나로 묶는다 (조건 목록만 늘어남)
    merged = {}
    for p in pool:
        key = (p["evalset"], p["qid"], p["answer"])
        if key in merged:
            merged[key]["conditions"].append(p.pop("condition"))
        else:
            cond = p.pop("condition")
            merged[key] = {**p, "conditions": [cond]}
    pool = list(merged.values())
    strata = {s: [p for p in pool if p["stratum"] == s] for s in B_TARGET}
    picked = []
    for s, n in B_TARGET.items():
        cand = strata[s][:]
        rng.shuffle(cand)
        for p in cand:
            if len([x for x in picked if x["stratum"] == s]) >= n:
                break
            if sum(x["evalset"] == p["evalset"] and x["qid"] == p["qid"] for x in picked) < PER_QUESTION:
                picked.append(p)
    rng.shuffle(picked)

    # C: B 중 인용이 있는 답, 충실도 판정이 엇갈린 것 먼저
    cited = [p for p in picked if CITE_RE.findall(p["answer"])]
    rng.shuffle(cited)
    cited.sort(key=lambda p: p["judge_qwen"]["faithfulness"] == p["judge_granite"]["faithfulness"])
    faith = {id(p) for p in cited[:10]}

    chunk_text = {}
    for p in picked:
        if id(p) in faith:
            key = json.dumps(p["chunking"], sort_keys=True)
            if key not in chunk_text:
                chunk_text[key] = {c["chunk_id"]: c["text"] for c in load_chunks(ChunkingConfig(**p["chunking"]))}
            ids = [c for c in dict.fromkeys(CITE_RE.findall(p["answer"])) if c in p["context_ids"]]
            p["cited_passages"] = [{"chunk_id": c, "text": chunk_text[key][c]} for c in ids]

    # A: 언어쌍(·근거 종류)별로 고르게
    a_items = []
    for evalset, pairs, per in (("v2", ["ko->ko", "ko->en", "en->ko", "en->en"], 3), ("pdf", ["ko->en", "en->en"], 6)):
        for pair in pairs:
            ql, dl = pair.split("->")
            cand = [q for q in queries[evalset].values() if readable(q) and q["q_lang"] == ql and q["gold"][0]["doc_lang"] == dl]
            rng.shuffle(cand)
            if evalset == "pdf":
                # 근거 종류가 돌아가며 나오게 정렬 (본문, 표, 캡션 순환)
                by_kind = {k: [q for q in cand if q["evidence_kind"] == k] for k in ("text", "table", "caption")}
                cand = [q for i in range(len(cand)) for k in ("text", "table", "caption") if i < len(by_kind[k]) for q in [by_kind[k][i]]]
            for q in cand[:per]:
                a_items.append({"evalset": evalset, "qid": q["qid"], "pair": pair, "evidence_kind": q.get("evidence_kind", "text")})

    out = {"seed": SEED, "readable_languages": sorted(READABLE),
           "part_a": [{"item": f"A{i + 1:02d}", **x} for i, x in enumerate(a_items)],
           "part_b": [{"item": f"B{i + 1:02d}", "faithfulness_item": id(p) in faith,
                       **{k: v for k, v in p.items() if k != "chunking"}} for i, p in enumerate(picked)],
           "b_pool_strata": {s: len(v) for s, v in strata.items()},
           "b_pool_by_condition": {name: sum(name in p["conditions"] for p in pool) for _, name in CONDS}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"A": len(out["part_a"]), "B": len(out["part_b"]), "C": len(faith),
                      "B strata picked": {s: sum(p["stratum"] == s for p in picked) for s in B_TARGET},
                      "pool": out["b_pool_strata"], "by_condition": out["b_pool_by_condition"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
