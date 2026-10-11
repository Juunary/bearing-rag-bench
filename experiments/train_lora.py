"""LoRA / QLoRA fine-tuning with a hand-written training loop (no trainer framework).

[EN]
- Role: train a low-rank adapter on data/sft/train.jsonl so the model completes citations, and record
  the cost (GPU memory, time) and the loss curve next to the adapter.
- Methods (train.method):
  - lora: base weights in bf16 (frozen), adapter in fp32 (peft default for bf16 bases).
  - qlora: base weights quantised to 4-bit NF4 with double quantisation, bf16 compute; the adapter
    is trained on top of the quantised weights (Dettmers et al., 2023).
  Everything else is identical between the two, so differences come from the precision of the base.
- Adapter: rank r, alpha = 2r, dropout 0.05, on all attention and MLP projections (q,k,v,o,gate,up,
  down). All linear layers rather than attention only because the QLoRA paper found that matching
  full fine-tuning quality needs them; the added parameters stay below 1% of the model (33.0M at r=16).
- Optimisation: AdamW, lr 2e-4, no weight decay, linear warm-up (5% of steps) then cosine decay to 0,
  gradient clipping 1.0, batch size 1 with gradient accumulation 8 (effective batch 8; sequences are
  ~2.3k tokens), 3 epochs, gradient checkpointing. These are common defaults and were NOT tuned.
- Loss: answer tokens only (src/ragbench/sft.py). Validation loss on data/sft/val.jsonl before
  training and after every epoch; it only monitors fitting, the real test is the 45 evaluation
  questions (run_generation.py with the adapter).
- Output: outputs/adapters/<exp_id>/ (git-ignored) and experiments/results/<exp_id>.json.
- Usage: uv run python experiments/train_lora.py configs/s4_qlora_r16.json

[KO]
- 역할: data/sft/train.jsonl로 저랭크 어댑터를 학습해 모델이 인용을 끝까지 달게 하고, 비용(GPU 메모리, 시간)과
  손실 곡선을 어댑터 옆에 기록한다.
- 방식(train.method):
  - lora: 기반 가중치는 bf16으로 고정, 어댑터는 fp32(bf16 기반에서 peft 기본값).
  - qlora: 기반 가중치를 이중 양자화한 4비트 NF4로 두고 bf16으로 계산하며, 양자화된 가중치 위에서 어댑터를
    학습한다(Dettmers 외, 2023).
  나머지는 두 방식이 모두 같아서, 차이는 기반 정밀도에서만 나온다.
- 어댑터: rank r, alpha = 2r, dropout 0.05, 모든 어텐션·MLP 투영(q,k,v,o,gate,up,down). 어텐션만이 아니라
  모든 선형층을 쓰는 이유는 QLoRA 논문에서 전체 파인튜닝 품질에 맞추려면 필요하다고 보고했기 때문이며,
  추가 파라미터는 모델의 1% 미만이다(r=16에서 33.0M).
- 최적화: AdamW, lr 2e-4, 가중치 감쇠 없음, 5% 선형 워밍업 후 코사인 감쇠, 그레이디언트 클리핑 1.0, 배치 1에
  누적 8(유효 배치 8; 시퀀스가 약 2.3k토큰), 3 epoch, 그레이디언트 체크포인팅. 일반적인 기본값이며 튜닝하지
  않았다.
- 손실: 답변 토큰만(src/ragbench/sft.py). 검증 손실은 학습 전과 epoch마다 data/sft/val.jsonl로 잰다. 적합
  여부를 감시할 뿐이고 진짜 시험은 평가 질문 45개다(어댑터를 붙인 run_generation.py).
- 출력: outputs/adapters/<exp_id>/(git 제외)와 experiments/results/<exp_id>.json.
- 사용: uv run python experiments/train_lora.py configs/s4_qlora_r16.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # noqa: E402

from ragbench.config import ExperimentConfig, ExperimentResult, environment_snapshot, set_seed  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.sft import encode_example, example_stats  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    t = cfg.train
    base = cfg.generation.model
    env = environment_snapshot()
    set_seed(cfg.seed)
    device = torch.device(t.device)

    tok = AutoTokenizer.from_pretrained(base)
    train = [encode_example(tok, ex["messages"], ex["answer"]) for ex in read_jsonl(REPO / t.train_file)]
    val = [encode_example(tok, ex["messages"], ex["answer"]) for ex in read_jsonl(REPO / t.val_file)]
    print("train", example_stats(train), "| val", example_stats(val), flush=True)

    t0_load = time.perf_counter()
    if t.method == "qlora":
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
        model = AutoModelForCausalLM.from_pretrained(base, quantization_config=bnb, device_map={"": device.index or 0})
    elif t.method == "lora":
        model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16).to(device)
    else:
        raise ValueError(f"unknown method {t.method!r}")
    base_gib = torch.cuda.memory_allocated(device) / 2**30
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(r=t.rank, lora_alpha=t.alpha, lora_dropout=t.dropout, target_modules=t.target_modules, bias="none", task_type="CAUSAL_LM"))
    model.train()           # gradient checkpointing only runs in training mode
    params = [p for p in model.parameters() if p.requires_grad]
    n_trainable = sum(p.numel() for p in params)
    print(f"method={t.method} base loaded in {time.perf_counter() - t0_load:.0f}s, {base_gib:.1f} GiB, trainable {n_trainable / 1e6:.1f}M", flush=True)

    def example_loss(ids: list[int], r: int) -> torch.Tensor:
        x = torch.tensor([ids], device=device)
        logits = model(input_ids=x, logits_to_keep=r + 1).logits[0]      # only the answer positions (+1)
        return F.cross_entropy(logits[:-1].float(), x[0, -r:], reduction="mean")

    @torch.no_grad()
    def val_loss() -> float:
        model.eval()
        tot, n = 0.0, 0
        for ids, r in val:
            tot += example_loss(ids, r).item() * r
            n += r
        model.train()
        return tot / n

    opt = torch.optim.AdamW(params, lr=t.lr, betas=(0.9, 0.999), weight_decay=0.0)
    steps_per_epoch = math.ceil(len(train) / t.grad_accum)
    total = steps_per_epoch * t.epochs
    warm = max(1, int(total * t.warmup_ratio))
    lr_at = lambda s: t.lr * (s + 1) / warm if s < warm else t.lr * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm)))

    val_curve = {"before": val_loss()}
    print(f"val loss before training: {val_curve['before']:.4f}", flush=True)
    torch.cuda.reset_peak_memory_stats(device)
    rng = random.Random(cfg.seed)
    step, step_losses, tokens_seen = 0, [], 0
    t_train = time.perf_counter()
    for epoch in range(1, t.epochs + 1):
        order = list(range(len(train)))
        rng.shuffle(order)
        for start in range(0, len(order), t.grad_accum):
            window = order[start:start + t.grad_accum]
            acc = 0.0
            for i in window:
                ids, r = train[i]
                loss = example_loss(ids, r) / len(window)
                loss.backward()
                acc += loss.item()
                tokens_seen += len(ids)
            torch.nn.utils.clip_grad_norm_(params, t.max_grad_norm)
            for g in opt.param_groups:
                g["lr"] = lr_at(step)
            opt.step(); opt.zero_grad(set_to_none=True)
            step_losses.append(acc)
            step += 1
            if step % 5 == 0 or step == total:
                print(f"epoch {epoch} step {step}/{total} lr {lr_at(step - 1):.2e} loss {acc:.4f} elapsed {time.perf_counter() - t_train:.0f}s", flush=True)
        val_curve[f"epoch_{epoch}"] = val_loss()
        print(f"epoch {epoch} val loss {val_curve[f'epoch_{epoch}']:.4f}", flush=True)
    train_seconds = time.perf_counter() - t_train
    peak_gib = torch.cuda.max_memory_allocated(device) / 2**30

    out_dir = REPO / "outputs" / "adapters" / cfg.exp_id
    model.save_pretrained(out_dir)
    adapter_mb = sum(f.stat().st_size for f in out_dir.iterdir()) / 2**20
    result = ExperimentResult(
        config=cfg.to_dict(), environment=env,
        metrics={"overall": {"train_loss_first_step": step_losses[0], "train_loss_last_step": step_losses[-1],
                             "val_loss_before": val_curve["before"], "val_loss_final": val_curve[f"epoch_{t.epochs}"], "n": len(train)}},
        per_query=[],
        timing={"train_seconds": train_seconds, "tokens_per_second": tokens_seen / train_seconds, "optimizer_steps": step},
        extra={"method": t.method, "base_model": base, "trainable_params_m": n_trainable / 1e6, "base_gib": base_gib, "peak_gpu_gib": peak_gib,
               "adapter_dir": str(out_dir.relative_to(REPO)), "adapter_mb": adapter_mb, "val_loss_curve": val_curve,
               "train_loss_by_step": [round(x, 4) for x in step_losses], "train_stats": example_stats(train), "val_stats": example_stats(val)})
    path = result.save()
    print(f"done in {train_seconds:.0f}s | peak {peak_gib:.1f} GiB | adapter {adapter_mb:.0f} MB | val {val_curve} | saved -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
