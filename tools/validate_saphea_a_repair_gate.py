#!/usr/bin/env python3
import glob,json,sys
from pathlib import Path
files=sorted(glob.glob("receipts/workers/saphea-a-system-architect-repair-*.json"))
if not files:
    raise SystemExit("SAPHEA_A_REPAIR_RECEIPT_MISSING")
p=Path(files[-1]);x=json.loads(p.read_text())
assert x.get("schema")=="SAPHEA_A_SYSTEM_ARCHITECT_REPAIR_CANARY_V1"
assert x.get("worker_id")=="SAPHEA-A"
assert x.get("role_id")=="SYSTEM_ARCHITECT"
assert x.get("llm_inference") is True
assert x.get("inference")=="PASS"
assert x.get("parse_ok") is True
assert x.get("rejects_simulation_alone") is True
assert x.get("physical_gate_present") is True
assert x.get("false_validation") is False
assert x.get("canary_pass") is True
assert x.get("spiralix_envelope_sha256")
print(json.dumps({"status":"PASS","receipt":str(p),"run_id":x.get("run_id"),"canary_pass":True},sort_keys=True))
