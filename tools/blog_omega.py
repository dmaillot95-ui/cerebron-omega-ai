#!/usr/bin/env python3
import json,hashlib,datetime,pathlib,sys
CFG=json.load(open("config/blog-omega.json"))
def publish(x):
    missing=[k for k in CFG["required_fields"] if k not in x and k not in {"post_id","timestamp"}]
    if missing: raise ValueError("missing:"+",".join(missing))
    x=dict(x); x.setdefault("timestamp",datetime.datetime.now(datetime.timezone.utc).isoformat())
    seed=json.dumps(x,sort_keys=True,ensure_ascii=False).encode()
    x.setdefault("post_id","BLOG-"+hashlib.sha256(seed).hexdigest()[:16])
    if x["status"] not in CFG["statuses"]: raise ValueError("invalid status")
    pathlib.Path("blog/posts").mkdir(parents=True,exist_ok=True)
    p=pathlib.Path("blog/posts")/(x["post_id"]+".json")
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
    return {"post_id":x["post_id"],"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
if __name__=="__main__":
    print(json.dumps(publish(json.load(sys.stdin)),ensure_ascii=False))
