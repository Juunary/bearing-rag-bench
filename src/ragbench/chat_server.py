"""Local chat server: the RAG pipeline behind a small HTTP API and one web page.

[EN]
- Role: expose RAGPipeline.answer() on localhost so questions can be typed into a browser instead of
  run from scripts. Nothing in the answer path changes: validation, retrieval, prompt, cache,
  output check and request log all happen in the pipeline; this module only translates HTTP <-> Response.
- Endpoints: GET / (chat page), GET /api/health, POST /api/ask {question, lang?} ->
  {answer, blocked, reason, lang, cache_hit, timings_ms, contexts[{chunk_id, text}]}.
  The raw model answer is never returned (it stays in the request log).
- Threading: the pipeline is built inside ONE worker thread and every request runs there. Reasons:
  a SQLite connection (LLM cache) may only be used by the thread that created it, and one GPU should
  run one generation at a time. Requests therefore queue; the page shows a "thinking" state.
- Single turn: the pipeline has no conversation memory; each question is answered on its own and the
  page says so. The server binds to 127.0.0.1 by default (not reachable from other machines).
- The pipeline is passed as a factory so the app can be tested with fake parts on CPU.

[KO]
- 역할: RAGPipeline.answer()를 localhost에 노출해 스크립트 대신 브라우저에서 질문을 입력할 수 있게 한다.
  답변 경로는 바뀌지 않는다: 검사, 검색, 프롬프트, 캐시, 출력 검사, 요청 로그는 모두 파이프라인 안에서
  일어나고, 이 모듈은 HTTP와 Response만 변환한다.
- 엔드포인트: GET /(채팅 페이지), GET /api/health, POST /api/ask {question, lang?} ->
  {answer, blocked, reason, lang, cache_hit, timings_ms, contexts[{chunk_id, text}]}.
  모델 원본 답변은 반환하지 않는다(요청 로그에만 남는다).
- 스레딩: 파이프라인을 단일 작업 스레드 안에서 만들고 모든 요청을 그 스레드에서 처리한다. 이유: SQLite
  연결(LLM 캐시)은 만든 스레드에서만 쓸 수 있고, GPU 하나는 한 번에 한 생성만 돌려야 한다. 그래서 요청은
  줄을 서고, 페이지는 "생각 중" 상태를 보여 준다.
- 단일 턴: 파이프라인에는 대화 기억이 없어 질문마다 독립적으로 답한다(페이지에도 표시). 서버는 기본으로
  127.0.0.1에만 열려 다른 컴퓨터에서 접근할 수 없다.
- 파이프라인은 팩토리로 받아 가짜 부품으로 CPU에서 앱을 테스트할 수 있게 한다.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

STATIC = Path(__file__).parent / "static"
MAX_BODY_CHARS = 10_000     # 요청 본문 상한 (파이프라인의 질문 길이 검사와 별개로 거대한 입력을 먼저 거른다)


class AskRequest(BaseModel):
    question: str = Field(max_length=MAX_BODY_CHARS)
    lang: str | None = Field(default=None, pattern="^(ko|en|de)$")


def create_app(build_pipeline: Callable[[], Any], chunks: list[dict[str, Any]], title: str = "bearing-rag-bench") -> FastAPI:
    by_id = {c["chunk_id"]: c for c in chunks}
    # max_workers=1: 파이프라인(캐시 연결·GPU 모델)을 소유하는 스레드는 하나뿐이다
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rag")
    state: dict[str, Any] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        loop = asyncio.get_running_loop()
        # 모델 로드와 인덱스 생성도 같은 스레드에서 한다 (끝나기 전에는 서버가 요청을 받지 않는다)
        state["pipe"] = await loop.run_in_executor(executor, build_pipeline)
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title=title, lifespan=lifespan)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "chat.html")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        pipe = state["pipe"]
        return {"ok": True, "config_id": pipe.config_id, "model": getattr(pipe.generator, "model_name", None),
                "prompt_version": pipe.prompt_version, "context_k": pipe.context_k}

    @app.post("/api/ask")
    async def ask(req: AskRequest) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(executor, lambda: state["pipe"].answer(req.question, lang=req.lang))
        return {
            "request_id": resp.request_id, "answer": resp.answer, "blocked": resp.blocked, "reason": resp.reason,
            "lang": resp.lang, "cache_hit": resp.cache_hit,
            "timings_ms": {k: round(v, 1) for k, v in resp.timings_ms.items()},
            # 인용 확인용: 프롬프트에 들어간 청크의 원문 (raw_answer는 의도적으로 내보내지 않는다)
            "contexts": [{"chunk_id": cid, "text": by_id[cid]["text"]} for cid in resp.context_ids if cid in by_id],
        }

    return app
