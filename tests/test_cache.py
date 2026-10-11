from ragbench.cache import LLMCache, make_key

MSG = [{"role": "system", "content": "s"}, {"role": "user", "content": "q"}]


def test_key_is_stable_and_sensitive():
    k = make_key("m", "r1", MSG, 256)
    assert k == make_key("m", "r1", [dict(x) for x in MSG], 256)
    assert k != make_key("m", "r2", MSG, 256)                       # model revision
    assert k != make_key("m", "r1", MSG, 128)                       # length limit
    assert k != make_key("m", "r1", MSG[:1] + [{"role": "user", "content": "q2"}], 256)   # prompt
    assert k != make_key("m", "r1", MSG, 256, decoding="sample")    # decoding mode
    assert len(k) == 64


def test_hit_miss_counters_and_roundtrip():
    c = LLMCache(":memory:")
    k = make_key("m", "r", MSG, 10)
    assert c.get(k) is None and c.misses == 1
    c.put(k, {"text": "한글 answer", "completion_tokens": 3})
    assert c.get(k) == {"text": "한글 answer", "completion_tokens": 3} and c.hits == 1
    assert len(c) == 1


def test_persistence_across_instances(tmp_path):
    p = tmp_path / "c.sqlite"
    a = LLMCache(p); a.put("k", {"v": 1}); a.close()
    b = LLMCache(p)
    assert b.get("k") == {"v": 1}
    b.put("k", {"v": 2})
    assert b.get("k") == {"v": 2}
