"""Dense embeddings with plain transformers (no sentence-transformers), cached on disk.

[EN]
- Role: text -> L2-normalised float32 vector. Used for chunks (index) and queries (search).
- Model: BAAI/bge-m3 dense head = CLS token of the last hidden layer, L2-normalised; cosine
  similarity is then a plain dot product. No query instruction prefix is needed for bge-m3.
- Other models (model swap experiment, 2026-11): `pooling` "cls" | "last" (Qwen3-Embedding: last non-pad
  token) | "mean" (EmbeddingGemma 2: mean over attended tokens, prompt included); `query_prefix` /
  `doc_prefix` are prepended verbatim (Qwen3: "Instruct: ...\nQuery:", Gemma: "task: search result | query: "
  and "title: none | text: "); `dtype` "fp16" | "bf16" | "fp32". The cache key includes pooling and prefix
  when they differ from the bge-m3 defaults, so older caches stay valid.
- Why plain transformers (decided 2026-10-11): the pooling and normalisation are 5 visible
  lines instead of a library config file. fp16 on GPU, batch encode, max_length 512 (chunks
  are <= 384 tokens + special tokens).
- Cache: chunk embeddings are stored under data/processed/emb_<key>.npz keyed by model name,
  model revision, chunk set id and max_length, so BM25/hybrid/HNSW experiments never re-embed.
- Model revision (HF commit hash) is recorded for the result file.

[KO]
- 역할: 텍스트 -> L2 정규화된 float32 벡터. 청크(인덱스)와 질의(검색)에 같이 쓴다.
- 모델: BAAI/bge-m3 dense = 마지막 은닉층의 CLS 토큰을 L2 정규화. 이후 코사인 유사도는 단순 내적이다.
  bge-m3는 질의 지시문 접두사가 필요 없다.
- 다른 모델(모델 교체 실험, 2026-11): `pooling` "cls" | "last"(Qwen3-Embedding: 마지막 비패딩 토큰) | "mean"(EmbeddingGemma 2:
  어텐션 토큰 평균, 프롬프트 포함); `query_prefix`/`doc_prefix`는 그대로 앞에 붙인다; `dtype` "fp16" | "bf16" | "fp32".
  캐시 키는 풀링·접두사가 bge-m3 기본값과 다를 때만 그 값을 포함해 기존 캐시가 그대로 유효하다.
- transformers 직접 사용 이유(2026-10-11 결정): 풀링·정규화가 라이브러리 설정 파일이 아니라 코드 5줄로
  보인다. GPU fp16, 배치 인코딩, max_length 512(청크는 384토큰 + 특수 토큰 이하).
- 캐시: 청크 임베딩을 data/processed/emb_<key>.npz에 저장. 키 = 모델명·리비전·청크 세트 ID·max_length.
  BM25/하이브리드/HNSW 실험에서 다시 임베딩하지 않는다.
- 모델 리비전(HF 커밋 해시)을 결과 파일용으로 기록한다.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

from ragbench.ingest import REPO

PROCESSED = REPO / "data" / "processed"


def hf_cached_revision(model_name: str) -> str | None:
    """Commit hash of the locally cached snapshot (transformers 5 no longer exposes _commit_hash)."""
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
        ref = Path(HF_HUB_CACHE) / f"models--{model_name.replace('/', '--')}" / "refs" / "main"
        return ref.read_text().strip() if ref.exists() else None
    except Exception:   # noqa: BLE001 - revision is informational only
        return None


_DTYPES = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}


def pool(hidden: torch.Tensor, mask: torch.Tensor, pooling: str) -> torch.Tensor:
    """(B, T, H) + attention mask -> (B, H): CLS token, last attended token, or mean over attended tokens."""
    if pooling == "cls":
        return hidden[:, 0]
    if pooling == "last":
        # 왼쪽 패딩이면 마지막 열, 오른쪽 패딩이면 각 행의 마지막 비패딩 위치 (Qwen3-Embedding 모델 카드와 같은 규칙)
        if bool(mask[:, -1].all()):
            return hidden[:, -1]
        idx = mask.sum(dim=1) - 1
        return hidden[torch.arange(hidden.shape[0], device=hidden.device), idx]
    if pooling == "mean":
        m = mask.unsqueeze(-1).to(hidden.dtype)
        return (hidden * m).sum(dim=1) / m.sum(dim=1).clamp(min=1.0)
    raise ValueError(f"pooling must be cls, last or mean, got {pooling!r}")


class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str | None = None,
                 batch_size: int = 32, max_length: int = 512, fp16: bool = True, pooling: str = "cls",
                 query_prefix: str = "", doc_prefix: str = "", dtype: str | None = None):
        from transformers import AutoModel, AutoTokenizer
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size, self.max_length = batch_size, max_length
        self.pooling, self.query_prefix, self.doc_prefix = pooling, query_prefix, doc_prefix
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # dtype 인자가 없으면 예전 규칙(GPU면 fp16) 그대로라 bge-m3 결과가 바뀌지 않는다
        torch_dtype = _DTYPES[dtype] if dtype else (torch.float16 if (fp16 and self.device == "cuda") else torch.float32)
        if self.device == "cpu":
            torch_dtype = torch.float32
        self.model = AutoModel.from_pretrained(model_name, dtype=torch_dtype).to(self.device).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or hf_cached_revision(model_name)
        # 출력 차원은 설정값을 믿지 않고 한 번 인코딩해서 잰다 (EmbeddingGemma 2는 텍스트 hidden_size와 출력 차원이 다르다)
        self.dim = int(self._raw_encode(["dimension probe"]).shape[1])

    @torch.no_grad()
    def _raw_encode(self, batch: list[str]) -> torch.Tensor:
        enc = self.tokenizer(batch, padding=True, truncation=True, max_length=self.max_length,
                             return_tensors="pt").to(self.device)
        hidden = self.model(**enc).last_hidden_state      # (B, T, H)
        vec = pool(hidden, enc["attention_mask"], self.pooling)
        return torch.nn.functional.normalize(vec.float(), p=2, dim=1)

    def _encode(self, texts: list[str]) -> np.ndarray:
        out = np.empty((len(texts), self.dim), dtype=np.float32)
        for i in range(0, len(texts), self.batch_size):
            out[i:i + len(texts[i:i + self.batch_size])] = self._raw_encode(texts[i:i + self.batch_size]).cpu().numpy()
        return out

    def encode(self, texts: list[str]) -> np.ndarray:
        """Document side (chunks): doc_prefix + text."""
        return self._encode([self.doc_prefix + t for t in texts])

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        """Query side: query_prefix + text (identical to encode() for bge-m3, whose prefixes are empty)."""
        return self._encode([self.query_prefix + t for t in texts])

    # ---------------------------------------------------------------- cache
    def cache_key(self, chunk_set_id: str) -> str:
        raw = f"{self.model_name}|{self.revision}|{chunk_set_id}|{self.max_length}"
        if self.pooling != "cls" or self.doc_prefix:
            raw += f"|{self.pooling}|{self.doc_prefix}"         # bge-m3 기본값이면 예전 키 그대로
        return hashlib.sha1(raw.encode()).hexdigest()[:12]

    def encode_chunks_cached(self, chunks: list[dict], chunk_set_id: str) -> tuple[np.ndarray, dict]:
        """Embeddings for chunks in the given order; (re)computed only if the cache is missing."""
        path = PROCESSED / f"emb_{self.cache_key(chunk_set_id)}.npz"
        ids = [c["chunk_id"] for c in chunks]
        if path.exists():
            z = np.load(path, allow_pickle=False)
            if list(z["ids"]) == ids:
                return z["emb"], {"cached": True, "path": str(path.relative_to(REPO)), "encode_seconds": 0.0}
        t0 = time.perf_counter()
        emb = self.encode([c["text"] for c in chunks])
        secs = time.perf_counter() - t0
        np.savez(path, emb=emb, ids=np.array(ids))
        meta = {"model": self.model_name, "revision": self.revision, "chunk_set_id": chunk_set_id,
                "max_length": self.max_length, "n": len(ids), "encode_seconds": secs}
        path.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        return emb, {"cached": False, "path": str(path.relative_to(REPO)), "encode_seconds": secs}
