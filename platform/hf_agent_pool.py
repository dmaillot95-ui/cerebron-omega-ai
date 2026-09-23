from __future__ import annotations
import json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
CFG=ROOT/"config"/"hf-20-agent-pool-v1.json"
MODELS=ROOT/"config"/"model-bank-six.json"

def status():
    cfg=json.loads(CFG.read_text())
    bank=json.loads(MODELS.read_text())
    return {
        "schema":"CEREBRON_HF_AGENT_POOL_STATUS_V1",
        "provider":cfg["provider"],
        "max_slots":cfg["max_slots"],
        "default_active":cfg["default_active"],
        "pool_status":cfg["status"],
        "candidate_models":bank["candidates"],
        "claim_ceiling":"ROUTING_CAPACITY_CONFIGURED_MODEL_EXECUTION_REQUIRES_RUNTIME_RECEIPT",
    }

def select(farm_ids=None, requested_agents=1):
    cfg=json.loads(CFG.read_text())
    n=max(0,min(int(requested_agents),cfg["max_slots"]))
    farms=[int(x) for x in (farm_ids or [])]
    selected=[]
    for slot in cfg["slots"][:n]:
        item=dict(slot)
        item["farm_id"]=farms[len(selected)%len(farms)] if farms else None
        selected.append(item)
    return {
        "status":"ROUTED_SLOTS_NOT_EXECUTED",
        "selected":selected,
        "count":len(selected),
        "execution_requirement":"MODEL_RUNTIME_CANARY_PLUS_RECEIPT",
    }
