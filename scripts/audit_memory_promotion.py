from __future__ import annotations
import json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name): return json.loads((CFG/name).read_text())

def main():
    errors=[]
    p=load("memory-promotion-policy-v1.json")
    fabric=load("memory-fabric-v1.json")
    bind=load("cerebron-civilization-memory-bindings-v1.json")
    mode=load("cerebron-mode-v1.json")
    farms=load("farms.json")
    rdx=load("rdx-knowledge-training-loop-v1.json")

    classes=p.get("classes",{})
    if set(classes)!={f"M{i}" for i in range(8)}:
        errors.append("M0-M7 class set incomplete")
    if classes.get("M6",{}).get("training_source") is not False:
        errors.append("M6 training_source must be false")
    if "NEVER_TRAIN_SOURCE" not in classes.get("M6",{}).get("absolute_rules",[]):
        errors.append("M6 absolute deny missing")
    if fabric.get("classes",{}).get("M6",{}).get("deny_training") is not True:
        errors.append("memory fabric M6 deny_training missing")

    active=set(p.get("active_namespaces",[]))
    expected_active={f"native-ai/{x}" for x in mode.get("applies_to",[])}
    if active!=expected_active:
        errors.append("active namespace set mismatch")

    pending=set(p.get("pending_namespaces",[]))
    expected_pending={x.get("namespace_reserved") for x in bind.get("planned_ai",[])}
    if pending!=expected_pending:
        errors.append("pending namespace set mismatch")

    pp=p.get("pending_namespace_policy",{})
    if pp.get("durable_classes_allowed_before_activation")!=["M7"]:
        errors.append("pending AI must allow only M7 before activation")
    denied=set(pp.get("durable_classes_denied_before_activation",[]))
    if denied!={"M1","M2","M3","M4","M5","M6"}:
        errors.append("pending deny class set mismatch")

    farm_count=len(farms.get("farms",[]))
    max_id=max((x.get("id",0) for x in farms.get("farms",[])),default=0)
    f72=p.get("live_gates",{}).get("F72",{})
    if f72.get("current")!="FAIL":
        errors.append("policy must reflect current F72 FAIL until fresh evidence passes")
    if f72.get("current_registry_count")!=farm_count:
        errors.append("F72 current_registry_count mismatch")
    ids=[x.get("id") for x in farms.get("farms",[])]
    if len(ids)!=len(set(ids)):
        errors.append("duplicate farm ids")
    if farms.get("max_farms")!=max_id:
        errors.append("max_farms must equal highest registered farm id")
    if farms.get("farm_ceiling")!=max_id:
        errors.append("farm_ceiling must equal highest registered farm id")
    if f72.get("current_registry_max_id")!=max_id:
        errors.append("F72 current_registry_max_id mismatch")
    gps=p.get("global_promotion_state","")
    if f72.get("current")!="PASS" and not gps.startswith("BLOCKED_PENDING_F72"):
        errors.append("global promotion must fail closed while F72 is not PASS")

    ingress=p.get("rdx_ingress",{})
    if ingress.get("source_farm_id")!=152:
        errors.append("RDX ingress must bind F152")
    if "RDX_TRAINING_ONLY_AFTER_M4_GOLD_PROMOTION" not in p.get("rules",[]):
        errors.append("RDX training M4 gate missing")
    if rdx.get("source",{}).get("farm_id")!=152:
        errors.append("RDX training loop source farm mismatch")
    if rdx.get("training_route",{}).get("auto_training") is not False:
        errors.append("RDX auto training must be false")
    if "M6_COLD_BENCHMARK" not in rdx.get("dataset_gate",{}).get("forbidden",[]):
        errors.append("RDX dataset gate must forbid M6")

    for rule in ["M6_NEVER_IN_TRAIN","LIVE_GATE_FAIL_BLOCKS_PROMOTION","PENDING_NAMESPACE_CANARY_DOES_NOT_ACTIVATE_AI"]:
        if rule not in p.get("rules",[]): errors.append(f"missing rule {rule}")

    out={
      "schema":"CEREBRON_MEMORY_PROMOTION_AUDIT_V2",
      "status":"PASS" if not errors else "FAIL",
      "farm_count":farm_count,
      "max_farm_id":max_id,
      "active_namespaces":len(active),
      "pending_namespaces":len(pending),
      "m6_training":"DENY",
      "pending_pre_activation_classes":["M7"],
      "f72_current":f72.get("current"),
      "m4_promotion":"OPEN" if f72.get("current")=="PASS" else "BLOCKED_BY_F72",
      "rdx_memory_ingress":"CONFIGURED",
      "rdx_auto_training":False,
      "errors":errors
    }
    print(json.dumps(out,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
