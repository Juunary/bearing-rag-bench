"""One request through the whole system: validate -> retrieve -> prompt -> cache/generate -> check -> log.

[EN]
- Role: the serving path. It composes the parts built in earlier stages and the operations parts of
  stage 3.5, and returns the text that may be shown to a user.
- Flow per request:
  1. validate the question (empty / too long -> fixed message, no retrieval, no model call).
  2. retrieve the top context_k chunks with the configured retriever.
  3. build the versioned prompt; look it up in the LLM cache; on a miss run the model and store it.
  4. validate the answer against the chunks that were in the prompt (validation.py). A blocked answer
     is replaced by a fixed message in the question's language.
  5. write one log line (requestlog.py) with everything needed to replay the request.
- Components are injected (retriever, generator, cache, logger), so the flow is unit-tested with
  fakes on CPU and run with the real models in experiments/run_pipeline.py.
- Latency is reported per stage in milliseconds: retrieve, generate (0 on a cache hit), total.
- The raw answer is always logged, even when it is blocked, so blocked cases can be reviewed.

[KO]
- 역할: 서비스 경로. 앞 단계에서 만든 부품과 3.5단계 운영 부품을 묶어 사용자에게 보여도 되는 텍스트를
  돌려준다.
- 요청당 흐름:
  1. 질문 검사(비었거나 너무 길면 고정 문구, 검색·모델 호출 없음).
  2. 설정된 검색기로 상위 context_k개 청크 검색.
  3. 버전이 붙은 프롬프트를 만들고 LLM 캐시를 조회, 미스면 모델을 돌려 저장.
  4. 프롬프트에 들어간 청크 기준으로 답변 검사(validation.py). 차단되면 질문 언어의 고정 문구로 교체.
  5. 요청을 재현하는 데 필요한 모든 것을 로그 한 줄로 기록(requestlog.py).
- 부품을 주입(검색기, 생성기, 캐시, 로거)하므로 흐름은 CPU에서 가짜 부품으로 단위 테스트하고 실제
  모델로는 experiments/run_pipeline.py에서 돌린다.
- 지연은 단계별 ms로 보고한다: retrieve, generate(캐시 히트면 0), total.
- 차단되어도 원본 답변은 항상 로그에 남겨 차단 사례를 검토할 수 있게 한다.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ragbench.cache import LLMCache, make_key
from ragbench.generation import build_messages
from ragbench.requestlog import RequestLogger
from ragbench.validation import INVALID_INPUT_MESSAGES, SAFE_MESSAGES, guess_lang, validate_answer, validate_question


@dataclass
class Response:
    request_id: str
    answer: str                       # text that may be shown to the user
    raw_answer: str | None            # what the model produced (None if no model call was needed)
    blocked: bool
    reason: str | None
    lang: str
    context_ids: list[str] = field(default_factory=list)
    cache_hit: bool = False
    timings_ms: dict[str, float] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0


class RAGPipeline:
    def __init__(self, retriever, chunks: list[dict[str, Any]], generator, cache: LLMCache, logger: RequestLogger,
                 prompt_version: str = "cite_refuse_v1", context_k: int = 5, max_new_tokens: int = 256,
                 config_id: str | None = None):
        self.retriever, self.generator, self.cache, self.logger = retriever, generator, cache, logger
        self.by_id = {c["chunk_id"]: c for c in chunks}
        self.prompt_version, self.context_k, self.max_new_tokens = prompt_version, context_k, max_new_tokens
        self.config_id = config_id

    def answer(self, question: str, lang: str | None = None, request_id: str | None = None) -> Response:
        t_start = time.perf_counter()
        request_id = request_id or uuid.uuid4().hex[:12]
        lang = lang or guess_lang(question or "")
        verdict, cleaned = validate_question(question)
        if not verdict.ok:
            resp = Response(request_id, INVALID_INPUT_MESSAGES.get(lang, INVALID_INPUT_MESSAGES["en"]), None, True,
                            verdict.reason, lang, timings_ms={"total": (time.perf_counter() - t_start) * 1000})
            self._log(resp, question, [], None)
            return resp

        t0 = time.perf_counter()
        hits = self.retriever.search(cleaned, self.context_k)
        retrieve_ms = (time.perf_counter() - t0) * 1000
        ctx = [(cid, score) for cid, score in hits[: self.context_k]]
        context_ids = [cid for cid, _ in ctx]
        messages = build_messages(self.prompt_version, cleaned, [self.by_id[i] for i in context_ids])

        key = make_key(self.generator.model_name, self.generator.revision, messages, self.max_new_tokens)
        cached = self.cache.get(key)
        cache_hit = cached is not None
        generate_ms = 0.0
        if cache_hit:
            out = cached
        else:
            t1 = time.perf_counter()
            out = self.generator.generate(messages, max_new_tokens=self.max_new_tokens)
            generate_ms = (time.perf_counter() - t1) * 1000
            self.cache.put(key, out)

        verdict_out = validate_answer(out["text"], context_ids)
        shown = out["text"] if verdict_out.ok else SAFE_MESSAGES.get(lang, SAFE_MESSAGES["en"])
        resp = Response(
            request_id, shown, out["text"], not verdict_out.ok, verdict_out.reason, lang, context_ids, cache_hit,
            {"retrieve": retrieve_ms, "generate": generate_ms, "total": (time.perf_counter() - t_start) * 1000},
            out["prompt_tokens"], out["completion_tokens"])
        self._log(resp, question, ctx, messages)
        return resp

    def _log(self, resp: Response, question: str, ctx: list[tuple[str, float]], messages) -> None:
        self.logger.log({
            "request_id": resp.request_id, "config_id": self.config_id, "question": question, "lang": resp.lang,
            "retrieved": [{"chunk_id": c, "score": round(float(s), 4)} for c, s in ctx],
            "prompt": messages, "prompt_version": self.prompt_version,
            "model": getattr(self.generator, "model_name", None), "model_revision": getattr(self.generator, "revision", None),
            "raw_answer": resp.raw_answer, "answer": resp.answer, "blocked": resp.blocked, "block_reason": resp.reason,
            "cache_hit": resp.cache_hit, "latency_ms": {k: round(v, 2) for k, v in resp.timings_ms.items()},
            "prompt_tokens": resp.prompt_tokens, "completion_tokens": resp.completion_tokens,
        })
