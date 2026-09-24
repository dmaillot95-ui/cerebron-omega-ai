from __future__ import annotations
import json, pathlib, re, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config"

def load(name):
    return json.loads((CFG/name).read_text())

def main():
    errors=[]
    pool=load("hf-20-agent-pool-v1.json")
    budget=load("cerebron-agent-budget-v1.json")
    admission=load("model-runtime-admission-policy.json")
    providers=load("runtime-provider-registry.json")
    bank=load("model-bank-six.json")

    slots=pool.get("slots",[])
    expected=[f"HF-A{i:02d}" for i in range(1,21)]
    got=[x.get("slot_id") for x in slots]
    if got!=expected: errors.append("slot IDs/order must be HF-A01..HF-A20")
    if pool.get("max_slots")!=20 or pool.get("default_active")!=0: errors.append("pool capacity/default mismatch")
    if budget.get("capacity",{}).get("max_agent_slots")!=20: errors.append("budget max slots mismatch")
    if budget.get("capacity",{}).get("permanent_identity") is not False: errors.append("permanent identity must be false")
    for s in slots:
        if s.get("status")!="ROUTABLE_RUNTIME_GATED": errors.append(f"{s.get('slot_id')} bad status")
        if s.get("model_id") is not None or s.get("model_revision") is not None: errors.append(f"{s.get('slot_id')} prematurely model-bound")
        if s.get("farm_id") is not None: errors.append(f"{s.get('slot_id')} prematurely farm-bound")
    required=set(pool.get("required_receipt",[]))
    must={"execution_id","slot_id","farm_id","model_id","model_revision","provider","prompt_hash","data_lineage","result_hash","latency_ms","completion_status"}
    if not must.issubset(required): errors.append("required receipt fields incomplete")
    if "AGENT_COUNT_NOT_EVIDENCE_COUNT" not in pool.get("rules",[]): errors.append("agent count evidence rule missing")
    if "SAME_MODEL_OR_LINEAGE_IS_CORRELATED_NOT_INDEPENDENT_EVIDENCE"!=pool.get("independence"): errors.append("independence policy mismatch")
    if pool.get("memory_route")!="cerebron-omega/cerebron-private-memory": errors.append("HF memory route mismatch")

    qualified={(x["model_id"],x["revision"]) for x in admission.get("current",{}).get("models",[]) if x.get("status")=="PASS"}
    if ("Qwen/Qwen3-4B","1cfa9a7208912126459214e8b04321603b3df60c") not in qualified:
        errors.append("Qwen runtime qualification missing")
    if ("HuggingFaceTB/SmolLM3-3B","a07cc9a04f16550a088caea529712d1d335b0ac1") not in qualified:
        errors.append("Smol runtime qualification missing")
    gha=next((x for x in providers.get("providers",[]) if x.get("id")=="GITHUB_ACTIONS_CPU"),{})
    if gha.get("state")!="QUALIFIED_SCOPED": errors.append("GitHub Actions CPU not scoped-qualified")

    bank_models={(x.get("model"),x.get("revision")) for x in bank.get("candidates",[])}
    for pair in qualified:
        if pair not in bank_models: errors.append(f"qualified model absent from model bank: {pair[0]}")

    out={
      "schema":"CEREBRON_HF20_POOL_AUDIT_V1",
      "status":"PASS" if not errors else "FAIL",
      "slot_count":len(slots),
      "default_active":pool.get("default_active"),
      "permanent_model_bindings":sum(x.get("model_id") is not None for x in slots),
      "permanent_farm_bindings":sum(x.get("farm_id") is not None for x in slots),
      "qualified_runtime_models":sorted([f"{a}@{b}" for a,b in qualified]),
      "independence":"SLOT_ID_NOT_INDEPENDENT_EVIDENCE",
      "errors":errors
    }
    print(json.dumps(out,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
