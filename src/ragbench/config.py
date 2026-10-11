"""Experiment config / reproducibility / result container.

[EN]
- Role: one JSON config file == one experiment (ExperimentConfig); one JSON result file ==
  one run (ExperimentResult) holding config + environment snapshot + metrics + per-query output.
- Why: a result file must be self-describing. Anyone (or compare.py) can read it months later
  and know which code commit, package versions, model revision and seed produced each number.
- Choices:
  - JSON, not YAML: results are JSON already; stdlib only, one format for configs and logs.
  - Nested dataclasses (chunking / retrieval / generation) so compare.py can diff only the fields
    that changed between runs.
  - environment_snapshot() records git commit (+"-dirty" if uncommitted changes), tracked package
    versions, GPU name, UTC timestamp. "-dirty" flags numbers that cannot be reproduced from git.
  - set_seed() fixes random / numpy / torch. GPU kernels may still differ at float precision.
- Alternatives considered: Hydra/OmegaConf (more features, more magic), MLflow (server; overkill
  for a 2-day study).

[KO]
- 역할: 설정 JSON 1개 = 실험 1개(ExperimentConfig), 결과 JSON 1개 = 실행 1회(ExperimentResult).
  결과 파일에 설정·환경 스냅샷·지표·질의별 출력을 전부 담는다.
- 이유: 결과 파일이 코드 없이도 자기 설명이 되어야 한다. 나중에 어떤 커밋·패키지 버전·모델 리비전·
  시드에서 나온 숫자인지 파일만 보고 알 수 있게 한다.
- 선택:
  - YAML 대신 JSON: 결과도 JSON이라 형식 통일, 표준 라이브러리만 사용.
  - 중첩 dataclass(chunking/retrieval/generation): compare.py가 실험 간 달라진 필드만 뽑기 쉽다.
  - environment_snapshot(): git 커밋(미커밋 변경 시 "-dirty"), 추적 패키지 버전, GPU, UTC 시각.
    "-dirty"는 git으로 재현 불가능한 숫자임을 표시한다.
  - set_seed(): random/numpy/torch 고정. GPU 커널 차이로 소수점 차이는 남을 수 있다.
- 대안: Hydra/OmegaConf(기능 많지만 마법이 많음), MLflow(서버 필요, 2일짜리 실험엔 과함).
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
