"""Markdown comparison table from result JSON files.

[EN]
- Role: read N result files, print one table: exp_id, config fields that DIFFER between the
  runs, the chosen metrics, query count. --by-group adds one table per language pair.
- Why "varying fields only": with full configs the table is unreadable; the diff is what
  explains the metric change.
- Usage:
    uv run python experiments/compare.py experiments/results/s1_*.json
    uv run python experiments/compare.py experiments/results/s1_*.json --by-group
    uv run python experiments/compare.py ... --metrics recall@5 mrr@10 ndcg@10

[KO]
- 역할: 결과 파일 N개를 읽어 표 하나를 출력: exp_id, 실험 간 "달라진" 설정 필드, 선택한 지표, 질의 수.
  --by-group이면 언어쌍별 표를 추가.
- "달라진 필드만" 보여주는 이유: 설정 전체를 넣으면 표를 읽을 수 없다. 지표 변화를 설명하는 건 차이뿐이다.
- 사용법은 위 영문 예시와 같다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.config import ExperimentResult  # noqa: E402

DEFAULT_METRICS = ["recall@5", "mrr@10", "ndcg@10"]
IGNORED_CONFIG_KEYS = {"exp_id", "description"}


def flatten(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def varying_keys(configs: list[dict[str, Any]]) -> list[str]:
    flat = [flatten(c) for c in configs]
    keys = sorted({k for f in flat for k in f} - IGNORED_CONFIG_KEYS)
    return [k for k in keys if len({repr(f.get(k)) for f in flat}) > 1]


def fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.3f}"
    if v is None:
        return "-"
    return str(v)


def table(rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+", type=Path)
    ap.add_argument("--metrics", nargs="+", default=DEFAULT_METRICS)
    ap.add_argument("--by-group", action="store_true")
    args = ap.parse_args()

    results = [ExperimentResult.load(p) for p in args.results]
    keys = varying_keys([r.config for r in results])
    short = [k.split(".")[-1] if k.count(".") else k for k in keys]
    header = ["exp_id", *short, *args.metrics, "n"]

    def rows_for(group: str) -> list[list[str]]:
        rows = []
        for r in results:
            flat = flatten(r.config)
            m = r.metrics.get("by_group", {}).get(group) if group != "overall" else r.metrics.get("overall", {})
            m = m or {}
            rows.append([r.exp_id, *(fmt(flat.get(k)) for k in keys),
                         *(fmt(m.get(name)) for name in args.metrics), fmt(m.get("n"))])
        return rows

    print("### overall\n")
    print(table(rows_for("overall"), header))
    if args.by_group:
        groups = sorted({g for r in results for g in r.metrics.get("by_group", {})})
        for g in groups:
            print(f"\n### {g}\n")
            print(table(rows_for(g), header))


if __name__ == "__main__":
    main()
