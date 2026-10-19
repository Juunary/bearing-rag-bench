"""Chat server under concurrent requests: queueing, client-side latency and throughput.

[EN]
- Role: the server runs ONE request at a time (one GPU pipeline), so concurrent requests queue. This
  measures how that looks to clients. It starts experiments/serve_chat.py as a subprocess with an empty
  LLM cache and an empty translation cache (--cold-translation), then sends, over real HTTP:
  - 4 requests one after another (service time of a single request),
  - batches of 2, 4 and 8 requests fired at the same moment.
  Every question is different (taken from the 90-question set), so no request is a cache hit.
- Reported per level: wall time, requests per minute, client latency p50 / max, and the server-side time
  of each request, so queue wait = client latency - server time.
- Usage: uv run python experiments/bench_chat_concurrency.py configs/s35_pipeline.json [--port 8123]

[KO]
- 역할: 서버는 한 번에 요청 하나만 처리하므로(GPU 파이프라인 1개) 동시 요청은 줄을 선다. 이것이 클라이언트에게
  어떻게 보이는지 잰다. experiments/serve_chat.py를 하위 프로세스로 띄우고(빈 LLM 캐시, 빈 번역 캐시
  --cold-translation), 실제 HTTP로 다음을 보낸다:
  - 요청 4개를 차례로(요청 하나의 서비스 시간),
  - 2개, 4개, 8개를 같은 순간에 한꺼번에.
  질문은 모두 다르므로(90문항에서 선택) 캐시 히트가 없다.
- 레벨마다: 전체 시간, 분당 요청 수, 클라이언트 지연 p50 / 최대, 요청별 서버 처리 시간(대기 시간 = 클라이언트
  지연 - 서버 시간).
- 사용: uv run python experiments/bench_chat_concurrency.py configs/s35_pipeline.json [--port 8123]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.config import ExperimentConfig, environment_snapshot  # noqa: E402
from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402


def post(port: int, question: str) -> dict:
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/ask", data=json.dumps({"question": question}).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=600) as r:
        body = json.loads(r.read())
    return {"client_s": time.perf_counter() - t0, "server_s": body["timings_ms"]["total"] / 1000, "blocked": body["blocked"], "cache_hit": body["cache_hit"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--port", type=int, default=8123)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    questions = [q["question"] for q in load_queries(REPO / "eval" / "queries_v2.jsonl")]
    tmp = Path(tempfile.mkdtemp())
    log = open(tmp / "server.log", "w")
    t0 = time.perf_counter()
    srv = subprocess.Popen([sys.executable, str(REPO / "experiments" / "serve_chat.py"), str(args.config), "--port", str(args.port),
                            "--cache", str(tmp / "cache.sqlite"), "--cold-translation"], stdout=log, stderr=log, cwd=REPO)
    try:
        while True:                                   # 모델 로드가 끝나 health에 응답할 때까지
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{args.port}/api/health", timeout=2).read()
                break
            except Exception:
                if srv.poll() is not None:
                    raise SystemExit("server exited early; see " + str(tmp / "server.log"))
                time.sleep(3)
        startup = time.perf_counter() - t0
        cursor = 0
        levels = []

        def take(n: int) -> list[str]:
            nonlocal cursor
            qs = [questions[(cursor + i * 7) % len(questions)] for i in range(n)]      # 서로 다른 질문 (7칸 간격)
            cursor += 1 + n * 7
            return qs

        for name, conc, rounds in (("sequential x4", 1, 4), ("concurrent x2", 2, 1), ("concurrent x4", 4, 1), ("concurrent x8", 8, 1)):
            res, t_start = [], time.perf_counter()
            for _ in range(rounds):
                qs = take(conc)
                out: list = [None] * conc
                threads = [threading.Thread(target=lambda i=i, q=q: out.__setitem__(i, post(args.port, q))) for i, q in enumerate(qs)]
                [t.start() for t in threads]
                [t.join() for t in threads]
                res += out
            wall = time.perf_counter() - t_start
            lat = sorted(x["client_s"] for x in res)
            wait = [x["client_s"] - x["server_s"] for x in res]
            levels.append({"level": name, "requests": len(res), "wall_s": wall, "requests_per_minute": 60 * len(res) / wall,
                           "client_latency_s": {"p50": statistics.median(lat), "max": lat[-1]},
                           "server_time_s": {"p50": statistics.median(x["server_s"] for x in res)},
                           "queue_wait_s": {"p50": statistics.median(wait), "max": max(wait)},
                           "cache_hits": sum(x["cache_hit"] for x in res), "blocked": sum(x["blocked"] for x in res)})
            L = levels[-1]
            print(f"{name:14} n={L['requests']} wall {wall:6.1f}s  {L['requests_per_minute']:5.1f} req/min  client p50 {L['client_latency_s']['p50']:5.1f}s max {L['client_latency_s']['max']:5.1f}s  "
                  f"server p50 {L['server_time_s']['p50']:4.1f}s  queue wait p50 {L['queue_wait_s']['p50']:5.1f}s max {L['queue_wait_s']['max']:5.1f}s", flush=True)
        result = {"config": cfg.to_dict(), "environment": environment_snapshot(), "startup_s": startup, "levels": levels}
        path = REPO / "experiments" / "results" / f"bench_chat_{cfg.exp_id}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"server startup (model load) {startup:.0f}s; saved -> {path.relative_to(REPO)}")
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=30)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    main()
