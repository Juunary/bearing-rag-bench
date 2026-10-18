"""Write the fine-tuning and generation configs of the improvement round (v2 evaluation set).

[EN]
- Training: same recipe as stage 4 (rank 16, alpha 32, lr 2e-4, 3 epochs, effective batch 8) on
  data/sft_v2 (sources exclude every gold chunk of the 90-question set, training questions are not
  close to any of its questions). General set: QLoRA and LoRA with seeds 42, 43, 44. Cross-language-only
  set (data/sft_v2x, every question in a language other than its source chunk): seed 42 for both methods.
- Generation: prompt cite_v1, top-5 chunks of the RRF + reranker run on the 90 questions (v2_b_rrf_rerank),
  greedy. Conditions: base bf16, base 4-bit, the eight adapters. Retrieval-effect runs (base bf16 model,
  other retrieval results) are written by --retrieval NAME.
- Usage: uv run python scripts/make_v2_ft_configs.py [--retrieval v2_b_rrf_en_rerank ...]

[KO]
- 학습: 4단계와 같은 방식(rank 16, alpha 32, lr 2e-4, 3 epoch, 유효 배치 8)을 data/sft_v2(출처가 90문항의
  모든 정답 청크를 제외하고, 학습 질문이 어느 평가 질문과도 가깝지 않음)로 한다. 일반 세트: QLoRA와 LoRA를
  시드 42·43·44로. 교차 언어 전용 세트(data/sft_v2x, 모든 질문이 출처 청크와 다른 언어): 두 방식 모두 시드 42.
- 생성: 프롬프트 cite_v1, 90문항에 대한 RRF + 리랭커 결과(v2_b_rrf_rerank)의 상위 5개 청크, greedy. 조건:
  기반 bf16, 기반 4비트, 어댑터 8개. 검색 효과 실험(기반 bf16 모델, 다른 검색 결과)은 --retrieval 이름으로 쓴다.
- 사용: uv run python scripts/make_v2_ft_configs.py [--retrieval v2_b_rrf_en_rerank ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "configs" / "v2"
BASE = "Qwen/Qwen3-4B-Instruct-2507"
RET = {"method": "hybrid_rerank", "bm25_tokenizer": "kiwi", "embedding_model": "BAAI/bge-m3", "rrf_k": 60, "fusion_candidates": 50,
       "rerank_model": "BAAI/bge-reranker-v2-m3", "rerank_top_n": 30, "top_k": 10}
# (이름, 방법, 시드, 데이터 디렉터리, 학습 장치)
TRAIN = [("qlora_s42", "qlora", 42, "data/sft_v2", "cuda:0"), ("lora_s42", "lora", 42, "data/sft_v2", "cuda:0"),
         ("qlora_s44", "qlora", 44, "data/sft_v2", "cuda:0"), ("xlora_s42", "lora", 42, "data/sft_v2x", "cuda:0"),
         ("qlora_s43", "qlora", 43, "data/sft_v2", "cuda:1"), ("lora_s43", "lora", 43, "data/sft_v2", "cuda:1"),
         ("lora_s44", "lora", 44, "data/sft_v2", "cuda:1"), ("xqlora_s42", "qlora", 42, "data/sft_v2x", "cuda:1")]


def write(name: str, cfg: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gen_cfg(exp: str, desc: str, retrieval_result: str, device: str, quantize: bool = False, adapter: str | None = None) -> dict:
    g = {"model": BASE, "prompt_version": "cite_v1", "max_new_tokens": 256, "temperature": 0.0, "context_k": 5,
         "retrieval_result": retrieval_result, "device": device}
    if quantize:
        g["quantize_4bit"] = True
    if adapter:
        g["adapter"] = adapter
    return {"exp_id": exp, "stage": "v2g", "description": desc + " [eval: queries_v2, 90 questions]", "eval_path": "eval/queries_v2.jsonl",
            "retrieval": RET, "generation": g}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval", nargs="*", default=[], help="v2 retrieval result names to feed the base bf16 model")
    args = ap.parse_args()
    for name, method, seed, data, dev in TRAIN:
        exp = f"v2_{name}"
        write(exp, {"exp_id": exp, "stage": "v2t", "seed": seed,
                    "description": f"{method} fine-tuning of {BASE} for citation completeness on {data}: rank 16, alpha 32, lr 2e-4, 3 epochs, effective batch 8, seed {seed}",
                    "generation": {"model": BASE, "prompt_version": "cite_v1"},
                    "train": {"method": method, "rank": 16, "alpha": 32, "dropout": 0.05, "lr": 0.0002, "epochs": 3, "grad_accum": 8,
                              "train_file": f"{data}/train.jsonl", "val_file": f"{data}/val.jsonl", "device": dev}})
        write(f"v2g_{name}", gen_cfg(f"v2g_{name}", f"Generation with the {method} adapter {exp}", "v2_b_rrf_rerank", dev,
                                      quantize=(method == "qlora"), adapter=f"outputs/adapters/{exp}"))
    write("v2g_base_bf16", gen_cfg("v2g_base_bf16", "Generation, base bf16 model", "v2_b_rrf_rerank", "cuda:0"))
    write("v2g_base_4bit", gen_cfg("v2g_base_4bit", "Generation, base 4-bit model", "v2_b_rrf_rerank", "cuda:1", quantize=True))
    for r in args.retrieval:
        short = r.removeprefix("v2_")
        write(f"v2g_ret_{short}", gen_cfg(f"v2g_ret_{short}", f"Generation, base bf16 model, contexts from {r}", r, "cuda:1"))
    print("configs written to", OUT.relative_to(REPO))


if __name__ == "__main__":
    main()
