#!/usr/bin/env python3
import json,hashlib
def compile_mission(q):
    core={"objective":q["objective"],"central_unknown":q["central_unknown"],"inputs":sorted(q.get("input_hashes",[]))}
    mid=hashlib.sha256(json.dumps(core,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]
    return {"mission_id":"M-"+mid,**core,"reuse_policy":"REUSE_VERIFIED_OR_JOIN_INFLIGHT",
      "coalition_requirements":{"min_method_diversity":3,"independent_evidence_not_assumed":True},
      "validation":["counterexample","formal-audit","replication"],
      "evidence_ceiling":q.get("evidence_ceiling","E2"),
      "stop_conditions":["VERIFIED_REUSE","NO_INFORMATION_GAIN","CONTRADICTION_REQUIRES_REDESIGN"]}
if __name__=="__main__":
    q={"objective":"Collatz return obstruction","central_unknown":"universal obstruction preventing nontrivial return","input_hashes":["checkpoint-66"],"evidence_ceiling":"E2"}
    a=compile_mission(q); b=compile_mission(q)
    assert a==b and a["mission_id"].startswith("M-") and a["coalition_requirements"]["min_method_diversity"]==3
    print(json.dumps({"status":"VERIFIED","mission":a,"claim":"R&D mission compilation protocol test only"}))
