#!/usr/bin/env python3
import json,hashlib
FIELDS=("objective","method","configuration_id","input_hashes","engine","engine_version")
def key(t):
    x={k:t.get(k) for k in FIELDS}
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def schedule(task,verified,inflight):
    k=key(task)
    if k in verified:return {"decision":"REUSE_VERIFIED","work_key":k,"artifact":verified[k]}
    if k in inflight:return {"decision":"JOIN_INFLIGHT","work_key":k,"run_id":inflight[k]}
    return {"decision":"EXECUTE_NEW","work_key":k}
if __name__=="__main__":
    t={"objective":"Q","method":"M","configuration_id":"C","input_hashes":["h"],"engine":"python","engine_version":"3.12"}
    k=key(t)
    assert schedule(t,{k:"artifact:A"},{})["decision"]=="REUSE_VERIFIED"
    assert schedule(t,{}, {k:"run:1"})["decision"]=="JOIN_INFLIGHT"
    assert schedule(t,{}, {})["decision"]=="EXECUTE_NEW"
    print(json.dumps({"status":"VERIFIED","work_key":k,"claim":"anti-redundancy scheduling protocol test only"}))
