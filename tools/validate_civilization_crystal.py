#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

top=json.loads((ROOT/"config/ai-8-agent-topology-v1.json").read_text())
cry=json.loads((ROOT/"config/crystal-preservation-v1.json").read_text())
mem=json.loads((ROOT/"config/memory-fabric-v1.json").read_text())
pm=json.loads((ROOT/"config/private-memory-route.json").read_text())
greek=json.loads((ROOT/"config/greek-24-colony-master.json").read_text())

assert top["per_ai_agent_slots"]==8
assert len(top["agent_template"])==8
assert len({x["slot"] for x in top["agent_template"]})==8
assert top["burst_pool"]["max_agents"]==20
assert top["runtime_changed"] is False

assert cry["no_overwrite"] is True
assert cry["runtime_changed"] is False
assert "APPEND_OR_VERSION_NEVER_DESTRUCTIVE_OVERWRITE" in cry["invariants"]
assert "rollback_targets" in cry["handoff_packet"]

assert "SCOPED_VERIFIED" in mem["status"]
assert mem["storage_targets"]["huggingface_private"]["status"]=="SCOPED_WRITE_READ_SHA_VERIFIED"
assert mem["ai_namespace_pattern"].startswith("ai/{ai_id}/agent/{agent_slot}/")

assert "SCOPED_VERIFIED" in pm["status"]
assert pm["routes"]["private_data_plane"]["availability"]=="VERIFIED_SCOPED"

assert greek["agent_slots_per_ai"]==8
assert len(greek["team_template"])==8
assert greek["burst_pool"]["max_agents"]==20

campaign=ROOT/"docs/CEREBRON_80_MESSAGE_CAMPAIGN_V1.md"
assert campaign.exists()
text=campaign.read_text()
assert "M80" in text
assert "20 REAL agents" in text

print(json.dumps({
    "status":"PASS",
    "agent_slots_per_ai":8,
    "burst_max_agents":20,
    "hf_private":"SCOPED_VERIFIED",
    "no_destructive_overwrite":True,
    "runtime_changed":False,
    "campaign_messages":80
}, sort_keys=True))
