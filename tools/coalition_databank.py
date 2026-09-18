#!/usr/bin/env python3
import json,hashlib
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def packet(task, candidates, cached):
    key=h({"objective":task["objective"],"method":task["method"],"inputs":task.get("inputs",[])})
    if key in cached and cached[key].get("status")=="VERIFIED":
        return {"decision":"REUSE","work_hash":key,"source":cached[key]["artifact"],"reason":"verified identical work"}
    ranked=sorted(candidates,key=lambda f:(f["domain"]==task["domain"],f["method"]==task["method"],-f.get("load",0)),reverse=True)
    chosen=[]; deps=set()
    for f in ranked:
        # preserve methodological/dependency diversity where possible
        if not chosen or f["method"] not in {x["method"] for x in chosen} or not (set(f.get("dependencies",[])) & deps):
            chosen.append(f); deps|=set(f.get("dependencies",[]))
        if len(chosen)==3: break
    return {"decision":"EXECUTE","work_hash":key,"coalition":[f["id"] for f in chosen],
            "audit":{"shared_dependencies":len(deps)<sum(len(set(f.get("dependencies",[]))) for f in chosen),
                     "independent_evidence_not_assumed":True}}
if __name__=="__main__":
    task={"domain":"collatz","objective":"return obstruction","method":"algebra","inputs":["checkpoint"]}
    fs=[{"id":"F1","domain":"collatz","method":"algebra","dependencies":["A"],"load":0},
        {"id":"F3","domain":"collatz","method":"3-adic","dependencies":["B"],"load":0},
        {"id":"F33","domain":"collatz","method":"red-team","dependencies":["C"],"load":0}]
    a=packet(task,fs,{})
    key=a["work_hash"]; b=packet(task,fs,{key:{"status":"VERIFIED","artifact":"sha256:artifact"}})
    assert a["decision"]=="EXECUTE" and len(a["coalition"])==3 and b["decision"]=="REUSE"
    print(json.dumps({"status":"VERIFIED","execute":a,"reuse":b,"claim":"databank/orchestration protocol test only"}))
