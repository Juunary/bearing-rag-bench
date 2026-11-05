import json

import numpy as np
import pytest
import torch

from ragbench.config import ExperimentConfig
from ragbench.embedding import pool
from ragbench.retrieval.rerank import QWEN3_RERANK_INSTRUCTION, qwen3_rerank_text


def test_pooling_rules():
    h = torch.tensor([[[1.0, 0.0], [0.0, 1.0], [5.0, 5.0]], [[2.0, 0.0], [9.0, 9.0], [9.0, 9.0]]])
    right = torch.tensor([[1, 1, 1], [1, 0, 0]])            # 오른쪽 패딩: 둘째 행은 첫 토큰만 유효
    assert pool(h, right, "cls").tolist() == [[1.0, 0.0], [2.0, 0.0]]
    assert pool(h, right, "last").tolist() == [[5.0, 5.0], [2.0, 0.0]]
    assert pool(h, right, "mean").tolist() == [[2.0, 2.0], [2.0, 0.0]]
    left = torch.tensor([[1, 1, 1], [0, 0, 1]])             # 왼쪽 패딩: 마지막 열이 항상 마지막 토큰
    assert pool(h, left, "last").tolist() == [[5.0, 5.0], [9.0, 9.0]]
    with pytest.raises(ValueError):
        pool(h, right, "max")


def test_qwen3_rerank_prompt_uses_card_format_and_default_instruction():
    t = qwen3_rerank_text("oil seal leak", "The sealing lip runs on the shaft.")
    assert t.startswith(f"<Instruct>: {QWEN3_RERANK_INSTRUCTION}\n<Query>: oil seal leak\n<Document>: The sealing")
    assert "<Instruct>: custom" in qwen3_rerank_text("q", "d", "custom")


def test_config_roundtrip_keeps_model_swap_fields(tmp_path):
    cfg = ExperimentConfig(exp_id="t")
    cfg.retrieval.embedding_pooling, cfg.retrieval.embedding_query_prefix, cfg.retrieval.embedding_dtype = "last", "Instruct: x\nQuery:", "bf16"
    cfg.retrieval.rerank_kind, cfg.retrieval.rerank_device = "qwen3", "cuda:1"
    p = tmp_path / "c.json"
    p.write_text(json.dumps(cfg.to_dict()), encoding="utf-8")
    assert ExperimentConfig.load(p) == cfg


def test_factory_keeps_default_embedder_and_cross_encoder(monkeypatch):
    from ragbench.retrieval import factory
    plain = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "dense"}})
    assert factory._embedder(plain) is None                 # bge-m3 기본값: DenseRetriever가 예전처럼 임베더를 만든다
    made = {}
    monkeypatch.setattr("ragbench.embedding.Embedder", lambda name, **kw: made.update(name=name, **kw) or "emb")
    swapped = ExperimentConfig.from_dict({"exp_id": "t", "retrieval": {"method": "dense", "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
                                                                       "embedding_pooling": "last", "embedding_dtype": "bf16"}})
    assert factory._embedder(swapped) == "emb" and made["pooling"] == "last" and made["dtype"] == "bf16"


def test_encode_queries_adds_prefix_only_on_the_query_side():
    from ragbench.embedding import Embedder

    class Stub(Embedder):
        def __init__(self):
            self.query_prefix, self.doc_prefix, self.seen = "Q: ", "D: ", []

        def _encode(self, texts):
            self.seen.append(texts)
            return np.zeros((len(texts), 2), dtype=np.float32)

    e = Stub()
    e.encode(["a"]); e.encode_queries(["b"])
    assert e.seen == [["D: a"], ["Q: b"]]
