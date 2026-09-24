#!/usr/bin/env python3
import json,glob
from pathlib import Path
R=Path(__file__).resolve().parents[1]
files=sorted(glob.glob(str(R/"receipts/agora/m10-semantic-audit-*.json")))
if not files:
    raise SystemExit("M10_DECISION_RECEIPT_MISSING")
p=Path(files[-1])
x=json.loads(p.read_text())
assert x["schema"]=="CEREBRON_M10_SEMANTIC_AUDIT_DECISION_V1"
assert x["decision"] in {"ACCEPT","LIMIT","HOLD","REJECT"}
assert x["gold_status"] in {"DENY","DENY_PENDING_HUMAN_OR_STRONGER_AUDIT"}
assert x["scaling_5_to_10"] in {"DENY_5_TO_10_PENDING_PROMPT_REPAIR","HOLD"}
assert x["promotion"]=="NO_GOLD_NO_TRAINING"
assert x["deterministic_findings"]["independent_evidence_count"]==0
assert x["deterministic_findings"]["shared_lineage"] is True
assert len(x["repair_required"])>=1
print(json.dumps({
  "status":"PASS",
  "receipt":p.name,
  "decision":x["decision"],
  "gold_status":x["gold_status"],
  "scaling_5_to_10":x["scaling_5_to_10"],
  "auditors_completed":x["auditors_completed"],
  "independent_evidence_count":0
},sort_keys=True))
