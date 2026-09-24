from __future__ import annotations
import json, pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name):
    return json.loads((CFG/name).read_text())

def main():
    errors=[]
    farms=load("farms.json").get("farms",[])
    mode=load("cerebron-mode-v1.json")
    school=load("agora-school-v1.json")
    mem=load("memory-fabric-v1.json")
    bind=load("cerebron-civilization-memory-bindings-v1.json")
    hf=load("hf-20-agent-pool-v1.json")
    direct=load("cerebron-farm-direct-routing-v1.json")
    arch=load("farm-functional-architecture-v1.json")
    gateway=load("model-gateway.json")
    providers=load("runtime-provider-registry.json")
    simplified=load("cerebron-simplified-operating-model.json")
    preservation=load("farm-preservation-manifest.json")

    ids=[x["id"] for x in farms]
    if len(farms)!=146: errors.append(f"farm_count={len(farms)} expected=146")
    if len(ids)!=len(set(ids)): errors.append("duplicate farm IDs")
    if min(ids)!=1 or max(ids)!=146: errors.append("farm range mismatch")

    by_id={x["id"]:x for x in farms}
    if by_id.get(145,{}).get("name")!="ELYSION": errors.append("F145 ELYSION missing")
    if by_id.get(146,{}).get("name")!="ELYSIUM": errors.append("F146 ELYSIUM missing")

    active=set(mode.get("applies_to",[]))
    if set(school.get("roles",[]))!=active: errors.append("AGORA/CEREBRON active role mismatch")
    if {x["ai_id"] for x in bind.get("current_ai",[])}!=active: errors.append("memory binding active role mismatch")
    if set(mem.get("native_ai",{}).get("active",[]))!=active: errors.append("memory fabric active role mismatch")
    bind_rows=bind.get("current_ai",[])
    namespaces=[x.get("namespace") for x in bind_rows]
    if len(namespaces)!=len(set(namespaces)): errors.append("duplicate native AI memory namespace")
    for row in bind_rows:
        expected=f"native-ai/{row['ai_id']}"
        if row.get("namespace")!=expected: errors.append(f"noncanonical namespace for {row['ai_id']}")
        if row.get("durable_backend")!="cerebron-omega/cerebron-private-memory": errors.append(f"backend mismatch for {row['ai_id']}")
        if row.get("m6_training")!="DENY": errors.append(f"M6 training not denied for {row['ai_id']}")
        if row.get("raw_agora_training")!="DENY": errors.append(f"RAW AGORA training not denied for {row['ai_id']}")
        if row.get("cross_ai_blind_copy")!="DENY": errors.append(f"blind cross-copy not denied for {row['ai_id']}")

    planned={"SAELION","ALPHA","OMEGA","DELTA","NEXUS"}
    if set(school.get("planned_roles",[]))!=planned: errors.append("AGORA planned role mismatch")
    if {x["ai_id"] for x in bind.get("planned_ai",[])}!=planned: errors.append("memory planned role mismatch")
    if set(mem.get("native_ai",{}).get("planned_not_active",[]))!=planned: errors.append("memory fabric planned role mismatch")
    if planned & active: errors.append("planned AI incorrectly active")

    slots=hf.get("slots",[])
    if len(slots)!=20 or len({x.get("slot_id") for x in slots})!=20: errors.append("HF20 slot mismatch")
    if any(x.get("model_id") is not None for x in slots): errors.append("HF slot permanently bound without admission")

    common="cerebron-omega/cerebron-private-memory"
    if mem.get("storage_targets",{}).get("huggingface_private",{}).get("common_memory_repo")!=common: errors.append("memory fabric repo mismatch")
    if bind.get("common_private_repo")!=common: errors.append("civilization binding repo mismatch")
    if hf.get("memory_route")!=common: errors.append("HF pool memory route mismatch")
    if mode.get("memory",{}).get("common_private_repo")!=common: errors.append("CEREBRON mode memory route mismatch")

    if set(direct.get("routing_classes",{}).get("native_ai",[]))!={"F145","F146"}: errors.append("native AI direct route mismatch")
    g12=next((g for g in arch.get("groups",[]) if g.get("id")=="G12"),None)
    if not g12 or set(g12.get("farms",[]))!={145,146}: errors.append("G12 native AI group mismatch")

    if mem.get("classes",{}).get("M6",{}).get("deny_training") is not True: errors.append("M6 deny_training missing")
    hfp=next((x for x in gateway.get("providers",[]) if x.get("id")=="huggingface"),None)
    if not hfp or hfp.get("elysion_memory_verification",{}).get("result")!="PASS": errors.append("ELYSION HF memory verification missing")
    gh=next((x for x in providers.get("providers",[]) if x.get("id")=="GITHUB_ACTIONS_CPU"),None)
    if not gh or gh.get("state")!="QUALIFIED_SCOPED": errors.append("GitHub Actions CPU qualification missing")

    if "PRESERVE_74_FARMS" in simplified.get("invariants",[]): errors.append("stale 74-farm invariant")
    ss=simplified.get("registry_snapshot",{})
    if ss.get("count")!=146 or ss.get("max_id")!=146: errors.append("simplified registry snapshot mismatch")
    ps=preservation.get("scope",{})
    if ps.get("count")!=146 or ps.get("farms")!="F01-F146": errors.append("preservation scope mismatch")

    out={
        "schema":"CEREBRON_CIVILIZATION_CONFIG_AUDIT_V1",
        "status":"PASS" if not errors else "FAIL",
        "farm_count":len(farms),
        "max_farm_id":max(ids),
        "active_ai_count":len(active),
        "planned_ai_count":len(planned),
        "hf_slot_count":len(slots),
        "common_private_repo":common,
        "native_ai_farms":[145,146],
        "errors":errors
    }
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
