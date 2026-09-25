#!/usr/bin/env python3
"""Build candidate corrective tasks only from TRAIN-split failure records.

These are questions/tasks, never answers and never training data by themselves.
Reserved validation/holdout records are excluded before derivation.
"""
import json, hashlib, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evolution.cerebron_self_evolution import stable_split

failure=json.loads((ROOT/"memory/failure-bank-v1.json").read_text())
routing=json.loads((ROOT/"config/cerebron-failure-curriculum-routing-v1.json").read_text())

task_kinds=[
  ("CORRECTIVE_CONTRAST","Construct two superficially similar situations where the repaired rule accepts one and rejects the other. Do not copy any evaluation example."),
  ("TRANSFER_BOUNDARY","Create a new-domain case that tests whether the repair transfers beyond the original wording while preserving the same failure boundary."),
  ("ADVERSARIAL_NEGATIVE","Create an adversarial case designed to trigger the historical failure if the learner still uses the bad shortcut.")
]

tasks=[]
excluded=[]
for f in failure.get("entries",[]):
    fid=f["FAILURE_ID"]
    split=stable_split(fid)
    if split!="train":
        excluded.append({"failure_id":fid,"split":split})
        continue
    route=routing.get("explicit_failure_overrides",{}).get(fid,{})
    if not route:
        route=routing.get("class_routes",{}).get(f.get("FAILURE_CLASS"),{})
    specialists=route.get("specialists",[])
    axes=f.get("CURRICULUM_TARGETS",[]) or route.get("axes",[])
    if not axes:
        axes=[
          f.get("FAILURE_CLASS","UNKNOWN"),
          "ROOT_CAUSE_DISCRIMINATION",
          "FAILURE_BOUNDARY_TRANSFER"
        ]
    for idx,(kind,instruction) in enumerate(task_kinds,1):
        body={
          "task_id":f"TRAINFAIL-{fid}-{idx:02d}",
          "source_failure_id":fid,
          "source_split":"train",
          "source_failure_class":f.get("FAILURE_CLASS"),
          "source_ai":f.get("AI_ID"),
          "failure_signature":f.get("FAILURE_SIGNATURE"),
          "root_cause":f.get("ROOT_CAUSE"),
          "impact":f.get("IMPACT"),
          "repair_status":f.get("REPAIR_STATUS"),
          "curriculum_axes":axes,
          "routed_specialists":specialists,
          "kind":kind,
          "instruction":instruction,
          "response_contract":[
            "CASE",
            "EXPECTED_BOUNDARY",
            "ASSUMPTIONS",
            "WHY_OLD_SHORTCUT_FAILS",
            "EVIDENCE_NEEDED",
            "UNKNOWN"
          ],
          "derived_from_reserved_eval":False,
          "training_eligible":False,
          "requires_before_training":[
            "REAL_MODEL_ATTEMPT",
            "AUDIT",
            "COUNTER_AUDIT",
            "REPRODUCTION_WHEN_APPLICABLE",
            "GOLD_OR_RED_ADMISSION",
            "DECONTAMINATION"
          ]
        }
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        body["task_sha256"]=hashlib.sha256(raw).hexdigest()
        tasks.append(body)

report={
  "schema":"CEREBRON_TRAIN_FAILURE_CURRICULUM_V1",
  "status":"CANDIDATE_TASKS_ONLY_NOT_TRAINING_DATA",
  "failure_bank_count":len(failure.get("entries",[])),
  "train_source_failure_count":len({t["source_failure_id"] for t in tasks}),
  "excluded_reserved_failure_count":len(excluded),
  "task_count":len(tasks),
  "task_kinds":[x[0] for x in task_kinds],
  "all_sources_train_split":all(t["source_split"]=="train" for t in tasks),
  "reserved_eval_derivative_count":sum(bool(t["derived_from_reserved_eval"]) for t in tasks),
  "training_eligible_count":sum(bool(t["training_eligible"]) for t in tasks),
  "excluded_reserved_sources":excluded,
  "tasks":tasks,
  "weight_training_released":False
}
out=ROOT/"artifacts/train-failure-curriculum-v1.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:report[k] for k in [
  "status","failure_bank_count","train_source_failure_count",
  "excluded_reserved_failure_count","task_count",
  "all_sources_train_split","reserved_eval_derivative_count",
  "training_eligible_count","weight_training_released"
]},sort_keys=True))
