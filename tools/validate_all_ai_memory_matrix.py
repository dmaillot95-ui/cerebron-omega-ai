#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
m=json.loads((R/"config/all-ai-memory-matrix-v1.json").read_text())
assert m["campaign_message"]==3
assert m["runtime_changed"] is False
assert m["total_logical_ai"]==39
assert m["available_ai"]==38
assert m["unavailable_ai"]==1
assert len(m["entries"])==39
assert len({x["ai_id"] for x in m["entries"]})==39
assert len({x["namespace"] for x in m["entries"]})==39
nu=[x for x in m["entries"] if x["identity"]=="NU"]
assert len(nu)==1 and nu[0]["available"] is False
for x in m["entries"]:
    assert x["namespace"].endswith("/agent/A6_MEMORY_KEEPER")
    if x["available"]:
        assert x["hf_write_read_sha"] in {"PENDING_M03_CANARY","HF_DIRECT_VERIFIED"}
    else:
        assert x["hf_write_read_sha"]=="UNAVAILABLE_REPOSITORY_MISSING"
print(json.dumps({
 "status":"PASS","logical_ai":39,"available":38,"unavailable":1,
 "unique_namespaces":39,"runtime_changed":False
},sort_keys=True))
