from __future__ import annotations
import json,pathlib,re

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name): return json.loads((CFG/name).read_text())

def main():
    errors=[]
    c=load("agora-transfer-contract-v1.json")
    school=load("agora-school-v1.json")
    mode=load("cerebron-mode-v1.json")
    bind=load("cerebron-civilization-memory-bindings-v1.json")
    mem=load("memory-fabric-v1.json")
    active=set(mode.get("applies_to",[]))
    pending={"SAELION","ALPHA","OMEGA","DELTA","NEXUS"}

    if set(c.get("active_roles",[]))!=active: errors.append("contract active roles mismatch CEREBRON mode")
    if set(school.get("roles",[]))!=active: errors.append("AGORA school roles mismatch active roles")
    if {x["ai_id"] for x in c.get("pending_roles",[])}!=pending: errors.append("contract pending roles mismatch")
    if set(school.get("planned_roles",[]))!=pending: errors.append("AGORA planned roles mismatch")
    if pending & active: errors.append("pending role incorrectly active")

    if c.get("cross_ai_transfer",{}).get("default")!="DENY_DIRECT_COPY":
        errors.append("direct cross-AI copy must be denied")
    req=set(c.get("cross_ai_transfer",{}).get("allowed_only_if",[]))
    must={"SOURCE_PROVENANCE_PRESENT","CONTENT_SHA256_PRESENT","AUDIT_COMPLETE","DEDUP_COMPLETE","M6_NOT_SOURCE","RAW_AGORA_NOT_SOURCE"}
    if not must.issubset(req): errors.append("cross-AI transfer gate incomplete")
    if c.get("memory_classes",{}).get("cold_benchmark")!="M6_SEALED_DENY_TRAINING":
        errors.append("M6 rule missing")
    if "M6_NEVER_IN_TRAIN" not in c.get("hard_rules",[]): errors.append("M6 hard rule missing")
    if c.get("runtime_scope",{}).get("runtime_change") is not False:
        errors.append("runtime change must remain false")

    runtime=(ROOT/"runtime/agora_forum.py").read_text()
    m=re.search(r'ROLES=\{([^}]*)\}',runtime)
    historical=set(re.findall(r'"([^"]+)"',m.group(1))) if m else set()
    declared=set(c.get("runtime_scope",{}).get("historical_forum_supported_roles",[]))
    if historical!=declared: errors.append(f"historical runtime role declaration mismatch {sorted(historical^declared)}")
    if len(historical)!=8: errors.append("historical forum runtime expected 8-role scope")
    if historical==active: errors.append("historical runtime unexpectedly equals 14 active roles; audit contract needs review")
    if c.get("runtime_scope",{}).get("full_runtime_role_support") is not False:
        errors.append("full 14-role runtime support must not be claimed")

    bind_active={x["ai_id"] for x in bind.get("current_ai",[])}
    if bind_active!=active: errors.append("memory binding active set mismatch")
    if mem.get("classes",{}).get("M6",{}).get("deny_training") is not True:
        errors.append("memory fabric M6 deny_training missing")

    out={
      "schema":"CEREBRON_AGORA_TRANSFER_AUDIT_V1",
      "status":"PASS" if not errors else "FAIL",
      "active_roles":len(active),
      "pending_roles":len(pending),
      "historical_forum_runtime_roles":len(historical),
      "full_runtime_role_support":False,
      "direct_cross_ai_copy":"DENY",
      "runtime_change":False,
      "errors":errors
    }
    print(json.dumps(out,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
