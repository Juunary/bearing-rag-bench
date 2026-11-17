"""Coverage gaps: which questions the system refused, grouped by topic, with the nearest knowledge-bundle page.

[EN]
- Role: turn refusals into a backlog for the knowledge bundle. A refused question is either outside what the system
  should cover, or a topic with no page yet, or a topic whose page exists but was not matched or did not hold the
  answer. Grouping the refused questions and putting the nearest page next to each group separates these cases.
- Sources (`collect_refusals`): request logs (logs/*requests*.jsonl, blocked rows), serving-config answers
  (eval/service/*.json, blocked rows), and the knowledge-bundle experiments (eval/kb*/results.json, the rows where
  the serving path of the run was blocked: kb_matched if present, else kb_first, else rag). Same question text = one entry.
- Grouping (`leader_clusters`): questions in a fixed order; each joins the first group whose leader has cosine
  >= `threshold` with it, otherwise it starts a new group. Deterministic and needs no cluster count.
- Per group: size, leader, members, nearest page and cosine. A group whose nearest cosine is >= the bundle's dense
  threshold (0.55) is marked "page exists" (routing or page content to check), otherwise "new page".

[KO]
- 역할: 거절을 지식 번들의 작업 목록으로 바꾼다. 거절된 질문은 (1) 다룰 범위 밖이거나 (2) 페이지가 아직 없는 주제이거나 (3) 페이지가
  있는데 매칭되지 않았거나 답이 페이지에 없는 경우다. 거절 질문을 묶고 묶음마다 가장 가까운 페이지를 붙이면 셋이 갈린다.
- 출처: 요청 로그(blocked), 서비스 설정 답변(eval/service/*.json), 번들 실험(eval/kb*/results.json에서 그 실행의 서비스 경로가 차단된
  행: kb_matched가 있으면 그것, 없으면 kb_first, 없으면 rag). 질문 문자열이 같으면 하나.
- 묶기: 고정 순서로 질문을 보며 리더와의 코사인이 `threshold` 이상인 첫 묶음에 넣고, 없으면 새 묶음을 만든다. 결정적이고 묶음 수가
  필요 없다.
- 묶음마다 크기, 리더, 구성원, 가장 가까운 페이지와 코사인. 코사인이 번들 dense 임계값(0.55) 이상이면 "페이지 있음"(라우팅이나
  페이지 내용 점검), 아니면 "새 페이지".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ragbench.ingest import REPO

REFUSAL_REASONS = {"refusal_sentinel", "refusal_text", "no_citation", "invalid_citation", "claim_unsupported"}
SERVING_MODES = ("kb_matched", "kb_first", "rag")


def _truthy(v: Any) -> bool:
    return v is True or v == "True"


def collect_refusals(repo: Path = REPO) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}

    def add(question: str, source: str, reason: str | None, scope: str | None = None) -> None:
        q = (question or "").strip()
        if q and q not in out:
            out[q] = {"question": q, "source": source, "reason": reason, "scope": scope}

    for p in sorted((repo / "logs").glob("*requests*.jsonl")) if (repo / "logs").exists() else []:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if _truthy(r.get("blocked")) and r.get("block_reason") in REFUSAL_REASONS:
                    add(r.get("question"), p.name, r.get("block_reason"))
    for p in sorted((repo / "eval" / "service").glob("*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")).get("rows", []):
            if _truthy(r.get("blocked")):
                add(r.get("question"), f"service/{p.name}", r.get("reason"), r.get("scope"))
    for p in sorted((repo / "eval").glob("kb*/results.json")):
        for r in json.loads(p.read_text(encoding="utf-8")).get("rows", []):
            mode = next((m for m in SERVING_MODES if m in r["modes"]), None)
            if mode and r["modes"][mode]["blocked"]:
                add(r["question"], f"{p.parent.name}/{mode}", r["modes"][mode].get("reason"), "in" if r.get("topic") else None)
    return list(out.values())


def leader_clusters(vecs: np.ndarray, threshold: float = 0.6) -> list[list[int]]:
    """Greedy leader clustering of L2-normalised vectors; returns index groups in order of creation."""
    groups: list[list[int]] = []
    leaders: list[int] = []
    for i in range(len(vecs)):
        sims = [float(vecs[i] @ vecs[j]) for j in leaders]
        best = int(np.argmax(sims)) if sims else -1
        if best >= 0 and sims[best] >= threshold:
            groups[best].append(i)
        else:
            leaders.append(i)
            groups.append([i])
    return groups


def gap_table(items: list[dict[str, Any]], qvecs: np.ndarray, page_ids: list[str], page_vecs: np.ndarray,
              threshold: float = 0.6, dense_min: float = 0.55) -> list[dict[str, Any]]:
    rows = []
    for g in leader_clusters(qvecs, threshold):
        centre = qvecs[g].mean(axis=0)
        centre /= np.linalg.norm(centre) or 1.0
        sims = page_vecs @ centre if len(page_ids) else np.array([])
        k = int(np.argmax(sims)) if len(sims) else -1
        nearest = (page_ids[k], round(float(sims[k]), 4)) if k >= 0 else (None, 0.0)
        rows.append({"size": len(g), "leader": items[g[0]]["question"], "members": [items[i] for i in g],
                     "nearest_page": nearest[0], "cosine": nearest[1],
                     "kind": "page exists" if nearest[1] >= dense_min else "new page"})
    return sorted(rows, key=lambda r: (-r["size"], r["leader"]))
