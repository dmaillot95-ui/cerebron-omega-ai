from __future__ import annotations
import json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name):
    return json.loads((CFG/name).read_text())

def fail(msg,errors):
    errors.append(msg)

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

    ids=[x["id"] for x in farms]
    if len(farms)!=146: fail(f"farm_count={len(farms)} expected=146",errors)
    if len(ids)!=len(set(ids)): fail("duplicate farm IDs",errors)
    if min(ids)!=1 or max(ids)!=146: fail(f"farm_range={min(ids)}..{max(ids)} expected=1..146",errors)

    by_id={x["id"]:x for x in farms}
    if by_id.get(145,{}).get("name")!="ELYSION": fail("F145 ELYSION missing",errors)
    if by_id.get(146,{}).get("name")!="ELYSIUM": fail("F146 ELYSIUM missing",errors)

    active=set(mode.get("applies_to",[]))
    school_roles=set(school.get("roles",[]))
    binding_active={x["ai_id"] for x in bind.get("current_ai",[])}
    mem_active=set(mem.get("native_ai",{}).get("active",[]))
    if school_roles!=active: fail(f"AGORA roles mismatch CEREBRON mode: {sorted(school_roles^active)}",errors)
    if binding_active!=active: fail(f"memory binding active mismatch: {sorted(binding_active^active)}",errors)
    if mem_active!=active: fail(f"memory fabric active mismatch: {sorted(mem_active^active)}",errors)

    planned={"SAELION","ALPHA","OMEGA","DELTA","NEXUS"}
    school_planned=set(school.get("planned_roles",[]))
    bind_planned={x["ai_id"] for x in bind.get("planned_ai",[])}
    mem_planned=set(mem.get("native_ai",{}).get("planned_not_active",[]))
    if school_planned!=planned: fail("AGORA planned roles mismatch",errors)
    if bind_planned!=planned: fail("memory binding planned roles mismatch",errors)
    if mem_planned!=planned: fail("memory fabric planned roles mismatch",errors)
    if planned & active: fail("planned AI incorrectly active",errors)
    farm_names={str(x.get("name","")).upper() for x in farms}
    if planned & farm_names: fail("planned AI prematurely inserted into farm registry",errors)

    slots=hf.get("slots",[])
    slot_ids=[x.get("slot_id") for x in slots]
    if len(slots)!=20 or len(set(slot_ids))!=20: fail("HF pool must contain 20 unique slots",errors)
    if hf.get("max_slots")!=20: fail("HF max_slots != 20",errors)
    if any(x.get("model_id") is not None for x in slots):
        fail("HF slot permanently bound without explicit admission update",errors)

    common="cerebron-omega/cerebron-private-memory"
    if mem.get("storage_targets",{}).get("huggingface_private",{}).get("common_memory_repo")!=common:
        fail("memory fabric common repo mismatch",errors)
    if bind.get("common_private_repo")!=common: fail("civilization binding common repo mismatch",errors)
    if hf.get("memory_route")!=common: fail("HF pool memory route mismatch",errors)
    if mode.get("memory",{}).get("common_private_repo")!=common: fail("CEREBRON mode common repo mismatch",errors)

    native_route=set(direct.get("routing_classes",{}).get("native_ai",[]))
    if native_route!={"F145","F146"}: fail("direct native_ai route must be F145/F146",errors)
    g12=next((g for g in arch.get("groups",[]) if g.get("id")=="G12"),None)
    if not g12 or set(g12.get("farms",[]))!={145,146}: fail("farm architecture G12 native AI mismatch",errors)

    if mem.get("classes",{}).get("M6",{}).get("deny_training") is not True:
        fail("M6 deny_training missing",errors)

    hfp=next((x for x in gateway.get("providers",[]) if x.get("id")=="huggingface"),None)
    if not hfp or hfp.get("elysion_memory_verification",{}).get("result")!="PASS":
        fail("latest ELYSION HF memory verification missing",errors)

    gh=next((x for x in providers.get("providers",[]) if x.get("id")=="GITHUB_ACTIONS_CPU"),None)
    if not gh or gh.get("state")!="QUALIFIED_SCOPED":
        fail("GitHub Actions CPU scoped qualification missing",errors)

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
