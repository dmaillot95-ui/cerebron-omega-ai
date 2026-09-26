#!/usr/bin/env python3
"""Fail-closed structural/evidence audit for NOVA/ATLAS/COLOSSUS model slots."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/tricore-model-slots-v1.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL_CLOSED: {message}")


def main() -> int:
    c = load("config/tricore-model-slots-v1.json")
    require(c["schema"] == "CEREBRON_TRICORE_MODEL_SLOTS_V1", "schema")
    require(c["total_slots"] == 9, "total_slots must be 9")
    require(c["candidate_assigned_slots"] == 6, "candidate_assigned_slots must be 6")
    require(c["blocked_slots"] == 3, "blocked_slots must be 3")
    for k in ("runtime_enabled", "output_enabled", "training_enabled", "training_executed", "weights_changed", "adapter_changed"):
        require(c[k] is False, f"{k} must remain false")

    expected = {176: "NOVA", 177: "ATLAS", 178: "COLOSSUS"}
    members = c["members"]
    require(len(members) == 3, "exactly three tri-core members required")
    require({m["farm_id"]: m["identity"] for m in members} == expected, "member identity/farm mismatch")

    slots = []
    for m in members:
        require(m["runtime"] == "MUTED_HOLD", f"{m['identity']} runtime must remain muted")
        require(len(m["slots"]) == 3, f"{m['identity']} must have three slots")
        require({s["slot"] for s in m["slots"]} == {"A", "B", "C"}, f"{m['identity']} slots must be A/B/C")
        slots.extend(m["slots"])

    require(len(slots) == 9, "flattened slot count must be 9")
    require(sum(s["model_ref"] == "SMOLLM3_3B_BASE" for s in slots) == 3, "SmolLM3 slot count")
    require(sum(s["model_ref"] == "QWEN3_4B_BASE" for s in slots) == 3, "Qwen3 slot count")
    require(sum(s["model_ref"] == "THIRD_LINEAGE" for s in slots) == 3, "third-lineage slot count")
    require(all(s["state"] == "UNASSIGNED_BLOCKED" for s in slots if s["model_ref"] == "THIRD_LINEAGE"), "third lineage must stay blocked")

    models = c["models"]
    smol = models["SMOLLM3_3B_BASE"]
    qwen = models["QWEN3_4B_BASE"]
    third = models["THIRD_LINEAGE"]

    smol_pin = load(smol["pin_receipt"])
    smol_runtime = load(smol["runtime_receipt"])
    require(smol_pin["model"] == smol["model_id"], "SmolLM3 model id evidence mismatch")
    require(smol_pin["resolved_sha"] == smol["revision"], "SmolLM3 revision mismatch")
    require(smol_pin["pin_resolve"] == "PASS" and smol_pin["config_load"] == "PASS", "SmolLM3 pin/config evidence")
    require(smol_runtime["model_id"] == smol["model_id"], "SmolLM3 runtime model mismatch")
    require(smol_runtime["requested_revision_sha"] == smol["revision"], "SmolLM3 runtime revision mismatch")
    require(smol_runtime["load"] == "PASS" and smol_runtime["inference"] == "PASS", "SmolLM3 runtime evidence")

    qwen_pin = load(qwen["pin_receipt"])
    require(qwen_pin["model"] == qwen["model_id"], "Qwen3 model id evidence mismatch")
    require(qwen_pin["resolved_sha"] == qwen["revision"], "Qwen3 revision mismatch")
    require(qwen_pin["pin_resolve"] == "PASS" and qwen_pin["config_load"] == "PASS", "Qwen3 pin/config evidence")
    require(qwen["runtime_load"] == "NOT_PROVEN_FOR_THIS_BASE_RECEIPT", "Qwen runtime scope must not be overstated")

    require(third["model_id"] is None and third["revision"] is None, "third lineage must remain unassigned")
    require(third["status"] == "UNASSIGNED_BLOCKED_NO_THIRD_VERIFIED_BASE", "third lineage status")

    memory = load(c["memory_reference"])
    require(memory["status"] == "HF_DIRECT_VERIFIED_3_OF_3", "tri-core HF memory must be directly verified")
    require(memory["training_executed"] is False and memory["weights_changed"] is False, "memory must not become training")

    print(json.dumps({
        "status": "PASS",
        "members": 3,
        "slots": 9,
        "candidate_assigned": 6,
        "blocked": 3,
        "smollm3_runtime": "PASS",
        "qwen3_pin_config": "PASS_RUNTIME_UNPROVEN",
        "third_lineage": "BLOCKED",
        "training_executed": False,
        "weights_changed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
