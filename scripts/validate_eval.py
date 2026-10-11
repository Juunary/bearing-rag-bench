"""Validate eval/queries.jsonl: schema, doc ids, anchors found, chunk mapping, coverage summary.

[EN]
- Role: run while writing the eval set. For every query checks required fields, that each gold
  doc_id exists, that each anchor is located in the document (exact or whitespace-insensitive),
  and that it maps to at least one chunk under the default chunking. gold[0] is the primary
  evidence (grade 2): its language decides mono vs cross and the group. Prints a per-language /
  mono-vs-cross coverage table at the end.
- Exit code 1 if any problem, so it can double as a test later.
- Usage: uv run python scripts/validate_eval.py [eval/queries.jsonl]

[KO]
- 역할: 평가셋을 쓰는 동안 돌리는 검사기. 질문마다 필수 필드, gold의 doc_id 존재, anchor가 문서에서
  찾아지는지(정확/공백 무시), 기본 청킹에서 청크 1개 이상에 매핑되는지 확인한다. gold[0]이 주 근거
  (등급 2)이며 그 언어가 단일/교차와 그룹을 결정한다. 끝에 언어별 분포 표를 출력한다.
- 문제가 하나라도 있으면 종료 코드 1 (나중에 테스트로도 쓸 수 있음).
- 사용: uv run python scripts/validate_eval.py [eval/queries.jsonl]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ChunkingConfig  # noqa: E402
from ragbench.evalset import locate_anchor, map_gold_to_chunks  # noqa: E402
from ragbench.ingest import REPO, load_docs  # noqa: E402

REQUIRED = {"qid", "q_lang", "question", "gold", "type"}
LANGS = {"ko", "en", "de"}


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "eval" / "queries.jsonl"
    docs = {d["doc_id"]: d for d in load_docs()}
    chunks = load_chunks(ChunkingConfig())
    problems: list[str] = []
    seen_qids: set[str] = set()
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                q = json.loads(line)
            except json.JSONDecodeError as e:
                problems.append(f"line {ln}: invalid JSON ({e})"); continue
            qid = q.get("qid", f"line{ln}")
            missing = REQUIRED - set(q)
            if missing:
                problems.append(f"{qid}: missing fields {sorted(missing)}")
            if qid in seen_qids:
                problems.append(f"{qid}: duplicate qid")
            seen_qids.add(qid)
            if q.get("q_lang") not in LANGS:
                problems.append(f"{qid}: q_lang must be one of {sorted(LANGS)}")
            golds = q.get("gold") or []
            if not golds:
                problems.append(f"{qid}: gold is empty")
            if golds and max(g.get("grade", 0) for g in golds) < 2:
                problems.append(f"{qid}: no grade-2 (core) evidence")
            if golds and golds[0].get("grade") != 2:
                problems.append(f"{qid}: gold[0] is the primary evidence and must have grade 2")
            for i, g in enumerate(golds):
                d = docs.get(g.get("doc_id"))
                if d is None:
                    problems.append(f"{qid}: gold[{i}] unknown doc_id {g.get('doc_id')!r}"); continue
                if g.get("doc_lang") != d["lang"]:
                    problems.append(f"{qid}: gold[{i}] doc_lang {g.get('doc_lang')!r} != document lang {d['lang']!r}")
                if g.get("grade") not in (1, 2):
                    problems.append(f"{qid}: gold[{i}] grade must be 1 or 2")
                try:
                    locate_anchor(d["text"], g.get("anchor", ""))
                except ValueError:
                    problems.append(f"{qid}: gold[{i}] anchor not found in {g['doc_id']}: {g.get('anchor', '')[:50]!r}")
            try:
                mapped = map_gold_to_chunks(golds, docs, chunks)
            except (ValueError, KeyError):
                mapped = {}
            primary_lang = golds[0].get("doc_lang") if golds else None
            is_cross = primary_lang != q.get("q_lang")
            if q.get("type") != ("cross" if is_cross else "mono"):
                problems.append(f"{qid}: type is {q.get('type')!r} but primary evidence (gold[0]) language implies {'cross' if is_cross else 'mono'}")
            rows.append((qid, q.get("q_lang"), "cross" if is_cross else "mono", [primary_lang], len(mapped)))

    print(f"{len(rows)} queries, {len(problems)} problems")
    for p in problems:
        print("  !", p)
    c = Counter((r[1], r[2]) for r in rows)
    print("\ncoverage (q_lang, mono/cross) -> count")
    for lang in sorted(LANGS):
        print(f"  {lang}: mono {c[(lang, 'mono')]:2d}  cross {c[(lang, 'cross')]:2d}")
    pairs = Counter(f"{r[1]}->{l}" for r in rows for l in r[3])
    print("language pairs:", dict(sorted(pairs.items())))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
