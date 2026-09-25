#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evolution.cerebron_self_evolution import stable_split

failure=json.loads((ROOT/"memory/failure-bank-v1.json").read_text())
routing=json.loads((ROOT/"config/cerebron-failure-curriculum-routing-v1.json").read_text())

severity={"F_ROLE":100,"F_TRANSFER":90,"F_RED":80,"F_EVIDENCE_SCOPE":75,"F_FORMAT":50,"F_TOOL":30}

def status_score(s):
    u=str(s or "").upper()
    if "OPEN" in u: return 100
    if "ROLLBACK" in u: return 95
    if "REQUIRED" in u: return 90
    if "BLOCKED" in u: return 85
    if "PENDING" in u: return 80
    if "CORRECTED" in u or "CLOSED" in u or "RESOLVED" in u: return 10
    return 40

candidates=[]
for f in failure.get("entries",[]):
    if stable_split(f["FAILURE_ID"])!="train":
        continue
    route=routing.get("explicit_failure_overrides",{}).get(f["FAILURE_ID"])
    if not route:
        route=routing.get("class_routes",{}).get(f.get("FAILURE_CLASS"),{})
    score=status_score(f.get("REPAIR_STATUS"))+severity.get(f.get("FAILURE_CLASS"),20)
    candidates.append({
      "failure_id":f["FAILURE_ID"],
      "failure_class":f.get("FAILURE_CLASS"),
      "source_ai":f.get("AI_ID"),
      "repair_status":f.get("REPAIR_STATUS"),
      "failure_signature":f.get("FAILURE_SIGNATURE"),
      "curriculum_targets":f.get("CURRICULUM_TARGETS",[]) or route.get("axes",[]),
      "routed_specialists":route.get("specialists",[]),
      "priority_score":score,
      "source_split":"train"
    })

candidates.sort(key=lambda x:(-x["priority_score"],x["failure_id"]))
selected=candidates[:8]
for i,x in enumerate(selected,1):
    x["wave_rank"]=i
    x["task_kind"]="TRANSFER_BOUNDARY" if x["failure_class"]=="F_TRANSFER" else (
      "ROLE_FIDELITY_CONTRAST" if x["failure_class"]=="F_ROLE" else
      "ADVERSARIAL_NEGATIVE"
    )
    x["training_eligible"]=False
    x["execution_status"]="NOT_EXECUTED"

report={
  "schema":"CEREBRON_TRAIN_CURRICULUM_WAVE_SELECTION_V1",
  "status":"SELECTED_NOT_EXECUTED",
  "candidate_train_failures":len(candidates),
  "selected_count":len(selected),
  "selected":selected,
  "selection_rule":"TRAIN_SPLIT_ONLY_THEN_OPEN_ROLLBACK_REQUIRED_BEFORE_CLOSED_THEN_FAILURE_CLASS_SEVERITY",
  "agent_execution_claim":False,
  "training_released":False,
  "weight_change":False
}
out=ROOT/"artifacts/train-curriculum-wave-selection-v1.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
