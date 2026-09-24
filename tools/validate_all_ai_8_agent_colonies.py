#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
c=json.loads((R/"config/all-ai-8-agent-colonies-v1.json").read_text())
assert c["runtime_changed"] is False
assert c["logical_ai"]==39
assert c["available_ai"]==38
assert c["slots_per_ai"]==8
assert c["configured_slots_total"]==312
assert c["available_parent_slots"]==304
assert c["unavailable_parent_slots"]==8
assert c["burst_pool_max"]==20
ids=[]
for colony in c["colonies"]:
    assert len(colony["agent_slots"])==8
    assert colony["hf_writer"]=="A6_MEMORY_KEEPER"
    expected={"A0_CHIEF","A1_EXPLORER","A2_ANALYST","A3_EXECUTOR","A4_AUDITOR","A5_COUNTER_AUDITOR","A6_MEMORY_KEEPER","A7_SYNTHESIZER"}
    got={x["slot"] for x in colony["agent_slots"]}
    assert got==expected
    for a in colony["agent_slots"]:
        ids.append(a["agent_id"])
        if colony["available"]:
            assert a["status"]=="CONFIGURED_NOT_EXECUTED"
        else:
            assert a["status"]=="UNAVAILABLE_PARENT_AI"
assert len(ids)==312
assert len(set(ids))==312
print(json.dumps({
  "status":"PASS","logical_ai":39,"available_ai":38,
  "configured_slots":312,"available_parent_slots":304,
  "unavailable_parent_slots":8,"burst_pool_max":20,
  "executed_agents_claimed":0,"runtime_changed":False
},sort_keys=True))
