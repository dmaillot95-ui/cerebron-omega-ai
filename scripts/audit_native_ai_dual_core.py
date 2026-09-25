from __future__ import annotations
import json,pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name):
    return json.loads((CFG/name).read_text())

def main():
    errors=[]
    c=load("native-ai-dual-core-v1.json")
    farms=load("farms.json")["farms"]
    mode=load("cerebron-mode-v1.json")
    direct=load("cerebron-farm-direct-routing-v1.json")

    rows=c["native_ai"]
    expected={145:"ELYSION",146:"ELYSIUM",147:"SAELION",148:"ALPHA",149:"OMEGA",150:"DELTA",151:"NEXUS"}
    byfarm={x["farm_id"]:x for x in rows}
    reg={x["id"]:x for x in farms}

    if set(c["scope_farms"])!=set(expected):
        errors.append("scope must be F145-F151")
    if len(rows)!=7 or len(byfarm)!=7:
        errors.append("exactly seven unique native AI rows required")

    for fid,name in expected.items():
        row=byfarm.get(fid,{})
        if row.get("ai_id")!=name:
            errors.append(f"F{fid} ai_id mismatch")
        if reg.get(fid,{}).get("name")!=name:
            errors.append(f"registry mismatch F{fid}")
        for key in ("core_a","core_b","fusion"):
            if not row.get(key,{}).get("role"):
                errors.append(f"{name} missing {key} role")
        if row.get("core_a",{}).get("role")==row.get("core_b",{}).get("role"):
            errors.append(f"{name} core roles must differ")

    active=set(mode.get("applies_to",[]))
    pending_names={"SAELION","ALPHA","OMEGA","DELTA","NEXUS"}
    for name in sorted(pending_names):
        if name in active:
            errors.append(f"{name} prematurely runtime-active")

    routing=direct.get("routing_classes",{})
    active_routes=set(routing.get("native_ai",[]))
    pending_routes=set(routing.get("native_ai_pending_activation",[]))
    if active_routes!={"F145","F146"}:
        errors.append("native AI active route must remain F145/F146")
    if pending_routes!={"F147","F148","F149","F150","F151"}:
        errors.append("F147-F151 must remain activation-gated routes")

    gates={g["id"] for g in c.get("activation_gates",[])}
    if gates!={f"D{i}" for i in range(9)}:
        errors.append("D0-D8 gate set incomplete")

    pair=c["shared_architecture"]["default_candidate_pair"]
    if len(pair)!=2 or pair[0]["model_id"]==pair[1]["model_id"]:
        errors.append("two distinct core candidates required")
    if c["shared_architecture"].get("runtime_change") is not False:
        errors.append("runtime change must remain false")

    required_rules={
      "TWO_CORES_DO_NOT_EQUAL_TWO_INDEPENDENT_PROOFS",
      "DUAL_CORE_MUST_BE_ABLATED_AGAINST_BEST_SINGLE_CORE",
      "PENDING_NATIVE_AI_MUST_NOT_ENTER_ACTIVE_ROUTING",
      "M6_NEVER_IN_TRAIN"
    }
    if not required_rules.issubset(set(c.get("rules",[]))):
        errors.append("required dual-core rules missing")

    evaluated={}
    for name in sorted(pending_names):
        row=next(x for x in rows if x["ai_id"]==name)
        evaluated[name]={
            "project_state":row.get("project_state"),
            "dual_core_state":row.get("dual_core_state"),
            "D3":row.get("gate_status",{}).get("D3"),
            "D4":row.get("gate_status",{}).get("D4"),
            "runtime_routable":name in active
        }

    out={
      "schema":"CEREBRON_NATIVE_AI_DUAL_CORE_AUDIT_V2",
      "status":"PASS" if not errors else "FAIL",
      "native_ai_count":len(rows),
      "scope_farms":c["scope_farms"],
      "runtime_active_project_ids":sorted(active & {x["ai_id"] for x in rows}),
      "evaluation_progress_not_activation":evaluated,
      "active_route_tokens":sorted(active_routes),
      "pending_activation_route_tokens":sorted(pending_routes),
      "runtime_change":c["shared_architecture"]["runtime_change"],
      "errors":errors
    }
    print(json.dumps(out,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
