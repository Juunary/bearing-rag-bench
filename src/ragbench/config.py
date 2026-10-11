"""Experiment configuration, reproducibility helpers and result container.

Every experiment is described by one JSON file (configs/*.json) that maps 1:1 onto
``ExperimentConfig``. Every run writes one JSON file (experiments/results/<exp_id>.json)
that contains the full config, an environment snapshot, aggregate metrics and the
per-query outputs, so a result file is self-describing without the code that made it.
"""

from __future__ import annotations

import dataclasses
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# Packages whose versions are recorded in every result file (only those installed).
TRACKED_PACKAGES = (
    "numpy", "torch", "transformers", "sentence-transformers", "bm25s", "kiwipiepy",
    "hnswlib", "pymupdf", "vllm",
)


# --------------------------------------------------------------------------- config


@dataclass
class ChunkingConfig:
    strategy: str = "fixed"        # "fixed" | "structure"
    unit: str = "token"            # "token" | "char"
    size: int = 384
    overlap: int = 48
    tokenizer: str = "BAAI/bge-m3"  # tokenizer used to count tokens when unit == "token"


@dataclass
class HNSWConfig:
    m: int = 16
    ef_construction: int = 128
    ef_search: int = 64


@dataclass
class RetrievalConfig:
    method: str = "bm25"           # "bm25" | "dense" | "hybrid" | "hybrid_rerank"
    top_k: int = 10                # how many results are kept for metrics
    bm25_tokenizer: str = "whitespace"   # "whitespace" | "char_bigram" | "kiwi" | "subword" | "snowball"
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    embedding_model: str = "BAAI/bge-m3"
    embedding_revision: str | None = None   # HF commit hash, filled in at run time if None
    hnsw: HNSWConfig = field(default_factory=HNSWConfig)
    exact_search: bool = False     # True -> brute-force numpy instead of HNSW (ground truth)
    rrf_k: int = 60
    fusion_candidates: int = 50    # per-retriever candidates fed into RRF
    rerank_model: str | None = None
    rerank_top_n: int = 30         # how many fused candidates go to the reranker


@dataclass
class GenerationConfig:
    model: str | None = None
    prompt_version: str | None = None
    max_new_tokens: int = 512
    temperature: float = 0.0


@dataclass
class ExperimentConfig:
    exp_id: str
    stage: str = "s1"
    description: str = ""
    seed: int = 42
    languages: list[str] = field(default_factory=lambda: ["ko", "en", "de"])
    eval_path: str = "eval/queries.jsonl"
    anchor_min_overlap: float = 0.5   # fraction of an anchor sentence a chunk must contain
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    # -- (de)serialisation -------------------------------------------------
    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ExperimentConfig":
        d = dict(d)
        d["chunking"] = ChunkingConfig(**d.get("chunking", {}))
        r = dict(d.get("retrieval", {}))
        r["hnsw"] = HNSWConfig(**r.get("hnsw", {}))
        d["retrieval"] = RetrievalConfig(**r)
        d["generation"] = GenerationConfig(**d.get("generation", {}))
        return cls(**d)

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentConfig":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# --------------------------------------------------------------- reproducibility


def set_seed(seed: int) -> None:
    """Fix every RNG we might touch. torch is optional at this stage."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


def environment_snapshot() -> dict[str, Any]:
    """Everything needed to answer 'which code / libs / hardware produced this number?'."""
    pkgs = {}
    for name in TRACKED_PACKAGES:
        try:
            pkgs[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    gpu = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "gpu": gpu,
        "packages": pkgs,
    }


# --------------------------------------------------------------------------- result


@dataclass
class ExperimentResult:
    config: dict[str, Any]
    environment: dict[str, Any]
    metrics: dict[str, Any]            # {"overall": {...}, "by_group": {"ko->en": {...}, ...}}
    per_query: list[dict[str, Any]]    # one entry per query: qid, ranked ids, scores, metric values
    timing: dict[str, Any] = field(default_factory=dict)   # index build, per-query latency, etc.
    extra: dict[str, Any] = field(default_factory=dict)    # anything method-specific (index size, ...)

    @property
    def exp_id(self) -> str:
        return self.config["exp_id"]

    def save(self, results_dir: str | Path = REPO_ROOT / "experiments" / "results") -> Path:
        results_dir = Path(results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        path = results_dir / f"{self.exp_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dataclasses.asdict(self), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentResult":
        with open(path, encoding="utf-8") as f:
            return cls(**json.load(f))
