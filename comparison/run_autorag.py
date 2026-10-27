"""Run the AutoRAG retrieval search (autorag_retrieval.yaml) on the shared corpus and questions.

[EN]
- Output: comparison/autorag_trial/<trial>/ (AutoRAG's own result tree, git-ignored). collect_autorag.py then
  scores every module result with the repository's metrics.
- Usage: uv run python run_autorag.py [yaml]

[KO]
- 출력: comparison/autorag_trial/<trial>/ (AutoRAG 자체 결과 트리, git 제외). 이후 collect_autorag.py가 모든
  모듈 결과를 저장소 지표로 다시 채점한다.
- 사용: uv run python run_autorag.py [yaml]
"""

import shutil
import sys
import time
from pathlib import Path

from autorag.evaluator import Evaluator

def main() -> None:
    HERE = Path(__file__).resolve().parent
    yaml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "autorag_retrieval.yaml"
    project = HERE / "autorag_trial" / yaml_path.stem
    if project.exists():
        shutil.rmtree(project)         # 항상 새 시험으로 시작한다 (이전 시험의 캐시된 결과가 섞이지 않게)
    t0 = time.perf_counter()
    Evaluator(qa_data_path=str(HERE / "data" / "autorag" / "qa.parquet"), corpus_data_path=str(HERE / "data" / "autorag" / "corpus.parquet"),
              project_dir=str(project)).start_trial(str(yaml_path))
    print(f"AutoRAG trial finished in {time.perf_counter() - t0:.0f}s -> {project}")


if __name__ == "__main__":   # spawn 방식 자식 프로세스가 이 파일을 다시 import해도 탐색이 중복 실행되지 않게 한다
    main()
