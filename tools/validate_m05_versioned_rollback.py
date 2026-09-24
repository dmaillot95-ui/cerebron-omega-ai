#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
latest=ROOT/"receipts/p03/m05-hf-rollback-latest.json"
if not latest.exists():
    raise SystemExit("M05_LATEST_RECEIPT_MISSING")
ptr=json.loads(latest.read_text())
p=ROOT/ptr["receipt"]
r=json.loads(p.read_text())
assert str(r["run_id"])==str(ptr["run_id"])
assert str(r["parent_run_id"])=="35996621664"
assert r["status"]=="PASS"
assert r["summary"]=={"sample":7,"passed":7,"failed":0}
assert len(r["results"])==7
for x in r["results"]:
    assert x["status"]=="PASS"
    assert x["rollback_read"]=="PASS"
    assert x["parent_unchanged_after_new_write"]=="PASS"
    assert "/35996621664.json" in x["parent_object"]
print(json.dumps({
    "status":"PASS",
    "run_id":r["run_id"],
    "parent_run_id":r["parent_run_id"],
    "sample":7,
    "rollback_verified":7
},sort_keys=True))
