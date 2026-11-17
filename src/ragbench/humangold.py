"""Human gold set: every answer a person has graded, in one file, with a sealed dev/test split.

[EN]
- Role: the human grades are spread over four rounds with four formats (eval/human_labels.json, eval/human_round2,
  eval/kb, eval/kb2). Judges and the claim check are calibrated against people, so the grades are gathered into one
  list of items (eval/human_gold/items.jsonl) that later scripts read without knowing where each grade came from.
- Item fields: id (g001 ..), source (r1 | r2 | kb1 | kb2), src_item (item id in its round: q025, B01, K05, M01),
  qid, question, q_lang, answer (the text the grader saw), blocked (shown as a refusal), context_ids, reference
  (r1/r2: the eval set's gold sentences; kb1/kb2: the guide page of the question's topic as kb_<id>#0, resolved by
  `reference_texts`), label ({"kind": "correctness", "value": 맞음|부분|틀림} or {"kind": "refusal", "value":
  적절|부적절|None}), extra (other dimensions the grader gave: faithfulness 예/아니오, answer_relevance), split.
- Grader notes are kept in the source files only (they would tell a second grader or a judge the answer).
- Round 1 graded one refusal as "거절" without saying whether it was appropriate; it is a refusal item with value None.
- Duplicates: the same (question, answer) graded in two rounds becomes one item (the first round wins).
- Split: stratified by (source, label value), shuffled with a fixed seed inside each stratum, alternating dev/test,
  so the split is reproducible and every stratum is in both halves. Test is sealed: choose judge prompts, thresholds
  and claim-check policies on dev only.

[KO]
- 역할: 사람 채점은 네 라운드에 네 가지 형식으로 흩어져 있다(eval/human_labels.json, eval/human_round2, eval/kb, eval/kb2).
  판정 모델과 claim check를 사람 기준으로 보정하려면 한 목록이 필요해서 eval/human_gold/items.jsonl로 모은다.
- 항목: id, source(r1|r2|kb1|kb2), src_item(원래 라운드의 항목 ID), qid, question, q_lang, answer(채점자가 본 문자열),
  blocked(거절로 보였는지), context_ids, reference(r1/r2는 평가셋 정답 문장, kb1/kb2는 질문 주제의 안내 페이지 kb_<id>#0),
  label(정확성 맞음/부분/틀림 또는 거절 적절/부적절/None), extra(충실도·답변 관련성 등 그 밖의 사람 판정), split.
- 채점자 메모는 원본 파일에만 둔다(두 번째 채점자나 판정 모델에게 답을 알려 주게 된다).
- 1차의 "거절"은 적절 여부를 적지 않았으므로 거절 항목, 값 None.
- 같은 (질문, 답변)이 두 라운드에 있으면 한 항목(앞 라운드 우선).
- 분할: (source, 라벨 값) 층마다 고정 시드로 섞고 dev/test를 번갈아 배정한다. 재현되고 모든 층이 양쪽에 들어간다.
  test는 봉인: 판정 프롬프트·임계값·claim check 정책은 dev로만 고른다.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from ragbench.ingest import REPO

SEED = 20261117
GOLD_DIR = REPO / "eval" / "human_gold"
ITEMS_PATH = GOLD_DIR / "items.jsonl"
CORRECTNESS = ("맞음", "부분", "틀림")
REFUSAL = ("적절", "부적절")
REFUSAL_TEXTS = ("제공된 문서에서 이 질문에 답할 근거를 찾지 못했습니다.", "NO_ANSWER")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _label(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Human grade dict of one item -> {"kind", "value"}; None if the item has no correctness/refusal grade."""
    if "refusal" in raw:
        return {"kind": "refusal", "value": raw["refusal"] if raw["refusal"] in REFUSAL else None}
    c = raw.get("correctness")
    if c in CORRECTNESS:
        return {"kind": "correctness", "value": c}
    if c == "거절":                       # 1차: 거절로만 적고 적절 여부는 적지 않음
        return {"kind": "refusal", "value": None}
    return None


def _extra(raw: dict[str, Any]) -> dict[str, str]:
    return {k: raw[k] for k in ("faithfulness", "answer_relevance") if k in raw}


def _anchors(q: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"doc_id": g["doc_id"], "grade": g["grade"], "text": g["anchor"]} for g in q.get("gold", [])]


def collect_round1(repo: Path = REPO) -> list[dict[str, Any]]:
    labels = _json(repo / "eval" / "human_labels.json")
    res = {p["qid"]: p for p in _json(repo / "experiments" / "results" / f"{labels['source']}.json")["per_query"]}
    queries = {q["qid"]: q for q in _jsonl(repo / "eval" / "queries.jsonl")}
    out = []
    for qid, raw in labels["labels"].items():
        lab = _label(raw)
        if lab is None:
            continue
        p = res[qid]
        out.append({"source": "r1", "src_item": qid, "qid": qid, "question": p["question"], "q_lang": p["q_lang"],
                    "answer": p["answer"], "blocked": bool(p["parsed"]["refused"]), "context_ids": p["context_ids"],
                    "reference": _anchors(queries[qid]), "label": lab, "extra": _extra(raw), "chunking": {"corpus": "wiki"}})
    return out


def collect_round2(repo: Path = REPO) -> list[dict[str, Any]]:
    d = repo / "eval" / "human_round2"
    labels = _json(d / "labels.json")["labels"]
    sets = {"v2": {q["qid"]: q for q in _jsonl(repo / "eval" / "queries_v2.jsonl")},
            "pdf": {q["qid"]: q for q in _jsonl(repo / "eval" / "queries_pdf.jsonl")}}
    out = []
    for b in _json(d / "sample.json")["part_b"]:
        lab = _label(labels.get(b["item"], {}))
        if lab is None:
            continue
        q = sets[b["evalset"]][b["qid"]]
        # 답을 낸 조건의 청크 세트: v2는 위키, PDF는 위키+PDF (조건 이름에 _th가 있으면 표 머리글 반복). 같은 답을 낸 조건은 같은 청크를 본다
        chunking = {"corpus": "wiki"} if b["evalset"] == "v2" else {"corpus": "wiki_pdf", "table_header": "_th_" in b["conditions"][0]}
        out.append({"source": "r2", "src_item": b["item"], "qid": f"{b['evalset']}:{b['qid']}", "question": q["question"],
                    "q_lang": q["q_lang"], "answer": b["answer"], "blocked": False, "context_ids": b["context_ids"],
                    "reference": _anchors(q), "label": lab, "extra": _extra(labels[b["item"]]), "chunking": chunking})
    return out


def collect_kb(round_dir: Path, source: str, questions: list[Path], repo: Path = REPO) -> list[dict[str, Any]]:
    labels = _json(round_dir / "labels.json")["labels"]
    rows = {r["qid"]: r for r in _json(round_dir / "results.json")["rows"]}
    qs = {q["qid"]: q for p in questions for q in _jsonl(p)}
    out = []
    for it in _json(round_dir / "sample.json")["items"]:
        lab = _label(labels.get(it["item"], {}))
        if lab is None:
            continue
        q = qs[it["qid"]]
        mode = rows[it["qid"]]["modes"][it["modes"][0]]       # 같은 답을 낸 방식은 컨텍스트도 같다 (첫 방식 기준)
        topic = q.get("topic")
        out.append({"source": source, "src_item": it["item"], "qid": it["qid"], "question": q["question"], "q_lang": q["q_lang"],
                    "answer": it["answer"], "blocked": bool(it["blocked"]), "context_ids": mode["context_ids"],
                    "reference": [{"kb_page": f"kb_{topic}#0"}] if topic else [], "label": lab,
                    "extra": {"scope": q.get("scope"), "modes": it["modes"]},
                    "chunking": {"corpus": "wiki_pdf", "table_header": True}})       # run_kb.py의 CONFIG (pdfth_x13...)
    return out


def collect_all(repo: Path = REPO) -> list[dict[str, Any]]:
    kbq = [repo / "eval" / "kb" / "questions.jsonl", repo / "eval" / "kb" / "questions2.jsonl"]
    items = (collect_round1(repo) + collect_round2(repo) + collect_kb(repo / "eval" / "kb", "kb1", kbq, repo)
             + collect_kb(repo / "eval" / "kb2", "kb2", kbq, repo))
    return dedupe(items)


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out = []
    for it in items:
        key = (it["question"].strip(), it["answer"].strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def assign_split(items: list[dict[str, Any]], seed: int = SEED) -> list[dict[str, Any]]:
    """Number the items g001.. and give each a dev/test split, stratified by (source, label value)."""
    for i, it in enumerate(items, start=1):
        it["id"] = f"g{i:03d}"
    strata: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for it in items:
        strata[(it["source"], it["label"]["kind"], it["label"]["value"])].append(it)
    rng = random.Random(seed)
    flip = 0
    for key in sorted(strata, key=str):
        group = sorted(strata[key], key=lambda x: x["id"])
        rng.shuffle(group)
        for it in group:
            # 층을 넘어 이어서 번갈아 배정한다: 크기가 홀수인 층이 여럿이어도 남는 하나가 늘 dev로 가지 않는다
            it["split"] = "dev" if flip % 2 == 0 else "test"
            flip += 1
    return items


def build(repo: Path = REPO, seed: int = SEED) -> list[dict[str, Any]]:
    keys = ("id", "split", "source", "src_item", "qid", "question", "q_lang", "answer", "blocked", "context_ids",
            "reference", "label", "extra", "chunking")
    return [{k: it[k] for k in keys} for it in assign_split(collect_all(repo), seed)]


ADJUDICATED_PATH = GOLD_DIR / "adjudicated.json"


def load_items(path: Path = ITEMS_PATH, split: str | None = None, adjudicated: Path | None = ADJUDICATED_PATH) -> list[dict[str, Any]]:
    """Gold items; label values agreed by both graders after a disagreement (adjudicated.json, {gold id: value}) replace the first grade."""
    items = _jsonl(path)
    agreed = _json(adjudicated)["labels"] if adjudicated is not None and adjudicated.exists() else {}
    for it in items:
        if it["id"] in agreed:
            it["label"] = {**it["label"], "value": agreed[it["id"]], "adjudicated": True}
    return [it for it in items if split is None or it["split"] == split]


def reference_texts(item: dict[str, Any], kb_dir: Path = REPO / "data" / "kb") -> list[str]:
    """Reference evidence as text: gold sentences, or the guide page body for kb items."""
    out = []
    for r in item["reference"]:
        if "text" in r:
            out.append(r["text"])
        elif "kb_page" in r:
            from ragbench.concepts import load_concepts
            pages = {f"kb_{c.id}#0": f"{c.title}\n{c.description}" for c in load_concepts(kb_dir)}
            out.append(pages[r["kb_page"]])
    return out


def context_passages(item: dict[str, Any], chunk_sets: dict | None = None, kb_dir: Path = REPO / "data" / "kb") -> list[dict[str, Any]]:
    """The passages the answer was generated from: chunks of the item's chunk set, or guide pages (kb_<id>#0)."""
    from ragbench.chunking import load_chunks, chunk_set_id
    from ragbench.config import ChunkingConfig
    from ragbench.kb import page_passage
    from ragbench.concepts import load_concepts

    cfg = ChunkingConfig(**item["chunking"])
    cache = chunk_sets if chunk_sets is not None else {}
    sid = chunk_set_id(cfg)
    if sid not in cache:
        cache[sid] = {c["chunk_id"]: c for c in load_chunks(cfg)}
    if "kb" not in cache and any(i.startswith("kb_") for i in item["context_ids"]):
        cache["kb"] = {f"kb_{c.id}#0": page_passage(c) for c in load_concepts(kb_dir)}
    return [cache["kb"][i] if i.startswith("kb_") else cache[sid][i] for i in item["context_ids"]]


def binary(value: str | None) -> bool | None:
    """Correctness as yes/no with 부분 = no (the convention of the earlier agreement tables)."""
    return None if value is None else value == "맞음"
