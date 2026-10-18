"""Start the local chat server (models load once, then http://127.0.0.1:<port>).

[EN]
- Role: build the real serving pipeline exactly like experiments/run_pipeline.py (retriever from the
  config, Qwen3 generator, SQLite cache, request log) and run it behind ragbench.chat_server.
- Differences from run_pipeline.py: the cache is NOT deleted at start (answers persist between
  sessions, key includes model and prompt), and requests are logged to logs/requests.jsonl with
  config_id "chat:<exp_id>" so chat traffic can be told apart from experiment runs.
- Binds to 127.0.0.1 only. Retrieval models use cuda:0 and the generator generation.device (cuda:1).
- Usage: uv run python experiments/serve_chat.py configs/s35_pipeline.json [--port 8000]

[KO]
- 역할: experiments/run_pipeline.py와 똑같이 실제 서비스 파이프라인(설정의 검색기, Qwen3 생성기, SQLite
  캐시, 요청 로그)을 만들어 ragbench.chat_server 뒤에서 실행한다.
- run_pipeline.py와의 차이: 시작할 때 캐시를 지우지 않고(답변이 세션 간 유지되며 키에 모델·프롬프트가
  들어간다), 요청은 config_id "chat:<exp_id>"로 logs/requests.jsonl에 기록해 실험 실행과 구별한다.
- 127.0.0.1에만 열린다. 검색 모델은 cuda:0, 생성기는 generation.device(cuda:1)를 쓴다.
- 사용: uv run python experiments/serve_chat.py configs/s35_pipeline.json [--port 8000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

from ragbench.cache import LLMCache  # noqa: E402
from ragbench.chat_server import create_app  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.generation import Generator  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.pipeline import RAGPipeline  # noqa: E402
from ragbench.requestlog import RequestLogger  # noqa: E402
from ragbench.retrieval.factory import build_retriever  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    g = cfg.generation
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)

    def build() -> RAGPipeline:
        # 이 함수는 서버의 작업 스레드 안에서 실행된다 (캐시 SQLite 연결과 GPU 모델의 소유 스레드)
        retriever = build_retriever(cfg)
        retriever.index(chunks)
        generator = Generator(g.model, device=g.device, quantize_4bit=g.quantize_4bit, adapter=g.adapter)
        return RAGPipeline(retriever, chunks, generator, LLMCache(REPO / "logs" / "chat_cache.sqlite"),
                           RequestLogger(REPO / "logs" / "requests.jsonl"), prompt_version=g.prompt_version,
                           context_k=g.context_k, max_new_tokens=g.max_new_tokens, config_id=f"chat:{cfg.exp_id}")

    # host를 127.0.0.1로 고정: 이 컴퓨터의 브라우저에서만 접속된다
    uvicorn.run(create_app(build, chunks), host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
