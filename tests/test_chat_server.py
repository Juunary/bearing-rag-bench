from fastapi.testclient import TestClient

from ragbench.cache import LLMCache
from ragbench.chat_server import create_app
from ragbench.pipeline import RAGPipeline
from ragbench.requestlog import RequestLogger
from tests.test_pipeline import CHUNKS, FakeGenerator, FakeRetriever


def make_client(tmp_path, text="Grease is semisolid [en_grease#2]."):
    gen = FakeGenerator(text)

    def build():
        # 앱의 작업 스레드 안에서 호출되어 SQLite 연결도 그 스레드가 소유한다
        return RAGPipeline(FakeRetriever(), CHUNKS, gen, LLMCache(tmp_path / "c.sqlite"), RequestLogger(tmp_path / "log.jsonl"),
                           context_k=3, config_id="t")
    return TestClient(create_app(build, CHUNKS)), gen


def test_health_and_page(tmp_path):
    with make_client(tmp_path)[0] as c:
        h = c.get("/api/health").json()
        assert h["ok"] and h["config_id"] == "t" and h["model"] == "fake"
        page = c.get("/")
        assert page.status_code == 200 and "bearing-rag-bench" in page.text


def test_ask_returns_answer_contexts_and_hides_raw_answer(tmp_path):
    client, gen = make_client(tmp_path)
    with client as c:
        r = c.post("/api/ask", json={"question": "What is grease?"}).json()
        assert r["answer"] == "Grease is semisolid [en_grease#2]." and not r["blocked"] and not r["cache_hit"]
        assert [x["chunk_id"] for x in r["contexts"]] == ["en_grease#2", "de_schmierfett#1", "ko_ball_bearing#4"]
        assert "raw_answer" not in r and r["lang"] == "en"
        again = c.post("/api/ask", json={"question": "What is grease?"}).json()      # 같은 질문은 캐시 히트
        assert again["cache_hit"] and gen.calls == 1


def test_blocked_answer_and_invalid_input(tmp_path):
    client, _ = make_client(tmp_path, text="Grease is semisolid [fake_id#9].")        # 프롬프트에 없던 ID 인용 -> 차단
    with client as c:
        r = c.post("/api/ask", json={"question": "What is grease?"}).json()
        assert r["blocked"] and "fake_id" not in r["answer"]
        empty = c.post("/api/ask", json={"question": "   "}).json()
        assert empty["blocked"] and empty["reason"] == "empty_question" and empty["contexts"] == []


def test_request_validation(tmp_path):
    with make_client(tmp_path)[0] as c:
        assert c.post("/api/ask", json={"question": "x", "lang": "fr"}).status_code == 422     # 지원하지 않는 언어
        assert c.post("/api/ask", json={"question": "x" * 10_001}).status_code == 422          # 본문 상한 초과
        assert c.post("/api/ask", json={}).status_code == 422
