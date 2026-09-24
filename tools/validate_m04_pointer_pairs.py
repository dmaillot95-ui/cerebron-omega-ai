#!/usr/bin/env python3
import json,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/"config/m04-pointer-manifest.json").read_text())
assert m["campaign_message"]==4
assert m["runtime_changed"] is False
assert m["verified_ai_count"]==38
assert len(m["entries"])==38

def get_json(repo,commit,path):
    owner,name=repo.split("/",1)
    url=f"https://raw.githubusercontent.com/{owner}/{name}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        return json.loads(r.read())

for e in m["entries"]:
    p=get_json(m["f74"]["repo"],m["f74"]["commit"],e["f74_path"])
    i=get_json(m["f66"]["repo"],m["f66"]["commit"],e["f66_path"])
    assert p["ai_id"]==e["ai_id"]
    assert i["ai_id"]==e["ai_id"]
    assert p["payload_sha256"]==e["payload_sha256"]
    assert i["payload_sha256"]==e["payload_sha256"]
    assert p["private_object_path"]==e["hf_remote_object"]
    assert i["f74_path"]==e["f74_path"]
    assert i["f74_commit"]==m["f74"]["commit"]
    assert p["privacy"]=="PRIVATE_PAYLOAD_NOT_STORED_HERE"
    assert i["privacy"]=="OPAQUE_POINTER_ONLY"
    assert p["rollback_status"]=="FIRST_VERSION_NO_PRIOR_POINTER"

print(json.dumps({
  "status":"PASS",
  "verified_pairs":len(m["entries"]),
  "f74_commit":m["f74"]["commit"],
  "f66_commit":m["f66"]["commit"],
  "rollback":"FIRST_VERSION_NO_PRIOR_POINTER",
  "next":"M05_SECOND_VERSION_ROLLBACK_TEST",
  "runtime_changed":False
},sort_keys=True))
