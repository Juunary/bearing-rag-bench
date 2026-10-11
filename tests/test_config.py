import json

from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed


def test_config_roundtrip(tmp_path):
    cfg = ExperimentConfig(exp_id="t1", description="x")
    cfg.retrieval.method = "hybrid"
    cfg.retrieval.hnsw.m = 32
    p = tmp_path / "c.json"
    p.write_text(json.dumps(cfg.to_dict()), encoding="utf-8")
    back = ExperimentConfig.load(p)
    assert back == cfg
    assert back.retrieval.hnsw.m == 32


def test_partial_json_fills_defaults(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"exp_id": "t2", "retrieval": {"method": "dense"}}', encoding="utf-8")
    cfg = ExperimentConfig.load(p)
    assert cfg.retrieval.method == "dense"
    assert cfg.retrieval.top_k == 10
    assert cfg.chunking.size == 384


def test_result_roundtrip(tmp_path):
    cfg = ExperimentConfig(exp_id="t3")
    res = ExperimentResult(config=cfg.to_dict(), environment=environment_snapshot(),
                           metrics={"overall": {"recall@5": 1.0}}, per_query=[])
    path = res.save(tmp_path)
    assert path.name == "t3.json"
    back = ExperimentResult.load(path)
    assert back.exp_id == "t3"
    assert back.environment["packages"]["numpy"]


def test_set_seed_is_deterministic():
    import random
    import numpy as np
    set_seed(7); a = (random.random(), np.random.rand())
    set_seed(7); b = (random.random(), np.random.rand())
    assert a == b
