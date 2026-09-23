from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import threading
import time

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
REVISION = "ec7ddfa904d4d447eedd0b7f126df16957734abb"
LICENSE = "apache-2.0"
BENCHMARK = {
    "schema": "CEREBRON_GENERATIVE_COLD_BENCHMARK_V1",
    "run_id": 35900280586,
    "job_id": 107314375062,
    "artifact_id": 10768374456,
    "artifact_digest": "sha256:f72fc7ab80f1f893ec29990c78796b3a18558d6ca4db4f4007676df78eabad5a",
    "score": 5,
    "max_score": 5,
    "scope": "FIVE_TINY_DETERMINISTIC_TASKS_NOT_GENERAL_CAPABILITY",
}

_LOCK = threading.Lock()
_TOKENIZER = None
_MODEL = None


class GenerativeBackendError(RuntimeError):
    pass


def canonical_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _deps_available() -> bool:
    return importlib.util.find_spec("torch") is not None and importlib.util.find_spec("transformers") is not None


def status() -> dict:
    enabled = os.getenv("CEREBRON_ENABLE_LOCAL_GENERATIVE", "").strip() == "1"
    deps = _deps_available()
    if not enabled:
        state = "CONFIGURED_DISABLED"
    elif not deps:
        state = "RUNTIME_DEPENDENCIES_MISSING"
    else:
        state = "READY_TO_LOAD"
    return {
        "provider": "local-open-model",
        "model_id": MODEL_ID,
        "revision": REVISION,
        "license": LICENSE,
        "runtime": "python-cpu-transformers",
        "enabled": enabled,
        "dependencies_available": deps,
        "health": state,
        "status": "ACTIVE_WORKER" if enabled and deps else state,
        "cost": 0,
        "benchmark_evidence": BENCHMARK,
        "limitations": [
            "compact 0.5B model",
            "benchmark evidence is a five-task smoke benchmark only",
            "model load may require local cache or network access on first use",
        ],
    }


def _load():
    global _TOKENIZER, _MODEL
    st = status()
    if not st["enabled"]:
        raise GenerativeBackendError("LOCAL_GENERATIVE_DISABLED")
    if not st["dependencies_available"]:
        raise GenerativeBackendError("GENERATIVE_DEPENDENCIES_MISSING")
    with _LOCK:
        if _TOKENIZER is None or _MODEL is None:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            _TOKENIZER = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
            _MODEL = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                revision=REVISION,
                dtype=torch.float32,
            )
            _MODEL.eval()
    return _TOKENIZER, _MODEL


def generate(prompt: str, max_new_tokens: int = 160) -> dict:
    prompt = str(prompt).strip()
    if not prompt:
        raise GenerativeBackendError("PROMPT_REQUIRED")
    tokenizer, model = _load()
    import torch
    started = time.perf_counter()
    rendered = tokenizer.apply_chat_template(
        [
            {
                "role": "system",
                "content": (
                    "You are the compact generative worker inside CEREBRON. "
                    "Answer the user's request directly. Do not claim tools, farms, tests, "
                    "or evidence that were not actually executed."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
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
    if not text:
        raise GenerativeBackendError("EMPTY_GENERATION")
    core = {
        "schema": "CEREBRON_GENERATIVE_RESPONSE_V1",
        "provider": "local-open-model",
        "model_id": MODEL_ID,
        "revision": REVISION,
        "license": LICENSE,
        "runtime": "python-cpu-transformers",
        "prompt_sha": canonical_sha(prompt),
        "generation": text,
        "latency_s": round(time.perf_counter() - started, 3),
        "claim_ceiling": "MODEL_OUTPUT_UNVERIFIED",
        "benchmark_evidence": BENCHMARK,
    }
    core["output_sha"] = canonical_sha(core)
    return core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--output", default="platform/artifacts/generative-backend-e2e.json")
    ap.add_argument("--max-new-tokens", type=int, default=80)
    args = ap.parse_args()
    result = generate(args.prompt, args.max_new_tokens)
    target = pathlib.Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
