#!/usr/bin/env python3
import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/corrective_curriculum_g1_tasks.json"

def load(p):
    return json.loads((ROOT/p).read_text())

curr=load("training/CEREBRON_CORRECTIVE_CURRICULUM_G1_V1.json")
coverage=load("config/all-ai-neural-training-coverage-v1.json")
failures=load("memory/failure-bank-v1.json")
gvl=load("config/gvl-specialization-registry-v2.json")
routing=load("config/cerebron-failure-curriculum-routing-v1.json")

available={e["identity"]:e for e in coverage["entries"] if e.get("available") is True}
targets=set(curr["ai_corrective_axes"])
expected=set(available)
if targets != expected:
    missing=sorted(expected-targets); extra=sorted(targets-expected)
    raise SystemExit(f"TARGET_ROSTER_MISMATCH missing={missing} extra={extra}")

vec_by_identity={}
for a in gvl["ais"]:
    vec_by_identity.setdefault(a["identity"],a)
missing_vec=[x for x in sorted(targets) if x not in vec_by_identity or len(vec_by_identity[x].get("specialization_vector",[]))!=32]
if missing_vec:
    raise SystemExit("MISSING_32D_VECTOR:"+",".join(missing_vec))

# Map direct/relevant measured failures plus explicit cross-specialist routes.
direct={}
route_reasons={}
class_routes=routing.get("class_routes",{})
overrides=routing.get("explicit_failure_overrides",{})
for f in failures["entries"]:
    ai=str(f.get("AI_ID",""))
    routed=set(class_routes.get(f.get("FAILURE_CLASS"),{}).get("specialists",[]))
    override=overrides.get(f.get("FAILURE_ID"),{})
    routed.update(override.get("specialists",[]))
    for ident in targets:
        direct_match=(ident in ai or ai in ("ALL_38_LOGICAL_AI","ALL_AVAILABLE_LOGICAL_AI"))
        routed_match=ident in routed
        if direct_match or routed_match:
            direct.setdefault(ident,[]).append(f)
            reasons=[]
            if direct_match: reasons.append("SOURCE_AI_OR_GLOBAL_SCOPE")
            if routed_match: reasons.append("FAILURE_CLASS_SPECIALIST_ROUTE")
            route_reasons.setdefault((ident,f.get("FAILURE_ID")),reasons)

task_types=[
    ("BOUNDARY_CONTRAST","Generate a pair of superficially similar cases whose correct treatment differs on the target skill boundary."),
    ("SURFACE_TRANSFER","Re-express the same underlying skill in a different vocabulary/domain surface without copying benchmark wording."),
    ("COUNTEREXAMPLE","Construct a case that breaks an overgeneralized rule and explain the exact failing assumption."),
    ("CALIBRATED_ABSTENTION","Create a case where the correct action is to preserve UNKNOWN/HOLD rather than force a confident answer.")
]

tasks=[]
for ident in sorted(targets):
    e=available[ident]
    axes=curr["ai_corrective_axes"][ident]
    refs=[]
    for f in direct.get(ident,[]):
        refs.append({
            "failure_id":f.get("FAILURE_ID"),
            "failure_class":f.get("FAILURE_CLASS"),
            "signature":f.get("FAILURE_SIGNATURE"),
            "repair_status":f.get("REPAIR_STATUS"),
            "root_cause":f.get("ROOT_CAUSE"),
            "curriculum_targets":f.get("CURRICULUM_TARGETS",[]),
            "route_reasons":route_reasons.get((ident,f.get("FAILURE_ID")),[])
        })
    for i,(kind,instruction) in enumerate(task_types):
        axis=axes[i % len(axes)]
        body={
            "task_id":f"G1-{ident}-{i+1:02d}",
            "target_ai":ident,
            "ai_id":e["ai_id"],
            "kind":kind,
            "corrective_axis":axis,
            "instruction":instruction,
            "specialization_tags":e.get("specialization_tags",[]),
            "specialization_vector":vec_by_identity[ident]["specialization_vector"],
            "source_failure_refs":refs[:8],
            "response_contract":[
                "ATTEMPT",
                "ASSUMPTIONS",
                "EVIDENCE_NEEDED",
                "COUNTEREXAMPLE_OR_LIMIT",
                "CONFIDENCE",
                "UNKNOWN"
            ],
            "training_eligible":False,
            "cold_benchmark_eligible":False,
            "requires":["AUDIT","COUNTER_AUDIT","REPRODUCTION","GOLD_OR_RED_ADMISSION"],
            "forbidden":[
                "COPY_FROZEN_M6_TRANSFER_RED_ANSWERS",
                "SELF_CERTIFY_AS_GOLD",
                "COUNT_SHARED_MODEL_AS_INDEPENDENT_EVIDENCE"
            ]
        }
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        body["task_sha256"]=hashlib.sha256(raw).hexdigest()
        tasks.append(body)

# Add fusion-specific tasks only where D4 learning is relevant.
fusion_targets=["ELYSION","ELYSIUM","ALPHA","OMEGA","NEXUS"]
for ident in fusion_targets:
    for kind in ("ROUTE_OR_FUSE","ABSTAIN_OR_FALLBACK"):
        body={
            "task_id":f"G1-{ident}-FUSION-{kind}",
            "target_ai":ident,
            "kind":kind,
            "corrective_axis":"ROUTER_FUSION",
            "instruction":"Given two model candidates and their disagreement metadata, choose A, B, FUSE, or HOLD using only observable task/domain/confidence features. Never use the hidden gold answer.",
            "response_contract":["DECISION","REASON","DEPENDENCY_WARNING","FALLBACK","CONFIDENCE"],
            "training_eligible":False,
            "requires":["FRESH_HOLDOUT","AUDIT","ABLATION_VS_BEST_SINGLE"],
            "forbidden":["ORACLE_LABEL_AS_ROUTER_FEATURE","MAJORITY_VOTE_AS_EVIDENCE","FORCE_FUSION"]
        }
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        body["task_sha256"]=hashlib.sha256(raw).hexdigest()
        tasks.append(body)

report={
    "schema":"CEREBRON_CORRECTIVE_CURRICULUM_G1_TASK_PACK_V1",
    "status":"CANDIDATE_TASKS_BUILT_NOT_TRAINING_DATA",
    "target_ai_count":len(targets),
    "base_task_count":len(targets)*len(task_types),
    "fusion_task_count":len(fusion_targets)*2,
    "task_count":len(tasks),
    "tasks":tasks,
    "admission_chain":["AGORA_ATTEMPT","AUDIT","COUNTER_AUDIT","REPRODUCTION","GOLD_OR_RED","DATASET_SEAL"],
    "failure_routing_schema":routing.get("schema"),
    "failure_class_route_count":len(class_routes),
    "training_released":False,
    "geometric_growth_claim":"NOT_ESTABLISHED"
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:report[k] for k in ["status","target_ai_count","base_task_count","fusion_task_count","task_count","training_released"]},sort_keys=True))
