from ragbench.requestlog import SCHEMA_VERSION, RequestLogger


def test_append_and_read(tmp_path):
    lg = RequestLogger(tmp_path / "sub" / "r.jsonl")
    lg.log({"request_id": "a", "question": "한글?"})
    lg.log({"request_id": "b", "blocked": True})
    rows = lg.read()
    assert [r["request_id"] for r in rows] == ["a", "b"]
    assert rows[0]["schema_version"] == SCHEMA_VERSION and rows[0]["question"] == "한글?" and rows[0]["ts"] > 0
    assert len((tmp_path / "sub" / "r.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_new_instance_appends(tmp_path):
    p = tmp_path / "r.jsonl"
    RequestLogger(p).log({"i": 1}); RequestLogger(p).log({"i": 2})
    assert [r["i"] for r in RequestLogger(p).read()] == [1, 2]
