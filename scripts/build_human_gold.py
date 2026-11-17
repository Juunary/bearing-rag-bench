"""Gather every human grade into eval/human_gold/items.jsonl with a sealed dev/test split.

[EN]
- Role: CLI around ragbench.humangold (format, sources, split rule are documented there).
- Prints counts per source, label and split so the file can be checked at a glance.
- Usage: uv run python scripts/build_human_gold.py [--seed 20261117]

[KO]
- 역할: ragbench.humangold를 실행하는 CLI(형식·출처·분할 규칙은 그 모듈에 있다).
- 출처·라벨·분할별 개수를 출력해 바로 확인할 수 있게 한다.
- 사용: uv run python scripts/build_human_gold.py [--seed 20261117]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.humangold import ITEMS_PATH, SEED, build  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    items = build(seed=args.seed)
    ITEMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ITEMS_PATH.write_text("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items), encoding="utf-8")
    c = Counter((it["source"], it["label"]["kind"], it["label"]["value"], it["split"]) for it in items)
    for key in sorted(c, key=str):
        print(*key, c[key])
    print("splits", dict(Counter(it["split"] for it in items)))
    print(f"wrote {len(items)} items -> {ITEMS_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
