"""Run an experiment (optionally) and compare it with its frozen baseline.

[EN]
- Role: command-line front end of ragbench.regression.
- Typical use:
    uv run python experiments/regression.py configs/s1_hybrid_rrf_rerank.json --run
        reruns the experiment, then compares experiments/results/<exp_id>.json with eval/baselines/<exp_id>.json
    uv run python experiments/regression.py configs/s3_gen_cite_refuse_v1.json
        only compares the existing result file
    ... --update-baseline     accept the current result as the new baseline (an intended change)
    ... --strict              treat WARN as failure
- Exit code: 0 for PASS and WARN (1 for WARN with --strict), 1 for FAIL.
- The run step uses the runner that matches the config's stage (s1 -> run_retrieval, s3 -> run_generation).

[KO]
- 역할: ragbench.regression의 명령줄 진입점.
- 사용 예는 위 영문과 같다. --run은 실험을 다시 돌린 뒤 결과를 기준선과 비교하고, 인자 없이 쓰면 기존
  결과 파일만 비교하며, --update-baseline은 현재 결과를 새 기준선으로 승인(의도한 변경)하고, --strict는
  WARN도 실패로 본다.
- 종료 코드: PASS와 WARN은 0(--strict의 WARN은 1), FAIL은 1.
- --run은 설정의 stage에 맞는 실행기를 쓴다(s1 -> run_retrieval, s3 -> run_generation).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.config import ExperimentConfig  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.regression import TOLERANCE, compare, extract_baseline  # noqa: E402

RUNNERS = {"s1": "run_retrieval.py", "s3": "run_generation.py"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--tolerance", type=float, default=TOLERANCE)
    args = ap.parse_args()

    cfg = ExperimentConfig.load(args.config)
    result_path = REPO / "experiments" / "results" / f"{cfg.exp_id}.json"
    baseline_path = REPO / "eval" / "baselines" / f"{cfg.exp_id}.json"

    if args.run:
        runner = RUNNERS[cfg.stage]
        subprocess.run([sys.executable, str(REPO / "experiments" / runner), str(args.config)], check=True)
    result = json.loads(result_path.read_text(encoding="utf-8"))

    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(extract_baseline(result), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"baseline updated: {baseline_path.relative_to(REPO)}")
        return

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    report = compare(result, baseline, args.tolerance)
    print(f"[{report.status}] {cfg.exp_id}")
    for line in report.lines:
        print("  ", line)
    sys.exit(1 if report.status == "FAIL" or (args.strict and report.status == "WARN") else 0)


if __name__ == "__main__":
    main()
