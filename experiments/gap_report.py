"""Refused questions grouped by topic, as a backlog for new knowledge-bundle pages -> eval/gaps/report.md.

[EN]
- Role: CLI around ragbench.gaps (sources, grouping and the page-exists / new-page rule are documented there).
  Questions and pages are embedded with bge-m3 (the serving dense model; CPU works for a few hundred questions).
- Outputs: eval/gaps/report.md (groups by size: kind, nearest page and cosine, member questions with their source)
  and eval/gaps/report.json.
- Next step for "new page" groups: an AI draft (verified: false) -> sealed commit -> a person writes questions ->
  review -> verified: true, the procedure of data/kb_review.md.
- Usage: uv run python experiments/gap_report.py [--threshold 0.6] [--device cuda:0]

[KO]
- 역할: ragbench.gaps를 실행하는 CLI(출처·묶기·페이지 있음/새 페이지 규칙은 그 모듈에 있다). 질문과 페이지는 bge-m3(서비스 dense
  모델)로 임베딩한다. 질문 수백 개는 CPU로도 된다.
- 출력: eval/gaps/report.md(크기순 묶음: 종류, 가장 가까운 페이지와 코사인, 구성 질문과 출처), eval/gaps/report.json.
- "새 페이지" 묶음의 다음 단계: AI 초안(verified: false) -> 봉인 커밋 -> 사람이 질문 작성 -> 검수 -> verified: true (data/kb_review.md 절차).
- 사용: uv run python experiments/gap_report.py [--threshold 0.6] [--device cuda:0]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.concepts import load_concepts  # noqa: E402
from ragbench.gaps import collect_refusals, gap_table  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402

OUT = REPO / "eval" / "gaps"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.6, help="cosine to join a group")
    ap.add_argument("--dense-min", type=float, default=0.55, help="the bundle's dense matching threshold")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()
    from ragbench.embedding import Embedder
    items = collect_refusals()
    pages = load_concepts(REPO / "data" / "kb")
    emb = Embedder("BAAI/bge-m3", device=args.device)
    qv = emb.encode_queries([it["question"] for it in items])
    pv = emb.encode([p.page_text() for p in pages])
    rows = gap_table(items, qv, [p.id for p in pages], pv, args.threshold, args.dense_min)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps({"threshold": args.threshold, "dense_min": args.dense_min, "n_questions": len(items),
                                                 "groups": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# 거절 질문 묶음 (지식 번들 작업 목록)", "",
             f"거절된 질문 {len(items)}개, 묶음 {len(rows)}개 (묶음 기준 코사인 {args.threshold}, 페이지 있음 기준 {args.dense_min}).", "",
             "| # | 크기 | 종류 | 가장 가까운 페이지 | 코사인 | 대표 질문 |", "|---|---|---|---|---|---|"]
    lines += [f"| {i} | {r['size']} | {r['kind']} | {r['nearest_page']} | {r['cosine']:.2f} | {r['leader'][:80]} |" for i, r in enumerate(rows, 1)]
    lines.append("")
    for i, r in enumerate(rows, 1):
        lines += [f"## {i}. {r['kind']}: {r['nearest_page']} ({r['cosine']:.2f})", ""]
        lines += [f"- {m['question']} ({m['source']}{', ' + m['reason'] if m['reason'] else ''})" for m in r["members"]] + [""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:len(rows) + 6]))


if __name__ == "__main__":
    main()
