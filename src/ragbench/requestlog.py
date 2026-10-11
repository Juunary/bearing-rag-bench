"""Append-only request log: one JSON object per line.

[EN]
- Role: record, for every request, what is needed to debug it or replay it later: the question, the
  retrieved chunks with scores, the exact prompt, the raw and the delivered answer, why an answer
  was blocked, whether the cache answered, latency per stage and token counts, plus the model,
  its revision and the prompt version.
- JSON Lines: appendable without rewriting, one line = one request, greppable and loadable with the
  standard library. Each line is flushed so a crash loses at most the request in flight.
- schema_version lets later readers handle format changes.
- Logs hold user questions and answers, so they stay out of git (logs/ is ignored).

[KO]
- 역할: 요청마다 디버깅과 재현에 필요한 것을 남긴다: 질문, 점수가 붙은 검색 청크, 정확한 프롬프트, 원본
  답변과 사용자에게 나간 답변, 차단 사유, 캐시가 답했는지, 단계별 지연, 토큰 수, 모델·리비전·프롬프트
  버전.
- JSON Lines: 다시 쓰지 않고 이어 붙일 수 있고, 한 줄이 요청 하나이며, grep과 표준 라이브러리로 읽을 수
  있다. 줄마다 flush해서 비정상 종료에도 처리 중이던 요청 하나만 잃는다.
- schema_version으로 이후 형식 변경을 처리한다.
- 로그에는 사용자 질문과 답이 들어 있으므로 git에서 제외한다(logs/는 무시됨).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class RequestLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: dict[str, Any]) -> None:
        line = {"schema_version": SCHEMA_VERSION, "ts": time.time(), **record}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            f.flush()

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
