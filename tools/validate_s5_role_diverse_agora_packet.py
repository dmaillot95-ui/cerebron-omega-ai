#!/usr/bin/env python3
import json,glob
from pathlib import Path
R=Path(__file__).resolve().parents[1]
files=sorted(glob.glob(str(R/"agora/packets/s5-role-diverse-*.json")))
if not files:
    raise SystemExit("NO_S5_ROLE_DIVERSE_AGORA_PACKET")
p=Path(files[-1])
x=json.loads(p.read_text())
assert x["schema"]=="CEREBRON_AGORA_REAL_WORKER_PACKET_V1"
assert x["executed_workers"]==5
assert x["successful_workers"]==5
assert len(x["roles"])==5
assert x["unique_result_sha256"]>=1
assert x["unique_lineage_fingerprints"]==1
assert x["lineage_classification"]=="CORRELATED_SHARED_MODEL_REVISION"
assert x["independent_evidence_count"]==0
assert x["promotion"]=="NOT_GOLD_PENDING_AUDIT_COUNTER_AUDIT"
for w in x["workers"]:
    assert w["real_execution"] is True
    assert w["llm_inference"] is True
    assert w["inference"]=="PASS"
    assert w["result_sha256"]
    assert w["receipt_sha256"]
status="PASS_ROLE_DIVERSE_OUTPUTS" if x["unique_result_sha256"]>=3 else "PASS_EXECUTION_LOW_OUTPUT_DIVERSITY"
print(json.dumps({
  "status":status,
  "packet":p.name,
  "workers":5,
  "roles":5,
  "unique_results":x["unique_result_sha256"],
  "independent_evidence_count":0,
  "promotion":"NOT_GOLD_PENDING_AUDIT_COUNTER_AUDIT"
},sort_keys=True))
