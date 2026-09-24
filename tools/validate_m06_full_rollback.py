#!/usr/bin/env python3
import json,glob
from pathlib import Path
R=Path(__file__).resolve().parents[1]
latest=R/"receipts/p03/m06-hf-full-rollback-latest.json"
if not latest.exists():
    raise SystemExit("M06_LATEST_RECEIPT_MISSING")
ptr=json.loads(latest.read_text())
p=R/ptr["receipt"]
x=json.loads(p.read_text())
assert x["schema"]=="CEREBRON_M06_FULL_ROLLBACK_RECEIPT_V1"
assert str(x["run_id"])==str(ptr["run_id"])
assert str(x["parent_run_id"])=="35996621664"
assert x["hf_commit_mode"]=="SINGLE_BATCH_COMMIT_38_OBJECTS"
assert x["status"]=="PASS"
assert x["summary"]=={"available":38,"passed":38,"failed":0,"unavailable":1}
assert len(x["results"])==38
assert x["unavailable"]==[{"ai_id":"F162-NU","reason":"REPOSITORY_MISSING"}]
seen=set()
for r in x["results"]:
    assert r["ai_id"] not in seen
    seen.add(r["ai_id"])
    assert r["status"]=="PASS"
    assert str(r["parent_run_id"])=="35996621664"
    assert r["new_parent_metadata"]=="PASS"
    assert r["rollback_read"]=="PASS"
    assert r["parent_unchanged_after_new_write"]=="PASS"
    assert r["new_sha256"]==r["new_read_sha256"]
print(json.dumps({
  "status":"PASS",
  "run_id":x["run_id"],
  "parent_run_id":x["parent_run_id"],
  "available":38,
  "passed":38,
  "failed":0,
  "unavailable":1,
  "hf_commit_mode":"SINGLE_BATCH_COMMIT_38_OBJECTS"
},sort_keys=True))
