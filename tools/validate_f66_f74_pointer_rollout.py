#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=json.loads((R/"config/f66-f74-pointer-rollout-v1.json").read_text())
assert p["status"]=="BLOCKED_BY_M03_HF_CANARY"
assert p["runtime_changed"] is False
assert p["prerequisite"]["required_receipt"]=="receipts/p03/all-ai-hf-m03.json"
assert "private_payload" in p["forbidden_public_fields"]
assert p["unavailable_rule"]=="NO_POINTER_CREATED"
assert p["overwrite_rule"].startswith("APPEND")
assert p["write_order"][0]=="VERIFY_M03_HF_PASS"
assert "VERIFY_ROLLBACK_POINTER" in p["write_order"]
print(json.dumps({"status":"PASS","rollout":"PREPARED_BLOCKED","runtime_changed":False},sort_keys=True))
