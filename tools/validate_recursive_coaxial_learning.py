#!/usr/bin/env python3
import json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/recursive_coaxial_learning_readiness.json"

def load(p):
    return json.loads((ROOT/p).read_text())

contract=load("training/CEREBRON_RECURSIVE_COAXIAL_VECTOR_LEARNING_V1.json")
coverage=load("config/all-ai-neural-training-coverage-v1.json")
gvl=load("config/gvl-specialization-registry-v2.json")
memory=load("config/memory-fabric-v1.json")
fabric=load("config/neural-training-fabric-v1.json")

errors=[]
warnings=[]

if contract["schema"]!="CEREBRON_RECURSIVE_COAXIAL_VECTOR_LEARNING_V1":
    errors.append("BAD_SCHEMA")
if contract["protected_scope"]["operational_do_not_modify_farms"] != [172,173,174]:
    errors.append("PROTECTED_FARMS_CHANGED")
if contract["training_policy"]["m6_deny_training"] is not True:
    errors.append("M6_NOT_DENIED")
if memory["classes"]["M6"].get("deny_training") is not True:
    errors.append("MEMORY_M6_NOT_DENIED")
if gvl.get("dimension") != 32:
    errors.append("GVL_DIMENSION_NOT_32")

blocked={"NU"}
eligible=[e for e in coverage["entries"] if e.get("available") is True and e.get("identity") not in blocked]
targets=contract["target_population"]["targets"]
target_ids={t["ai_id"] for t in targets}
eligible_ids={e["ai_id"] for e in eligible}
if target_ids != eligible_ids:
    errors.append("TARGET_COVERAGE_MISMATCH")
if len(targets)!=38 or contract["target_population"]["expected_count"]!=38:
    errors.append("TARGET_COUNT_NOT_38")
if any(t["identity"] in blocked for t in targets):
    errors.append("PROTECTED_OR_UNAVAILABLE_IDENTITY_IN_TARGETS")

gvl_by_identity={}
for a in gvl["ais"]:
    gvl_by_identity.setdefault(a["identity"],[]).append(a)
missing_vectors=[]
bad_vectors=[]
for t in targets:
    candidates=gvl_by_identity.get(t["identity"],[])
    if not candidates:
        missing_vectors.append(t["identity"]); continue
    v=candidates[0].get("specialization_vector",[])
    if len(v)!=32:
        bad_vectors.append(t["identity"])
if missing_vectors: errors.append("MISSING_GVL_VECTOR:"+",".join(sorted(missing_vectors)))
if bad_vectors: errors.append("BAD_GVL_VECTOR:"+",".join(sorted(bad_vectors)))

# Current real neural-training evidence in the allowed scope.
fabric_roles=fabric.get("roles",{})
trained_in_scope=[]
rollback_in_scope=[]
research_only=[]
for t in targets:
    ident=t["identity"]
    r=fabric_roles.get(ident)
    if not r:
        continue
    st=str(r.get("status",""))
    if "REAL_LORA" in st or "TRAINED" in st:
        trained_in_scope.append(ident)
    if "ROLLBACK" in st or "REVOKED" in st:
        rollback_in_scope.append(ident)
    if "RESEARCH_ONLY" in st:
        research_only.append(ident)

# Build non-destructive queue: the contract defines ordering, but no training is
# released here. Existing failed adapters require materially new data/method.
wave_order=[
    ("WAVE3A",["ELYSION","ELYSIUM","SAELION","NEXUS"]),
    ("WAVE3B",["ALPHA","DELTA","OMEGA"]),
    ("WAVE4",["BETA","GAMMA","EPSILON","ZETA","ETA"]),
    ("WAVE5",["THETA","IOTA","KAPPA","LAMBDA","MU"]),
    ("WAVE6",["XI","OMICRON","PI","RHO","SIGMA"]),
    ("WAVE7",["TAU","UPSILON","PHI","CHI","PSI"]),
    ("FINAL",["CEREBRON"]),
]
queue=[]
coverage_by_identity={e["identity"]:e for e in coverage["entries"]}
for wave,ids in wave_order:
    items=[]
    for ident in ids:
        e=coverage_by_identity.get(ident)
        if not e or e.get("identity") in blocked:
            continue
        items.append({
            "identity":ident,
            "coverage_state":e.get("coverage_state"),
            "training_mode":e.get("training_mode"),
            "release":"HOLD_UNTIL_ROLE_DATA_AND_GATES_READY"
        })
    queue.append({"wave":wave,"items":items})

parallel=contract["parallel_lanes"]
if len(parallel)<4:
    errors.append("INSUFFICIENT_PARALLEL_LANES")
if contract["training_policy"]["weights_changed_required_for_training_claim"] is not True:
    errors.append("WEIGHT_CHANGE_CLAIM_GATE_DISABLED")
required_prom=set(contract["promotion_gate"]["required"])
for req in ["WEIGHTS_OR_ADAPTER_CHANGED","COLD_GAIN_POSITIVE","TRANSFER_GAIN_POSITIVE","REDTEAM_NOT_WORSE","ABLATION_SUPPORTS_CAUSAL_VALUE","NO_CRITICAL_REGRESSION"]:
    if req not in required_prom:
        errors.append("MISSING_PROMOTION_REQUIREMENT:"+req)

# Learning-only exception for F172/F173/F174.
special=contract.get("special_case_learning",{})
if set(special) != {"PSI","AELYS","ELYRA"}:
    errors.append("SPECIAL_CASE_LEARNING_SCOPE_MISMATCH")
else:
    if special["PSI"].get("runtime_or_site_mutation") is not False:
        errors.append("PSI_OPERATIONAL_MUTATION_ALLOWED")
    if special["AELYS"].get("runtime_or_site_mutation") is not False:
        errors.append("AELYS_OPERATIONAL_MUTATION_ALLOWED")
    if special["AELYS"].get("prior_failed_adapter_must_not_be_reactivated") is not True:
        errors.append("AELYS_ROLLBACK_REACTIVATION_GUARD_MISSING")
    if special["ELYRA"].get("runtime_or_site_mutation") is not False:
        errors.append("ELYRA_OPERATIONAL_MUTATION_ALLOWED")
    if special["ELYRA"].get("must_preserve_physical_claim_boundary") is not True:
        errors.append("ELYRA_PHYSICAL_CLAIM_GUARD_MISSING")

growth=contract["geometric_growth_metric"]
if growth["current_claim"]!="NOT_ESTABLISHED" or growth["minimum_generations_for_claim"]<3:
    errors.append("GEOMETRIC_GROWTH_OVERCLAIM")

# Historical aggregate is diagnostic only, not an independence count.
history=fabric.get("wave2_parallel_lora",{})
if history.get("canonical_run_id") == contract["scheduling"]["no_repeat_wave2_run"]:
    warnings.append("WAVE2_CANONICAL_RUN_BLOCKED_FROM_REPEAT")

report={
    "schema":"CEREBRON_RECURSIVE_COAXIAL_VECTOR_READINESS_V1",
    "status":"PASS" if not errors else "FAIL",
    "operationally_protected_farms":[172,173,174],
    "operational_mutations_detected":0,
    "target_ai_count":len(targets),
    "gvl_dimension":gvl.get("dimension"),
    "parallel_lane_count":len(parallel),
    "real_training_already_executed_in_scope_count":len(set(trained_in_scope)),
    "real_training_already_executed_in_scope":sorted(set(trained_in_scope)),
    "rollback_or_revoked_in_scope":sorted(set(rollback_in_scope)),
    "research_only_in_scope":sorted(set(research_only)),
    "geometric_growth_claim":"NOT_ESTABLISHED",
    "next_queue":queue,
    "next_release_rule":"NO_WEIGHT_TRAINING_UNTIL_NEW_VALIDATED_GOLD_RED_ROLE_DATA + FROZEN_COLD/TRANSFER/RED + ABLATION PLAN",
    "agora_effect":"AGORA lessons become training candidates only after audit/counter-audit/reproduction and GOLD/RED admission.",
    "weights_effect":"Weights/adapters improve only after a real training run followed by positive sealed COLD and TRANSFER evidence; this validator itself changes no weights.",
    "warnings":warnings,
    "errors":errors
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
if errors:
    raise SystemExit(1)
