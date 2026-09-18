#!/usr/bin/env python3
import json, hashlib, argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"config"/"glyph-vector.json"

def load_spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))

def encode(domain,objective,method,evidence_level,validation,priority,task_type,payload=None):
    spec=load_spec()
    if evidence_level not in spec["evidence_scale"]:
        raise ValueError("invalid evidence_level")
    obj={"language":spec["language"],"layer":spec["layer"],"vector":{"domain":domain,"objective":objective,"method":method,"evidence_level":evidence_level,"validation":validation,"priority":priority,"task_type":task_type},"payload":payload or {}}
    canonical=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    obj["sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    return obj

def verify(obj):
    spec=load_spec()
    required=spec["vector"]
    if obj.get("language")!=spec["language"]: return False,"LANGUAGE_MISMATCH"
    if any(k not in obj.get("vector",{}) for k in required): return False,"VECTOR_INCOMPLETE"
    if obj["vector"]["evidence_level"] not in spec["evidence_scale"]: return False,"EVIDENCE_INVALID"
    x=dict(obj); claimed=x.pop("sha256",None)
    canonical=json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    actual=hashlib.sha256(canonical.encode()).hexdigest()
    return claimed==actual, "VERIFIED" if claimed==actual else "HASH_MISMATCH"

def route(obj):
    ok,status=verify(obj)
    if not ok: return {"status":"REJECTED","reason":status}
    d=obj["vector"]["domain"].lower(); t=obj["vector"]["task_type"].lower()
    rules=[("collatz","cerebron-collatz-theory-farm"),("literature","cerebron-farm-48-global-scientific-literature-intelligence"),("research","cerebron-farm-08-research-web"),("cad","cerebron-farm-49-engineering-cad-digital-twin"),("struct","cerebron-farm-51-architecton-struct"),("cfd","cerebron-farm-52-architecton-cfd"),("thermal","cerebron-farm-53-architecton-thermal"),("multiphysics","cerebron-farm-54-architecton-multiphysics"),("electrical","cerebron-farm-55-architecton-electrical"),("control","cerebron-farm-56-architecton-control"),("cam","cerebron-farm-57-architecton-cam"),("metrology","cerebron-farm-58-architecton-metrology"),("learn","cerebron-farm-59-verified-learning")]
    for key,farm in rules:
        if key in d or key in t: return {"status":"ROUTED","farm":farm,"packet_sha256":obj["sha256"]}
    return {"status":"UNKNOWN","farm":None,"packet_sha256":obj["sha256"]}

def decode(obj):
    ok,status=verify(obj)
    if not ok: raise ValueError(status)
    v=obj["vector"]
    return f'{obj["language"]}: domain={v["domain"]}; objective={v["objective"]}; method={v["method"]}; evidence={v["evidence_level"]}; validation={v["validation"]}; priority={v["priority"]}; task={v["task_type"]}'

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test:
        x=encode("collatz","global-cycle-closure","H-coupling x 3-adic","E2","VERIFY","high","reason",{"claim":"finite evidence only"})
        ok,status=verify(x)
        print(json.dumps({"verify":status,"route":route(x),"decoded":decode(x),"sha256":x["sha256"]},ensure_ascii=False))
        raise SystemExit(0 if ok and route(x)["status"]=="ROUTED" else 1)
