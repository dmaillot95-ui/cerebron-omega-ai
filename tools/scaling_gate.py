#!/usr/bin/env python3
import json
DIMS=("domain","method","dependency","engine","evidence_reach","failure_detection")
def signature(x): return {d:set(x.get(d,[])) for d in DIMS}
def assess(existing,candidate):
    base={d:set() for d in DIMS}
    for e in existing:
        for d,v in signature(e).items(): base[d]|=v
    c=signature(candidate)
    gain={d:sorted(c[d]-base[d]) for d in DIMS}
    n=sum(bool(v) for v in gain.values())
    if n>=2: decision="SCALE"
    elif n==1: decision="EXTEND_EXISTING"
    else: decision="REJECT_REDUNDANT"
    return {"decision":decision,"capability_gain":gain,"gain_dimensions":n}
if __name__=="__main__":
    existing=[{"domain":["math"],"method":["algebra"],"dependency":["A"],"engine":["python"],"evidence_reach":["E2"],"failure_detection":["assert"]}]
    redundant={"domain":["math"],"method":["algebra"],"dependency":["A"],"engine":["python"],"evidence_reach":["E2"],"failure_detection":["assert"]}
    useful={"domain":["math"],"method":["formal"],"dependency":["B"],"engine":["lean"],"evidence_reach":["E2"],"failure_detection":["proof-check"]}
    assert assess(existing,redundant)["decision"]=="REJECT_REDUNDANT"
    assert assess(existing,useful)["decision"]=="SCALE"
    print(json.dumps({"status":"VERIFIED","redundant":assess(existing,redundant),"useful":assess(existing,useful),"claim":"scaling decision protocol test only"}))
