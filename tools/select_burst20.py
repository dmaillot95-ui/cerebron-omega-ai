#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/"config/burst20-controller-v1.json").read_text())
mission=json.loads((R/"config/burst20-selection-canary.json").read_text())
colonies=json.loads((R/"config/all-ai-8-agent-colonies-v1.json").read_text())

available=[c for c in colonies["colonies"] if c["available"]]
assert len(available)>=20

# Deterministic spread across available AIs: one parent per role before reuse.
roles=mission["required_roles"]
selected=[]
for i,role in enumerate(roles):
    parent=available[i % len(available)]
    # Rotate local slots but reserve A6 for memory and A7 for local synthesis when semantically appropriate.
    slots=["A1_EXPLORER","A2_ANALYST","A3_EXECUTOR","A4_AUDITOR","A5_COUNTER_AUDITOR"]
    slot=slots[i % len(slots)]
    worker_id=f'{parent["ai_id"]}:{slot}:BURST20:{i+1:02d}'
    lineage=f'{parent["ai_id"]}|{slot}|CEREBRON_SHARED_INFRA'
    selected.append({
      "burst_slot":i+1,
      "worker_id":worker_id,
      "parent_ai":parent["ai_id"],
      "identity":parent["identity"],
      "local_slot":slot,
      "role":role,
      "execution_route":"UNBOUND_UNTIL_QUALIFIED",
      "model_source":"HF_PINNED_CANDIDATE_WHEN_GITHUB_ACTIONS_HF_WEIGHTS_QUALIFIED",
      "status":"PLANNED_NOT_EXECUTED",
      "lineage_fingerprint":hashlib.sha256(lineage.encode()).hexdigest()
    })

assert len(selected)==20
assert len({x["worker_id"] for x in selected})==20
assert len({x["parent_ai"] for x in selected})==20
assert set(x["role"] for x in selected)==set(roles)

out={
 "schema":"CEREBRON_BURST20_SELECTION_RECEIPT_V1",
 "mission_id":mission["mission_id"],
 "requested_workers":mission["requested_workers"],
 "selected_workers":len(selected),
 "executed_workers":0,
 "selection_status":"PASS",
 "execution_status":"NOT_EXECUTED",
 "workers":selected,
 "rules":["PLANNED_NE_EXECUTED","MAX_20","DISTINCT_PARENT_AI_IN_CANARY","REAL_EXECUTION_RECEIPT_REQUIRED"]
}
Path("receipts/burst20").mkdir(parents=True,exist_ok=True)
Path("receipts/burst20/selection-canary.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k!="workers"},sort_keys=True))
