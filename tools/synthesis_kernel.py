#!/usr/bin/env python3
import json
ORDER={"VERIFIED":5,"SUPPORTED":4,"PRELIMINARY":3,"CONTRADICTORY":2,"FAILED":1,"UNKNOWN":0}
def synthesize(question,records):
    valid=[r for r in records if r.get("source_hash") and r.get("status") in ORDER]
    established=[r for r in valid if r["status"]=="VERIFIED"][:5]
    derived=[r for r in valid if r["status"] in ("SUPPORTED","PRELIMINARY")][:5]
    contradictions=[r for r in valid if r["status"]=="CONTRADICTORY"][:5]
    unknowns=[r for r in valid if r["status"]=="UNKNOWN"][:5]
    tests=[]
    for r in contradictions+unknowns:
        t=r.get("discriminating_test")
        if t and t not in tests: tests.append(t)
        if len(tests)==3: break
    refs=sorted({r["source_hash"] for r in established+derived+contradictions+unknowns})
    return {"question":question,
      "established":[r["claim"] for r in established],
      "derived":[r["claim"] for r in derived],
      "contradictions":[r["claim"] for r in contradictions],
      "unknowns":[r["claim"] for r in unknowns],
      "next_discriminating_test":tests,"evidence_refs":refs}
if __name__=="__main__":
    rs=[{"claim":"A","status":"VERIFIED","source_hash":"h1"},
        {"claim":"B","status":"CONTRADICTORY","source_hash":"h2","discriminating_test":"T1"},
        {"claim":"C","status":"UNKNOWN","source_hash":"h3","discriminating_test":"T2"},
        {"claim":"noise","status":"VERIFIED"}]
    s=synthesize("Q",rs)
    assert s["established"]==["A"] and s["contradictions"]==["B"] and "noise" not in str(s)
    print(json.dumps({"status":"VERIFIED","synthesis":s,"claim":"synthesis-format protocol test only"}))
