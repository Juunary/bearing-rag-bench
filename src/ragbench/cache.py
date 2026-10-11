"""Exact-match LLM response cache on SQLite.

[EN]
- Role: return the stored answer when the very same generation request was made before, instead of
  running the model again.
- Key = SHA-256 of a canonical JSON of (model name, model revision, chat messages, max_new_tokens,
  decoding mode). Anything that can change the output is in the key, so changing the prompt text,
  the retrieved context, the model revision or the length limit automatically misses the cache and
  an outdated answer is never served.
- Why SQLite (decided 2026-10-12): Python standard library (no dependency), safe for concurrent
  writers, survives restarts. A JSONL file would need a full read at start-up; a dict would be lost
  when the process ends.
- Valid only for deterministic decoding (greedy). With sampling the same key would legitimately
  produce different answers, so the key records the decoding mode and the generator uses greedy.
- Not a semantic cache: a differently worded question is a different key.

[KO]
- 역할: 똑같은 생성 요청이 전에 있었으면 모델을 다시 돌리지 않고 저장된 답을 돌려준다.
- 키 = (모델 이름, 모델 리비전, 채팅 메시지, max_new_tokens, 디코딩 방식)을 정규화한 JSON의 SHA-256.
  출력을 바꿀 수 있는 것은 모두 키에 들어 있어서, 프롬프트 문구·검색된 컨텍스트·모델 리비전·길이 제한이
  바뀌면 자동으로 캐시를 비껴가고 오래된 답이 나가지 않는다.
- SQLite를 쓰는 이유(2026-10-12 결정): 표준 라이브러리라 의존성이 없고, 동시 쓰기에 안전하며, 재시작
  후에도 남는다. JSONL은 시작할 때 전체를 읽어야 하고 dict는 프로세스가 끝나면 사라진다.
- 결정적 디코딩(greedy)에서만 유효하다. 샘플링이면 같은 키에도 답이 달라질 수 있어서 키에 디코딩
  방식을 넣고 생성기는 greedy만 쓴다.
- 의미 기반 캐시가 아니다: 표현이 다른 질문은 다른 키다.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


def make_key(model: str, revision: str | None, messages: list[dict[str, str]], max_new_tokens: int,
             decoding: str = "greedy") -> str:
    payload = {"model": model, "revision": revision, "messages": messages,
               "max_new_tokens": max_new_tokens, "decoding": decoding}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class LLMCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, "
                        "created_at REAL NOT NULL, hits INTEGER NOT NULL DEFAULT 0)")
        self.db.commit()
        self.hits = 0      # this process only
        self.misses = 0

    def get(self, key: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        self.db.execute("UPDATE cache SET hits = hits + 1 WHERE key = ?", (key,))
        self.db.commit()
        return json.loads(row[0])

    def put(self, key: str, value: dict[str, Any]) -> None:
        self.db.execute("INSERT OR REPLACE INTO cache (key, value, created_at, hits) VALUES (?, ?, ?, COALESCE((SELECT hits FROM cache WHERE key = ?), 0))",
                        (key, json.dumps(value, ensure_ascii=False), time.time(), key))
        self.db.commit()

    def __len__(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM cache").fetchone()[0])

    def close(self) -> None:
        self.db.close()
