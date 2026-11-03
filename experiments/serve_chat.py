"""Start the local chat server (models load once, then http://127.0.0.1:<port>).

[EN]
- Role: build the real serving pipeline exactly like experiments/run_pipeline.py (retriever from the
  config, Qwen3 generator, SQLite cache, request log) and run it behind ragbench.chat_server.
- Differences from run_pipeline.py: the cache is NOT deleted at start (answers persist between
  sessions, key includes model and prompt), and requests are logged to logs/requests.jsonl with
  config_id "chat:<exp_id>" so chat traffic can be told apart from experiment runs.
- Binds to 127.0.0.1 only. Retrieval models use cuda:0 and the generator generation.device (cuda:1).
  When the query translator uses the same model as the generator (English pivot), it shares the
  generator's weights instead of loading a second copy on cuda:0; any translator that cannot share is
  loaded at start-up, so an out-of-memory error appears before the server accepts requests.
- Usage: uv run python experiments/serve_chat.py [configs/s6_pipeline_en.json] [--port 8000]
  (default config = English pivot; configs/s35_pipeline.json serves the original-text pipeline)

[KO]
- 역할: experiments/run_pipeline.py와 똑같이 실제 서비스 파이프라인(설정의 검색기, Qwen3 생성기, SQLite
  캐시, 요청 로그)을 만들어 ragbench.chat_server 뒤에서 실행한다.
- run_pipeline.py와의 차이: 시작할 때 캐시를 지우지 않고(답변이 세션 간 유지되며 키에 모델·프롬프트가
  들어간다), 요청은 config_id "chat:<exp_id>"로 logs/requests.jsonl에 기록해 실험 실행과 구별한다.
- 127.0.0.1에만 열린다. 검색 모델은 cuda:0, 생성기는 generation.device(cuda:1)를 쓴다.
  질의 번역 모델이 생성 모델과 같으면(영어 피벗) cuda:0에 두 번째 복사본을 올리지 않고 생성기 가중치를
  같이 쓴다. 공유할 수 없는 번역기는 시작할 때 미리 올려, 메모리 부족이 요청 전에 드러나게 한다.
- 사용: uv run python experiments/serve_chat.py [configs/s6_pipeline_en.json] [--port 8000]
  (기본 설정 = 영어 피벗, 원문 검색 파이프라인은 configs/s35_pipeline.json)
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
    ap.add_argument("config", type=Path, nargs="?", default=REPO / "configs" / "s6_pipeline_en.json",
                    help="serving config (default configs/s6_pipeline_en.json: English pivot + reranker on English text)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--cache", type=Path, default=None, help="LLM cache file (default logs/chat_cache.sqlite)")
    ap.add_argument("--cold-translation", action="store_true", help="benchmark mode: start with an empty translation cache")
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    g = cfg.generation
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)

    def build() -> RAGPipeline:
        # 이 함수는 서버의 작업 스레드 안에서 실행된다 (캐시 SQLite 연결과 GPU 모델의 소유 스레드)
        retriever = build_retriever(cfg)
        retriever.index(chunks)
        if args.cold_translation:
            from ragbench.retrieval.factory import use_cold_translation_cache
            use_cold_translation_cache(retriever)        # 번역 캐시를 비워 질의 번역이 실제로 실행되게 한다
        generator = Generator(g.model, device=g.device, quantize_4bit=g.quantize_4bit, adapter=g.adapter)
        # 질의 번역 모델이 생성 모델과 같으면 한 벌만 올린다 (영어 피벗에서 cuda:0의 Qwen3-4B 복사본 약 7.7 GiB가 빠짐)
        from ragbench.retrieval.factory import share_translator_model
        share_translator_model(retriever, generator)
        return RAGPipeline(retriever, chunks, generator, LLMCache(args.cache or REPO / "logs" / "chat_cache.sqlite"),
                           RequestLogger(REPO / "logs" / "requests.jsonl"), prompt_version=g.prompt_version,
                           context_k=g.context_k, max_new_tokens=g.max_new_tokens, config_id=f"chat:{cfg.exp_id}")

    # host를 127.0.0.1로 고정: 이 컴퓨터의 브라우저에서만 접속된다
    uvicorn.run(create_app(build, chunks), host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
