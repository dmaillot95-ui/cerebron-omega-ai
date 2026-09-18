#!/usr/bin/env python3
import json,hashlib,datetime,pathlib,sys
CFG=json.load(open("config/session-memory-encyclopedia.json"))
def store(x):
    x=dict(x); x.setdefault("timestamp",datetime.datetime.now(datetime.timezone.utc).isoformat())
    seed=json.dumps(x,sort_keys=True,ensure_ascii=False).encode()
    x.setdefault("session_id","SESSION-"+hashlib.sha256(seed).hexdigest()[:16])
    missing=[k for k in CFG["capsule_fields"] if k not in x and k not in {"session_id","timestamp"}]
    if missing: raise ValueError("missing:"+",".join(missing))
    root=pathlib.Path("memory/sessions"); root.mkdir(parents=True,exist_ok=True)
    p=root/(x["session_id"]+".json"); p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
    idx=pathlib.Path("memory/latest.json"); idx.parent.mkdir(parents=True,exist_ok=True)
    idx.write_text(json.dumps({"session_id":x["session_id"],"path":str(p),"timestamp":x["timestamp"]},indent=2)+"\n")
    return {"session_id":x["session_id"],"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
if __name__=="__main__": print(json.dumps(store(json.load(sys.stdin)),ensure_ascii=False))
