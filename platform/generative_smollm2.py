from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
REVISION = "a91318be21aeaf0879874faa161dcb40c68847e9"
LICENSE = "apache-2.0"
OUT = pathlib.Path("platform/artifacts/generative-smollm2-result.json")


def canonical_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def generate(prompt: str, max_new_tokens: int = 80) -> dict:
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        dtype=torch.float32,
    )
    model.eval()
    messages = [
        {"role": "system", "content": "You are a compact CEREBRON test worker. Answer briefly and factually."},
        {"role": "user", "content": prompt},
    ]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(rendered, return_tensors="pt")
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = generated[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    core = {
        "schema": "CEREBRON_GENERATIVE_MODEL_RUN_V1",
        "provider": "huggingface-open-model",
        "model_id": MODEL_ID,
        "revision": REVISION,
        "license": LICENSE,
        "runtime": "github-actions-cpu",
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "prompt": prompt,
        "input_sha": canonical_sha(prompt),
        "generation": text,
        "latency_s": round(time.perf_counter() - started, 3),
        "limitations": [
            "compact 135M-parameter model",
            "single deterministic smoke generation",
            "not a capability benchmark",
            "not a specialized SAPHEA MICRO yet",
        ],
    }
    core["output_sha"] = canonical_sha(core)
    return core


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=80)
    args = parser.parse_args()
    result = generate(args.prompt, args.max_new_tokens)
    if not result["generation"]:
        raise SystemExit("EMPTY_GENERATION")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
