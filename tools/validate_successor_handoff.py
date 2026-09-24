#!/usr/bin/env python3
import hashlib,json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
p=R/"checkpoints/CEREBRON_80_M02_SUCCESSOR_HANDOFF.json"
h=json.loads(p.read_text())

def git_blob_sha(path: Path) -> str:
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

assert h["message"]==2
assert h["runtime_changed"] is False
assert h["registry"]["farm_count"]==172
assert h["registry"]["farm_cap"]==172
assert h["registry"]["greek_infrastructure_present"]==23
assert h["agents"]["per_ai_slots"]==8
assert h["agents"]["burst_pool_max"]==20
assert h["memory"]["verification_scope"]=="SCOPED_VERIFIED_NOT_GLOBAL"
assert h["memory"]["write_policy"]=="APPEND_OR_VERSION_NEVER_DESTRUCTIVE_OVERWRITE"
assert h["training"]["m6"]=="NEVER_IN_TRAIN"
assert len(h["civilization_tasks"])==5
assert all(x["enabled"] for x in h["civilization_tasks"])
parent=R/h["parent_checkpoint"]["path"]
assert parent.exists()
assert git_blob_sha(parent)==h["parent_checkpoint"]["git_blob_sha"]
for item in h["authoritative_files"]:
    fp=R/item["path"]
    assert fp.exists(), item["path"]
    actual=git_blob_sha(fp)
    assert actual==item["git_blob_sha"], (item["path"],actual,item["git_blob_sha"])
assert "CONTINUE_CAMPAIGN_AT_M03" in h["successor_protocol"]
print(json.dumps({
  "status":"PASS",
  "message":2,
  "authoritative_files_verified":len(h["authoritative_files"]),
  "civilization_tasks":len(h["civilization_tasks"]),
  "agent_slots_per_ai":h["agents"]["per_ai_slots"],
  "burst_pool_max":h["agents"]["burst_pool_max"],
  "hf_scope":h["memory"]["verification_scope"],
  "open_blockers":len(h["open_blockers"]),
  "next":h["next_message"]["id"],
  "runtime_changed":False
},sort_keys=True))
