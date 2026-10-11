"""Cross-encoder reranking on top of any retriever.

[EN]
- Role: take the base retriever's top `top_n` candidates, score each (query, chunk) pair with a
  cross-encoder, return the top k by that score.
- Why a cross-encoder after retrieval (book ch.12 reranking): bi-encoders embed query and chunk
  separately, so fine-grained term interaction is lost; a cross-encoder reads both together
  and is far more accurate but costs one forward pass per pair, hence only on a short list.
- Model (decided 2026-10-11): BAAI/bge-reranker-v2-m3 (Apache 2.0, multilingual, 568M).
  Output = single logit; higher is more relevant. fp16 on GPU, batched, max_length 512.
- top_n=30 default: the candidate list must contain the answer (recall of the base retriever)
  while staying cheap; the trade-off is reported via latency in the result file.

[KO]
- 역할: 기본 검색기의 상위 `top_n`개 후보를 (질의, 청크) 쌍으로 cross-encoder에 넣어 점수를 매기고
  그 점수로 상위 k개를 돌려준다.
- 검색 뒤에 cross-encoder를 두는 이유(책 12장 리랭킹): bi-encoder는 질의와 청크를 따로 임베딩해
  세밀한 단어 상호작용을 잃는다. cross-encoder는 둘을 함께 읽어 훨씬 정확하지만 쌍마다 forward pass가
  필요하므로 짧은 후보 목록에만 쓴다.
- 모델(2026-10-11 결정): BAAI/bge-reranker-v2-m3 (Apache 2.0, 다국어, 568M). 출력은 logit 하나,
  클수록 관련. GPU fp16, 배치, max_length 512.
- top_n=30 기본: 후보 목록에 정답이 들어 있어야 하고(기본 검색기의 recall) 동시에 싸야 한다.
  그 trade-off는 결과 파일의 지연 시간으로 보고한다.
"""

from __future__ import annotations

import time
from typing import Any

import torch

from ragbench.embedding import hf_cached_revision
from ragbench.retrieval.base import Hit


class CrossEncoder:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str | None = None,
                 batch_size: int = 16, max_length: int = 512, fp16: bool = True):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size, self.max_length = batch_size, max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if (fp16 and self.device == "cuda") else torch.float32
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, dtype=dtype).to(self.device).eval()
        self.revision = hf_cached_revision(model_name)

    @torch.no_grad()
    def score(self, query: str, texts: list[str]) -> list[float]:
        out: list[float] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            enc = self.tokenizer([query] * len(batch), batch, padding=True, truncation=True,
                                 max_length=self.max_length, return_tensors="pt").to(self.device)
            logits = self.model(**enc).logits.view(-1).float()
            out.extend(logits.cpu().tolist())
        return out


class RerankRetriever:
    def __init__(self, base, model_name: str = "BAAI/bge-reranker-v2-m3", top_n: int = 30,
                 cross_encoder: CrossEncoder | None = None):
        self.base = base
        self.top_n = top_n
        self.ce = cross_encoder or CrossEncoder(model_name)
        self.name = f"rerank({base.name})_{model_name.split('/')[-1]}_n{top_n}"
        self.chunk_text: dict[str, str] = {}
        self.last_base_ranks: dict[str, int] = {}

    def index(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        self.chunk_text = {c["chunk_id"]: c["text"] for c in chunks}
        stats = self.base.index(chunks)
        stats["reranker"] = {"model": self.ce.model_name, "revision": self.ce.revision, "top_n": self.top_n}
        return stats

    def search(self, query: str, k: int) -> list[Hit]:
        cands = self.base.search(query, self.top_n)
        self.last_base_ranks = {cid: r for r, (cid, _) in enumerate(cands, start=1)}
        if not cands:
            return []
        t0 = time.perf_counter()
        scores = self.ce.score(query, [self.chunk_text[cid] for cid, _ in cands])
        self.last_rerank_seconds = time.perf_counter() - t0
        order = sorted(zip((cid for cid, _ in cands), scores), key=lambda x: -x[1])
        return order[:k]
