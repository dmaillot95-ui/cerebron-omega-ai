#!/usr/bin/env python3
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
cp=json.loads((R/"checkpoints/CEREBRON_80_M01_CRYSTAL_BASELINE.json").read_text())
farms=json.loads((R/"config/farms.json").read_text())
top=json.loads((R/"config/ai-8-agent-topology-v1.json").read_text())
crystal=json.loads((R/"config/crystal-preservation-v1.json").read_text())
route=json.loads((R/"config/private-memory-route.json").read_text())
mem=json.loads((R/"config/memory-fabric-v1.json").read_text())

assert cp["message"]==1
assert cp["runtime_changed"] is False
assert farms["max_farms"]==172
assert farms["policy"]["farm_cap"]==172
assert len(farms["farms"])==172
assert {f["id"] for f in farms["farms"]}==set(range(1,173))
assert top["per_ai_agent_slots"]==8
assert top["burst_pool"]["max_agents"]==20
assert top["runtime_changed"] is False
assert crystal["no_overwrite"] is True
assert "APPEND_OR_VERSION_NEVER_DESTRUCTIVE_OVERWRITE" in crystal["invariants"]
assert route["routes"]["private_data_plane"]["availability"]=="VERIFIED_SCOPED"
assert mem["status"].startswith("CONTROL_PLANE_ACTIVE_HF_PRIVATE_SCOPED_VERIFIED")
missing=[f["id"] for f in farms["farms"] if f.get("infrastructure_status")=="BLOCKED_MISSING_REPOSITORY"]
assert missing==[162], missing

print(json.dumps({
 "status":"PASS",
 "campaign_message":1,
 "registry_count":len(farms["farms"]),
 "agent_slots_per_ai":top["per_ai_agent_slots"],
 "burst_pool_max":top["burst_pool"]["max_agents"],
 "hf_scope":"SCOPED_VERIFIED",
 "missing_repository_ids":missing,
 "runtime_changed":False,
 "no_destructive_overwrite":True
}, sort_keys=True))
