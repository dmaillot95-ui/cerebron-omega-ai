#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "config/wave1-parallel-role-baseline-v1.json"


def sha256_obj(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def parse_label(text: str, labels: list[str]) -> str | None:
    s = text.strip().upper()
    exact = re.sub(r"^[^A-Z_]+|[^A-Z_]+$", "", s)
    if exact in labels:
        return exact
    for label in labels:
        if re.search(rf"(?<![A-Z_]){re.escape(label)}(?![A-Z_])", s):
            return label
    return None


def build_prompt(role: str, spec: dict, scenario: str) -> tuple[str, str]:
    labels = ", ".join(spec["labels"])
    system = (
        f"You are the scoped {role} baseline evaluator inside CEREBRON. "
        f"Specialization: {spec['specialization']}. "
        "This is a frozen cold benchmark and not training. "
        "Choose the single label best justified by the scenario. "
        "Do not invent execution or evidence."
    )
    user = (
        f"Scenario: {scenario}\n"
        f"Allowed labels: [{labels}]\n"
        "Return exactly one label and no explanation."
    )
    return system, user


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    cfg = json.loads(CFG_PATH.read_text())
    role = args.role.upper()
    if role not in cfg["roles"]:
        raise SystemExit(f"UNKNOWN_ROLE:{role}")
    spec = cfg["roles"][role]
    model_id = cfg["base_model"]["id"]
    revision = cfg["base_model"]["revision"]

    tasks = [
        {"id": row[0], "target": row[1], "scenario": row[2]}
        for row in spec["tasks"]
    ]
    benchmark_payload = {
        "schema": cfg["schema"],
        "role": role,
        "labels": spec["labels"],
        "tasks": tasks,
        "deny_training": True,
    }
    benchmark_sha = sha256_obj(benchmark_payload)

    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()

    results = []
    started = time.perf_counter()
    with torch.no_grad():
        for task in tasks:
            system, user = build_prompt(role, spec, task["scenario"])
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
            try:
                prompt = tok.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                prompt = system + "\n\n" + user + "\nASSISTANT:\n"
            inp = tok(prompt, return_tensors="pt")
            out = model.generate(
                **inp,
                max_new_tokens=10,
                do_sample=False,
                repetition_penalty=1.05,
                pad_token_id=tok.eos_token_id,
            )
            answer = tok.decode(
                out[0][inp["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()
            pred = parse_label(answer, spec["labels"])
            ok = pred == task["target"]
            results.append({
                "id": task["id"],
                "target": task["target"],
                "prediction": pred,
                "raw_output": answer[:300],
                "pass": ok,
            })

    score = sum(int(r["pass"]) for r in results)
    receipt = {
        "schema": "CEREBRON_WAVE1_ROLE_BASELINE_RECEIPT_V1",
        "run_id": int(args.run_id),
        "role": role,
        "specialization": spec["specialization"],
        "training_readiness": spec["training_readiness"],
        "real_inference": True,
        "training_executed": False,
        "benchmark_deny_training": True,
        "benchmark_sha256": benchmark_sha,
        "model_id": model_id,
        "revision": revision,
        "lineage_fingerprint": hashlib.sha256(
            f"{model_id}|{revision}".encode()
        ).hexdigest(),
        "independent_evidence": False,
        "task_count": len(tasks),
        "score": score,
        "accuracy": score / max(1, len(tasks)),
        "results": results,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "claim_ceiling": "SCOPED_COLD_ROLE_BASELINE_ONLY_NOT_TRAINING_OR_GENERAL_CAPABILITY",
    }
    receipt["receipt_sha256"] = sha256_obj(receipt)
    p = pathlib.Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "role": role,
        "score": score,
        "max": len(tasks),
        "accuracy": receipt["accuracy"],
        "training_readiness": receipt["training_readiness"],
        "benchmark_sha256": benchmark_sha,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
