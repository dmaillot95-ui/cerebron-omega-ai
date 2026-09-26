#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time

CORES = {
    "QWEN3_4B": {
        "model_id": "Qwen/Qwen3-4B",
        "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
        "min_vram_gb": 20.0,
    },
    "SMOLLM3_3B": {
        "model_id": "HuggingFaceTB/SmolLM3-3B",
        "revision": "a07cc9a04f16550a088caea529712d1d335b0ac1",
        "min_vram_gb": 16.0,
    },
}
SCHEMA = "CEREBRON_WAVE3A_TARGET_CORE_CANARY_V1"
CANARY_TEXT = (
    "CEREBRON WAVE3A target-core backend canary. "
    "This is disposable infrastructure validation, not role training. "
    "Return exactly EVIDENCE."
)
CANARY_TARGET = "EVIDENCE"


def sha_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter_tensor_sha(model) -> str:
    h = hashlib.sha256()
    count = 0
    for name, param in sorted(model.named_parameters()):
        if "lora_" not in name:
            continue
        count += 1
        h.update(name.encode())
        h.update(str(tuple(param.shape)).encode())
        h.update(param.detach().float().cpu().contiguous().numpy().tobytes())
    if count == 0:
        raise RuntimeError("NO_LORA_PARAMETERS")
    return h.hexdigest()


def write_report(output: pathlib.Path, report: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "canary-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )


def deny(output: pathlib.Path, report: dict, reason: str, code: int = 2) -> None:
    report.update({
        "status": "DENY",
        "deny_reason": reason,
        "training_executed": False,
        "weights_changed": False,
        "target_model_canary_pass": False,
        "release_eligible": False,
        "promotion": "DENY",
    })
    write_report(output, report)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-core", choices=sorted(CORES))
    parser.add_argument("--output-root", default="artifacts/wave3a-target-core-canary")
    parser.add_argument("--print-contract", action="store_true")
    args = parser.parse_args()

    if args.print_contract:
        print(json.dumps({
            "schema": SCHEMA,
            "cores": CORES,
            "canary_only": True,
            "automatic_release": False,
            "automatic_promotion": False,
            "requires_cuda": True,
        }, sort_keys=True))
        return

    if not args.model_core:
        raise SystemExit("MODEL_CORE_REQUIRED")

    output = pathlib.Path(args.output_root)
    core = CORES[args.model_core]
    started = time.perf_counter()
    report = {
        "schema": SCHEMA,
        "model_core": args.model_core,
        "base_model_id": core["model_id"],
        "base_revision": core["revision"],
        "canary_only": True,
        "role_training": False,
        "dataset_training": False,
        "cold_transfer_red_used_for_training": False,
        "training_released": False,
        "continuous_training_eligible": False,
        "release_eligible": False,
        "promotion": "DENY",
        "claim_ceiling": "TARGET_CORE_SINGLE_STEP_LORA_BACKEND_CANARY_ONLY_NO_ROLE_CAPABILITY_NO_RELEASE_NO_PROMOTION",
    }

    try:
        import torch
    except Exception as exc:
        deny(output, report, f"TORCH_IMPORT_FAILED:{type(exc).__name__}")

    if not torch.cuda.is_available():
        deny(output, report, "CUDA_UNAVAILABLE")

    device = torch.device("cuda:0")
    props = torch.cuda.get_device_properties(device)
    total_vram_gb = float(props.total_memory) / (1024**3)
    report["hardware"] = {
        "device_name": props.name,
        "total_vram_gb": round(total_vram_gb, 3),
        "cuda_version": torch.version.cuda,
        "torch_version": torch.__version__,
    }
    if total_vram_gb < float(core["min_vram_gb"]):
        deny(output, report, f"VRAM_BELOW_CONSERVATIVE_CANARY_FLOOR:{total_vram_gb:.3f}<{core['min_vram_gb']:.3f}")

    try:
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        deny(output, report, f"LORA_STACK_IMPORT_FAILED:{type(exc).__name__}")

    torch.manual_seed(26092601)
    torch.cuda.manual_seed_all(26092601)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    report["dtype"] = str(dtype)

    tokenizer = AutoTokenizer.from_pretrained(
        core["model_id"], revision=core["revision"], trust_remote_code=False
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        core["model_id"],
        revision=core["revision"],
        dtype=dtype,
        low_cpu_mem_usage=True,
        device_map={"": 0},
        trust_remote_code=False,
    )
    if hasattr(base.config, "use_cache"):
        base.config.use_cache = False
    if hasattr(base, "gradient_checkpointing_enable"):
        base.gradient_checkpointing_enable()

    lora_cfg = LoraConfig(
        r=4,
        lora_alpha=8,
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(base, lora_cfg)
    trainable = [name for name, p in model.named_parameters() if p.requires_grad]
    if not trainable or any("lora_" not in name for name in trainable):
        deny(output, report, "NON_LORA_TRAINABLE_PARAMETER")

    prefix_ids = tokenizer(
        CANARY_TEXT, add_special_tokens=True, truncation=True, max_length=96
    )["input_ids"]
    target_ids = tokenizer(
        CANARY_TARGET + (tokenizer.eos_token or ""),
        add_special_tokens=False,
        truncation=True,
        max_length=16,
    )["input_ids"]
    input_ids = torch.tensor([prefix_ids + target_ids], device=device)
    labels = torch.tensor([[-100] * len(prefix_ids) + target_ids], device=device)
    attention_mask = torch.ones_like(input_ids, device=device)

    initial_sha = adapter_tensor_sha(model)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=1e-4, weight_decay=0.0
    )

    torch.cuda.reset_peak_memory_stats(device)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
    if not torch.isfinite(outputs.loss):
        deny(output, report, "NONFINITE_LOSS")
    outputs.loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    torch.cuda.synchronize(device)

    final_sha = adapter_tensor_sha(model)
    if final_sha == initial_sha:
        deny(output, report, "ADAPTER_TENSOR_SHA_UNCHANGED")

    adapter_dir = output / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_dir, safe_serialization=True)
    adapter_file = adapter_dir / "adapter_model.safetensors"
    adapter_cfg = adapter_dir / "adapter_config.json"
    if not adapter_file.is_file() or not adapter_cfg.is_file():
        deny(output, report, "ADAPTER_SAVE_MISSING")

    report.update({
        "status": "PASS_TARGET_CORE_CANARY",
        "training_executed": True,
        "optimizer_steps": 1,
        "weights_changed": True,
        "target_model_canary_pass": True,
        "initial_adapter_tensor_sha256": initial_sha,
        "final_adapter_tensor_sha256": final_sha,
        "adapter_file_sha256": sha_file(adapter_file),
        "adapter_config_sha256": sha_file(adapter_cfg),
        "loss": float(outputs.loss.detach().float().cpu()),
        "hardware": {
            **report["hardware"],
            "peak_memory_allocated_gb": round(torch.cuda.max_memory_allocated(device) / (1024**3), 3),
            "peak_memory_reserved_gb": round(torch.cuda.max_memory_reserved(device) / (1024**3), 3),
        },
        "elapsed_s": round(time.perf_counter() - started, 3),
        "release_eligible": False,
        "promotion": "DENY",
        "pending": [
            "PERSIST_ADAPTER_OUTSIDE_GITHUB_ARTIFACTS",
            "READBACK_SHA_VERIFY",
            "INDEPENDENT_GATE_REVIEW",
        ],
    })
    write_report(output, report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
