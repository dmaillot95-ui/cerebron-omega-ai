#!/usr/bin/env python3
import json
def impulse(state,candidates):
    used=set(state.get("methods",[])); deps=set(state.get("dependencies",[]))
    ranked=sorted(candidates,key=lambda c:(
        c["method"] not in used,
        not bool(set(c.get("dependencies",[]))&deps),
        c.get("targets_unknown",False),
        -c.get("cost",1)),reverse=True)
    c=ranked[0]
    return {"task_id":"MICRO-1","farm_id":c["farm_id"],"method":c["method"],
            "target":state["central_unknown"],"baseline":state["signature"],
            "decision":"EXECUTE","claim":"targeted information-gain probe only"}
def evaluate(before,after):
    changed=before!=after
    return {"information_gain":1 if changed else 0,"decision":"KEEP" if changed else "ROLLBACK"}
if __name__=="__main__":
    s={"central_unknown":"return-obstruction","methods":["algebra"],"dependencies":["A"],"signature":"S0"}
    cs=[{"farm_id":"F1","method":"algebra","dependencies":["A"],"targets_unknown":True,"cost":1},
        {"farm_id":"F3","method":"3-adic","dependencies":["B"],"targets_unknown":True,"cost":1},
        {"farm_id":"F33","method":"red-team","dependencies":["C"],"targets_unknown":False,"cost":1}]
    x=impulse(s,cs); assert x["farm_id"]=="F3"
    e=evaluate("S0","S1"); assert e["decision"]=="KEEP"
    print(json.dumps({"status":"VERIFIED","impulse":x,"evaluation":e,"claim":"micro-impulse selection protocol test only"}))
