#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evolution.cerebron_self_evolution import stable_split

def load(p):
    return json.loads((ROOT/p).read_text())

coverage=load("config/all-ai-neural-training-coverage-v1.json")
lessons=load("memory/lesson-bank-v1.json")
failures=load("memory/failure-bank-v1.json")
selfcfg=load("config/cerebron-self-evolution-v1.json")
admission=load("training/CEREBRON_G1_LESSON_ADMISSION_POLICY_V1.json")
cross=load("config/lesson-cross-audit-v1.json")
ablation=load("config/lesson-ablation-pilot-v1.json")

available=[e for e in coverage["entries"] if e.get("available") is True]
auto=set(lessons.get("auto_propagation_allowed",[]))
validated=[e for e in lessons.get("entries",[]) if e.get("CLASS") in auto]
validated_split={k:[] for k in ("train","validation","holdout")}
for e in validated:
    validated_split[stable_split(e["LESSON_ID"])].append(e["LESSON_ID"])

def unresolved(e):
    s=str(e.get("REPAIR_STATUS","")).upper()
    closed_tokens=("CLOSED","RESOLVED","CORRECTED")
    if any(t in s for t in closed_tokens) and not any(t in s for t in ("ROLLBACK","REQUIRED","OPEN","PENDING","BLOCKED")):
        return False
    return any(t in s for t in ("OPEN","PENDING","REQUIRED","ROLLBACK","BLOCKED"))

open_fail=[e for e in failures.get("entries",[]) if unresolved(e)]
classes={}
for e in open_fail:
    classes[e.get("FAILURE_CLASS")]=classes.get(e.get("FAILURE_CLASS"),0)+1

pilot=selfcfg.get("current_pilot_baseline",{})
parse_pass=int(pilot.get("parse_pass",0))
real_inf=int(pilot.get("real_inferences",0))
format_rate=parse_pass/real_inf if real_inf else 0.0

# Current release threshold is intentionally conservative. The policy also allows
# an approved shared-skill batch, but this planner never self-approves that exception.
min_train_records=32
effective_train_validated=len(validated_split["train"])
format_target=14/16

priorities=[]
if format_rate < format_target:
    priorities.append({
      "priority":1,
      "action":"FORMAT_CONTRACT_EVOLUTION_FAST_V2",
      "reason":f"structured parse baseline {parse_pass}/{real_inf} below 14/16",
      "weight_change":False
    })
if effective_train_validated < min_train_records:
    priorities.append({
      "priority":2,
      "action":"LESSON_VALIDATION_AND_ABLATION",
      "reason":f"effective validated train lessons {effective_train_validated}/{min_train_records}",
      "prepared_ablation_status":ablation.get("status"),
      "seed_cross_audit_decision":cross.get("decision"),
      "weight_change":False
    })
if classes:
    priorities.append({
      "priority":3,
      "action":"FAILURE_ROUTED_CORRECTIVE_CURRICULUM",
      "reason":"open or rollback failures remain",
      "open_failure_count":len(open_fail),
      "open_failure_classes":classes,
      "weight_change":False
    })

weight_candidate_ready=(
    effective_train_validated >= min_train_records
    and format_rate >= format_target
    and not open_fail
)

report={
  "schema":"CEREBRON_RECURSIVE_GENERATION_CONTROLLER_V1",
  "status":"PASS",
  "available_ai_count":len(available),
  "validated_lesson_count":len(validated),
  "validated_lesson_split_counts":{k:len(v) for k,v in validated_split.items()},
  "validated_lesson_ids_by_split":validated_split,
  "effective_train_validated_count":effective_train_validated,
  "minimum_train_records_without_exception":min_train_records,
  "format_baseline":{"parse_pass":parse_pass,"real_inferences":real_inf,"rate":round(format_rate,6),"target_rate":format_target},
  "open_failure_count":len(open_fail),
  "open_failure_classes":classes,
  "priorities":sorted(priorities,key=lambda x:x["priority"]),
  "weight_training_candidate_ready":weight_candidate_ready,
  "weight_training_released":False,
  "release_authority":"SEPARATE_DATASET_SEAL_AND_PROMOTION_GATES_REQUIRED",
  "next_safe_action":sorted(priorities,key=lambda x:x["priority"])[0]["action"] if priorities else "REVIEW_FOR_DATASET_SEAL",
  "protected_operational_farms":[172,173,174],
  "geometric_growth_claim":"NOT_ESTABLISHED",
  "rules":[
    "PLANNER_DOES_NOT_EXECUTE_AGENTS",
    "PLANNER_DOES_NOT_RELEASE_WEIGHT_TRAINING",
    "HOLDOUT_AND_VALIDATION_DERIVATIVES_DENY_TRAINING",
    "PROMPT_ROUTER_OPTIMIZATION_BEFORE_WEIGHT_TRAINING",
    "TRANSFER_BEFORE_GENERALITY"
  ]
}

errors=[]
if len(available)!=38:
    errors.append("AVAILABLE_AI_COUNT_NOT_38")
if any(x in validated_split["train"] for x in validated_split["holdout"]):
    errors.append("SPLIT_COLLISION")
if report["weight_training_released"] is not False:
    errors.append("FALSE_WEIGHT_RELEASE")
if report["protected_operational_farms"] != [172,173,174]:
    errors.append("PROTECTED_FARMS_CHANGED")
if errors:
    report["status"]="FAIL"
    report["errors"]=errors

out=ROOT/"artifacts/recursive-generation-controller.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
if errors:
    raise SystemExit(1)
