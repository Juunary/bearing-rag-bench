"""Run a list of retrieval configs one after another and keep going when one fails.

[EN]
- Role: drive experiments/run_retrieval.py over configs/v2/*.json (or the names given), skipping configs
  whose result file already exists (use --force to rerun) and writing one line per config to the log.
  A failing config does not stop the suite; failures are listed at the end.
- Usage: uv run python experiments/run_suite.py [--force] [--glob 'configs/v2/v2_b_*.json'] [name ...]

[KO]
- 역할: experiments/run_retrieval.py를 configs/v2/*.json(또는 지정한 이름)에 대해 차례로 실행한다. 결과
  파일이 이미 있으면 건너뛰고(--force면 재실행), 설정마다 한 줄을 로그에 남긴다. 하나가 실패해도 멈추지
  않고 마지막에 실패 목록을 보여 준다.
- 사용: uv run python experiments/run_suite.py [--force] [--glob 'configs/v2/v2_b_*.json'] [이름 ...]
"""

from __future__ import annotations

import argparse
import glob
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--glob", default="configs/v2/*.json")
    ap.add_argument("names", nargs="*")
    args = ap.parse_args()
    paths = sorted(glob.glob(str(REPO / args.glob)))
    if args.names:
        paths = [p for p in paths if Path(p).stem in args.names or Path(p).stem.removeprefix("v2_") in args.names]
    failed = []
    for p in paths:
        exp = Path(p).stem
        if (REPO / "experiments" / "results" / f"{exp}.json").exists() and not args.force:
            print(f"[skip] {exp}", flush=True)
            continue
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, str(REPO / "experiments" / "run_retrieval.py"), p], capture_output=True, text=True, cwd=REPO)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("overall:")]
        status = "ok" if r.returncode == 0 else "FAILED"
        print(f"[{status}] {exp} {time.perf_counter() - t0:.0f}s {line[0][:110] if line else ''}", flush=True)
        if r.returncode != 0:
            failed.append(exp)
            print("   " + "\n   ".join(r.stderr.strip().splitlines()[-4:]), flush=True)
    print("FAILED:", failed if failed else "none", flush=True)


if __name__ == "__main__":
    main()
