#!/usr/bin/env python3
"""SPIRALIX Forum Ω — deterministic, auditable forum protocol.
Transport/state layer only. Consensus is never promoted to evidence.
"""
import json, hashlib, argparse, uuid
from datetime import datetime, timezone
from pathlib import Path

TYPES={"QUESTION","HYPOTHESIS","RESULT","COUNTEREXAMPLE","EVIDENCE","AUDIT","CHALLENGE","SYNTHESIS"}
STATUSES={"OPEN","SUPPORTED","CONTRADICTORY","VERIFIED","FAILED","UNKNOWN","CLOSED"}
EVIDENCE={f"E{i}" for i in range(9)}

def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()

def make_post(farm_id,thread_id,msg_type,claim,evidence_level="E0",status="OPEN",reply_to=None,artifacts=None,dependencies=None):
    if msg_type not in TYPES: raise ValueError("invalid type")
    if status not in STATUSES: raise ValueError("invalid status")
    if evidence_level not in EVIDENCE: raise ValueError("invalid evidence")
    body={"protocol":"SPIRALIX-FORUM-OMEGA/0.1","post_id":str(uuid.uuid4()),"thread_id":thread_id,
          "farm_id":farm_id,"reply_to":reply_to,"type":msg_type,"claim":claim,
          "evidence_level":evidence_level,"status":status,"artifacts":artifacts or [],
          "dependencies":dependencies or [],"timestamp":datetime.now(timezone.utc).isoformat()}
    body["sha256"]=digest(body)
    return body

def verify(p):
    x=dict(p); claimed=x.pop("sha256",None)
    return claimed==digest(x)

def independent(a,b):
    return not (set(a.get("dependencies",[])) & set(b.get("dependencies",[])))

def gate(posts):
    valid=[p for p in posts if verify(p)]
    return {"valid_posts":len(valid),"invalid_posts":len(posts)-len(valid),
            "rule":"CONSENSUS != TRUTH; shared dependencies are not independent evidence",
            "independent_pairs":sum(independent(valid[i],valid[j]) for i in range(len(valid)) for j in range(i+1,len(valid)))}

def self_test():
    a=make_post("F1","collatz-demo","HYPOTHESIS","candidate lemma","E0",dependencies=["source:A"])
    b=make_post("F34","collatz-demo","AUDIT","audit pending","E0",reply_to=a["post_id"],dependencies=["source:A"])
    c=make_post("F33","collatz-demo","CHALLENGE","independent red-team","E0",reply_to=a["post_id"],dependencies=["source:B"])
    assert all(map(verify,[a,b,c]))
    assert not independent(a,b) and independent(a,c)
    print(json.dumps({"status":"VERIFIED","gate":gate([a,b,c]),"claim":"forum protocol test only"},ensure_ascii=False))

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: self_test()
