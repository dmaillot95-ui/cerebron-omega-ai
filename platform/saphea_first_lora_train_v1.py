from __future__ import annotations

import hashlib
import json
import os
import pathlib
import platform
import random
import time

import peft
import torch
import transformers
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
REVISION = "ec7ddfa904d4d447eedd0b7f126df16957734abb"
EXPECTED_GOLD_SHA = "efcc9dd80465a6bab3c05ad0706e2ff356a134afc0d7913c6a917a1b66010eaa"
EXPECTED_M6_SHA = "cea1ef908ebf1773f39bbce8876b4041d31b05c73e86878d673dcfe6e3fe4a63"
EXPECTED_BASELINE_SCORE = 18
EXPECTED_BASELINE_MAX = 60
SEED = 3407
MAX_LENGTH = 256
LR = 1e-4
EPOCHS = 1
GRAD_ACCUM = 8
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05

ROOT = pathlib.Path("platform/artifacts")
GOLD_PATH = ROOT / "saphea-epistemic-gold-v1.json"
M6_PATH = ROOT / "saphea-epistemic-m6-v1.json"
BASELINE_PATH = ROOT / "saphea-epistemic-baseline-v1.json"
ADAPTER_DIR = ROOT / "saphea-first-lora-adapter-v1"
REPORT_PATH = ROOT / "saphea-first-lora-training-v1.json"

LABELS = [
    "ROUTED_ONLY",
    "FARM_EXECUTED",
    "NO_NEURAL_LEARNING",
    "NEURAL_LEARNING_VERIFIED",
    "SIMULATION_ONLY",
    "CLAIM_BLOCKED",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(obj) -> str:
    return sha256_bytes(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def tensor_state_sha(model) -> str:
    h = hashlib.sha256()
    found = 0
    for name, param in sorted(model.named_parameters()):
        if "lora_" not in name:
            continue
        found += 1
        h.update(name.encode())
        h.update(str(tuple(param.shape)).encode())
        h.update(param.detach().cpu().contiguous().numpy().tobytes())
    if found == 0:
        raise RuntimeError("NO_LORA_PARAMETERS")
    return h.hexdigest()


def file_sha(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalize(text: str) -> str:
    import re
    s = str(text).strip().upper()
    s = re.sub(r"^[^A-Z_]+|[^A-Z_]+$", "", s)
    return s


def render_prompt(tok, prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are SAPHEA epistemic gate. Obey the requested output format exactly."},
        {"role": "user", "content": prompt},
    ]
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def encode_supervised(tok, prompt: str, target: str):
    prefix = render_prompt(tok, prompt)
    full = prefix + target + (tok.eos_token or "")
    prefix_ids = tok(prefix, add_special_tokens=False)["input_ids"]
    full_ids = tok(full, add_special_tokens=False, truncation=True, max_length=MAX_LENGTH)["input_ids"]
    if len(full_ids) <= len(prefix_ids):
        raise RuntimeError("TARGET_TRUNCATED")
    labels = [-100] * min(len(prefix_ids), len(full_ids)) + full_ids[len(prefix_ids):]
    labels = labels[:len(full_ids)]
    return full_ids, labels


def pad_batch(tok, input_ids, labels):
    max_len = max(len(x) for x in input_ids)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    xs, ys, masks = [], [], []
    for ids, lab in zip(input_ids, labels):
        n = max_len - len(ids)
        xs.append(ids + [pad_id] * n)
        ys.append(lab + [-100] * n)
        masks.append([1] * len(ids) + [0] * n)
    return (
        torch.tensor(xs, dtype=torch.long),
        torch.tensor(ys, dtype=torch.long),
        torch.tensor(masks, dtype=torch.long),
    )


def loss_on_records(model, tok, records):
    model.eval()
    losses = []
    with torch.no_grad():
        for rec in records:
            ids, lab = encode_supervised(tok, rec["prompt"], rec["target"])
            x, y, m = pad_batch(tok, [ids], [lab])
            out = model(input_ids=x, attention_mask=m, labels=y)
            losses.append(float(out.loss.detach().cpu()))
    model.train()
    return sum(losses) / max(1, len(losses))


def evaluate_m6(model, tok, m6):
    model.eval()
    rows = []
    by_label = {k: {"pass": 0, "total": 0} for k in LABELS}
    with torch.no_grad():
        for rec in m6["records"]:
            rendered = render_prompt(tok, rec["prompt"])
            inputs = tok(rendered, return_tensors="pt")
            out = model.generate(
                **inputs,
                max_new_tokens=12,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
            answer = tok.decode(
                out[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()
            pred = normalize(answer)
            ok = pred == rec["target"]
            rows.append(
                {"id": rec["id"], "target": rec["target"], "answer": answer, "prediction": pred, "pass": ok}
            )
            by_label[rec["target"]]["total"] += 1
            by_label[rec["target"]]["pass"] += int(ok)
    score = sum(int(r["pass"]) for r in rows)
    return {
        "score": score,
        "max_score": len(rows),
        "accuracy": score / max(1, len(rows)),
        "by_label": by_label,
        "results": rows,
    }


def main():
    started = time.perf_counter()
    random.seed(SEED)
    torch.manual_seed(SEED)
    ROOT.mkdir(parents=True, exist_ok=True)

    gold = json.loads(GOLD_PATH.read_text())
    m6 = json.loads(M6_PATH.read_text())
    baseline = json.loads(BASELINE_PATH.read_text())

    if gold["dataset_sha256"] != EXPECTED_GOLD_SHA:
        raise SystemExit("GOLD_SHA_MISMATCH")
    if m6["dataset_sha256"] != EXPECTED_M6_SHA:
        raise SystemExit("M6_SHA_MISMATCH")
    if m6.get("deny_training") is not True:
        raise SystemExit("M6_DENY_TRAINING_MISSING")
    if gold.get("training_eligible") is not True:
        raise SystemExit("GOLD_NOT_TRAINING_ELIGIBLE")
    if baseline["m6_dataset_sha256"] != EXPECTED_M6_SHA:
        raise SystemExit("BASELINE_M6_SHA_MISMATCH")
    if baseline["score"] != EXPECTED_BASELINE_SCORE or baseline["max_score"] != EXPECTED_BASELINE_MAX:
        raise SystemExit("BASELINE_SCORE_DRIFT")

    gold_ids = {r["id"] for r in gold["records"]}
    m6_ids = {r["id"] for r in m6["records"]}
    if gold_ids & m6_ids:
        raise SystemExit("GOLD_M6_ID_OVERLAP")

    records = list(gold["records"])
    rng = random.Random(SEED)
    rng.shuffle(records)
    train_records = records[:150]
    val_records = records[150:]
    split_manifest = {
        "seed": SEED,
        "train_ids": [r["id"] for r in train_records],
        "validation_ids": [r["id"] for r in val_records],
    }
    split_sha = canonical_sha(split_manifest)

    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    lora_cfg = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(base, lora_cfg)
    model.train()

    trainable_names = [n for n, p in model.named_parameters() if p.requires_grad]
    if not trainable_names or any("lora_" not in n for n in trainable_names):
        raise SystemExit("NON_LORA_TRAINABLE_PARAMETER_DETECTED")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    init_adapter_sha = tensor_state_sha(model)
    val_loss_before = loss_on_records(model, tok, val_records)

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=LR,
        weight_decay=0.01,
    )
    optimizer.zero_grad(set_to_none=True)

    train_loss_sum = 0.0
    train_steps = 0
    optimizer_steps = 0
    for _epoch in range(EPOCHS):
        rng.shuffle(train_records)
        for idx, rec in enumerate(train_records, start=1):
            ids, lab = encode_supervised(tok, rec["prompt"], rec["target"])
            x, y, m = pad_batch(tok, [ids], [lab])
            out = model(input_ids=x, attention_mask=m, labels=y)
            loss = out.loss / GRAD_ACCUM
            if not torch.isfinite(loss):
                raise SystemExit("NONFINITE_LOSS")
            loss.backward()
            train_loss_sum += float(out.loss.detach().cpu())
            train_steps += 1
            if idx % GRAD_ACCUM == 0 or idx == len(train_records):
                torch.nn.utils.clip_grad_norm_(
                    [p for p in model.parameters() if p.requires_grad], 1.0
                )
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_steps += 1

    final_adapter_sha = tensor_state_sha(model)
    if final_adapter_sha == init_adapter_sha:
        raise SystemExit("ADAPTER_WEIGHTS_UNCHANGED")

    val_loss_after = loss_on_records(model, tok, val_records)
    post = evaluate_m6(model, tok, m6)

    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(ADAPTER_DIR, safe_serialization=True)
    adapter_file = ADAPTER_DIR / "adapter_model.safetensors"
    adapter_cfg = ADAPTER_DIR / "adapter_config.json"
    if not adapter_file.exists() or not adapter_cfg.exists():
        raise SystemExit("ADAPTER_FILES_MISSING")
    saved_adapter_sha = file_sha(adapter_file)

    baseline_by_label = {k: {"pass": 0, "total": 0} for k in LABELS}
    for row in baseline["results"]:
        baseline_by_label[row["target"]]["total"] += 1
        baseline_by_label[row["target"]]["pass"] += int(row["pass"])
    per_label_delta = {
        k: post["by_label"][k]["pass"] - baseline_by_label[k]["pass"]
        for k in LABELS
    }
    critical_regression = any(v < -2 for v in per_label_delta.values())
    cold_gain = post["score"] - baseline["score"]

    if cold_gain > 0 and not critical_regression:
        training_decision = "G6_TRAINING_VERIFIED_HOLD_G7_PENDING_TRANSFER_ABLATION_AUDIT"
    else:
        training_decision = "ROLLBACK_RETAIN_EVIDENCE"

    report = {
        "schema": "SAPHEA_FIRST_LORA_TRAINING_V1",
        "role": "SAPHEA",
        "scope": "CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_ONLY",
        "base_model_id": MODEL_ID,
        "base_revision": REVISION,
        "base_weights_policy": "IMMUTABLE_G0",
        "adapter_type": "PEFT_LORA",
        "peft_target_modules": ["q_proj", "v_proj"],
        "library_versions": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "peft": peft.__version__,
        },
        "hardware": {
            "device": "cpu",
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "torch_num_threads": torch.get_num_threads(),
        },
        "hyperparameters": {
            "r": LORA_R,
            "lora_alpha": LORA_ALPHA,
            "lora_dropout": LORA_DROPOUT,
            "learning_rate": LR,
            "epochs": EPOCHS,
            "gradient_accumulation_steps": GRAD_ACCUM,
            "effective_batch_size": GRAD_ACCUM,
            "max_length": MAX_LENGTH,
            "seed": SEED,
        },
        "gold_dataset_sha256": gold["dataset_sha256"],
        "m6_dataset_sha256": m6["dataset_sha256"],
        "m6_deny_training": True,
        "gold_m6_disjoint": True,
        "split_manifest_sha256": split_sha,
        "train_record_count": len(train_records),
        "validation_record_count": len(val_records),
        "m6_record_count": len(m6["records"]),
        "total_params": total_params,
        "trainable_params": trainable_params,
        "trainable_fraction": trainable_params / total_params,
        "trainable_names_all_lora": True,
        "initial_adapter_tensor_sha256": init_adapter_sha,
        "final_adapter_tensor_sha256": final_adapter_sha,
        "weights_changed": final_adapter_sha != init_adapter_sha,
        "adapter_file": adapter_file.name,
        "adapter_file_sha256": saved_adapter_sha,
        "adapter_config_sha256": file_sha(adapter_cfg),
        "baseline_m6_score": baseline["score"],
        "baseline_m6_max": baseline["max_score"],
        "posttrain_m6_score": post["score"],
        "posttrain_m6_max": post["max_score"],
        "cold_gain": cold_gain,
        "baseline_by_label": baseline_by_label,
        "posttrain_by_label": post["by_label"],
        "per_label_pass_delta": per_label_delta,
        "critical_regression": critical_regression,
        "validation_loss_before": val_loss_before,
        "validation_loss_after": val_loss_after,
        "validation_loss_improved": val_loss_after < val_loss_before,
        "train_mean_loss": train_loss_sum / max(1, train_steps),
        "train_steps": train_steps,
        "optimizer_steps": optimizer_steps,
        "decision": training_decision,
        "promotion": "NOT_PROMOTED",
        "pending_gates": [
            "HF_PRIVATE_WRITE_READBACK_SHA",
            "NOVEL_TRANSFER_GAIN",
            "ABLATION_SUPPORTS_VALUE",
            "INDEPENDENT_AUDIT",
            "RED_TEAM",
            "F72_REVIEW",
            "AFAH_FINAL_AUTHORITY",
        ],
        "elapsed_s": round(time.perf_counter() - started, 3),
        "claim_ceiling": "REAL_LORA_WEIGHT_CHANGE_IF_WEIGHTS_CHANGED_TRUE; NO_GENERAL_CAPABILITY_CLAIM",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "weights_changed": report["weights_changed"],
        "adapter_sha256": report["adapter_file_sha256"],
        "baseline": report["baseline_m6_score"],
        "posttrain": report["posttrain_m6_score"],
        "cold_gain": report["cold_gain"],
        "critical_regression": report["critical_regression"],
        "decision": report["decision"],
    }, sort_keys=True))

    if not report["weights_changed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
