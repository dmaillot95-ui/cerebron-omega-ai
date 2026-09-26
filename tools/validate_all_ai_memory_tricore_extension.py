#!/usr/bin/env python3
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
base = json.loads((R / "config/all-ai-memory-matrix-v1.json").read_text())
ext = json.loads((R / "config/all-ai-memory-matrix-tricore-extension-v1.json").read_text())
receipt = json.loads((R / ext["verification_receipt"]).read_text())

assert ext["schema"] == "CEREBRON_ALL_AI_MEMORY_MATRIX_TRICORE_EXTENSION_V1"
assert ext["status"] == "HF_DIRECT_VERIFIED_3_OF_3"
assert ext["training_executed"] is False
assert ext["weights_changed"] is False
assert ext["runtime_changed"] is False

base_entries = base["entries"]
ext_entries = ext["entries"]
assert len(ext_entries) == 3
assert ext["base_logical_ai"] == len(base_entries)
assert ext["base_available_ai"] == sum(1 for x in base_entries if x["available"])
assert ext["base_unavailable_ai"] == sum(1 for x in base_entries if not x["available"])
assert ext["combined_logical_ai"] == len(base_entries) + len(ext_entries)
assert ext["combined_available_ai"] == ext["base_available_ai"] + 3
assert ext["combined_unavailable_ai"] == ext["base_unavailable_ai"]

base_ids = {x["ai_id"] for x in base_entries}
ext_ids = {x["ai_id"] for x in ext_entries}
assert len(ext_ids) == 3 and not (base_ids & ext_ids)
assert len({x["namespace"] for x in base_entries + ext_entries}) == len(base_entries) + len(ext_entries)

assert receipt["run_id"] == str(ext["verification_run_id"])
assert receipt["status"] == "PASS"
assert receipt["private_repo"] == "PASS" and receipt["private_repo_after"] == "PASS"
assert receipt["training_executed"] is False
assert receipt["weights_changed"] is False

by_id = {x["ai_id"]: x for x in receipt["results"]}
for x in ext_entries:
    assert x["available"] is True
    assert x["hf_write_read_sha"] == "HF_DIRECT_VERIFIED"
    r = by_id[x["ai_id"]]
    assert r["status"] == r["write"] == r["read"] == r["sha256"] == "PASS"
    assert r["payload_sha256"] == r["downloaded_sha256"] == x["payload_sha256"]
    assert r["remote_object"] == x["remote_object"]

print(json.dumps({
    "status": "PASS",
    "base_logical_ai": len(base_entries),
    "extension_logical_ai": len(ext_entries),
    "combined_logical_ai": len(base_entries) + len(ext_entries),
    "combined_available_ai": sum(1 for x in base_entries if x["available"]) + 3,
    "hf_verified_extension": 3,
    "training_executed": False,
    "weights_changed": False
}, sort_keys=True))
