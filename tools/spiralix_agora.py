#!/usr/bin/env python3
import json, hashlib
def score(farm,task):
    domain=1 if task["domain"] in farm["domains"] else 0
    method=1 if task["method"] in farm["methods"] else 0
    independence=1 if not set(task.get("dependencies",[])) & set(farm.get("dependencies",[])) else 0
    return 4*domain+3*method+2*independence-farm.get("load",0)
def allocate(farms,task,k=3):
    ranked=sorted(farms,key=lambda f:(score(f,task),f["id"]),reverse=True)
    chosen=[]; methods=set()
    for f in ranked:
        if len(chosen)>=k: break
        if f["methods"]-methods or not chosen:
            chosen.append(f); methods|=f["methods"]
    return [f["id"] for f in chosen]
def triangulate(results):
    methods={r["method"] for r in results}; claims={r["claim"] for r in results}
    return {"method_diversity":len(methods),"agreement":len(claims)==1,
            "status":"SUPPORTED" if len(methods)>=3 and len(claims)==1 else "CONTRADICTORY" if len(claims)>1 else "PRELIMINARY"}
if __name__=="__main__":
    farms=[{"id":"F1","domains":{"collatz"},"methods":{"algebra"},"dependencies":{"A"},"load":0},
           {"id":"F3","domains":{"collatz"},"methods":{"3-adic"},"dependencies":{"B"},"load":0},
           {"id":"F33","domains":{"collatz"},"methods":{"red-team"},"dependencies":{"C"},"load":0},
           {"id":"F34","domains":{"collatz"},"methods":{"audit"},"dependencies":{"A"},"load":1}]
    task={"domain":"collatz","method":"algebra","dependencies":["A"]}
    coalition=allocate(farms,task,3)
    tri=triangulate([{"method":"algebra","claim":"X"},{"method":"3-adic","claim":"X"},{"method":"red-team","claim":"X"}])
    assert len(coalition)==3 and tri["status"]=="SUPPORTED"
    print(json.dumps({"status":"VERIFIED","coalition":coalition,"triangulation":tri,"claim":"allocation/triangulation protocol test only"}))
