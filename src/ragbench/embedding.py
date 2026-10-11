"""Dense embeddings with plain transformers (no sentence-transformers), cached on disk.

[EN]
- Role: text -> L2-normalised float32 vector. Used for chunks (index) and queries (search).
- Model: BAAI/bge-m3 dense head = CLS token of the last hidden layer, L2-normalised; cosine
  similarity is then a plain dot product. No query instruction prefix is needed for bge-m3.
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


class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str | None = None,
                 batch_size: int = 32, max_length: int = 512, fp16: bool = True):
        from transformers import AutoModel, AutoTokenizer
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size, self.max_length = batch_size, max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if (fp16 and self.device == "cuda") else torch.float32
        self.model = AutoModel.from_pretrained(model_name, dtype=dtype).to(self.device).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or hf_cached_revision(model_name)
        self.dim = self.model.config.hidden_size

    @torch.no_grad()
    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.empty((len(texts), self.dim), dtype=np.float32)
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            enc = self.tokenizer(batch, padding=True, truncation=True, max_length=self.max_length,
                                 return_tensors="pt").to(self.device)
            hidden = self.model(**enc).last_hidden_state      # (B, T, H)
            cls = hidden[:, 0]                                 # CLS pooling (bge-m3 dense)
            cls = torch.nn.functional.normalize(cls.float(), p=2, dim=1)
            out[i:i + len(batch)] = cls.cpu().numpy()
        return out

    # ---------------------------------------------------------------- cache
    def cache_key(self, chunk_set_id: str) -> str:
        raw = f"{self.model_name}|{self.revision}|{chunk_set_id}|{self.max_length}"
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
