#!/usr/bin/env python3
import json
def state(g):
    if not g["justified"]: return "PLANNED"
    if not g["bootstrap_manifest"]: return "JUSTIFIED"
    if not g["repository_exists"]: return "JUSTIFIED"
    if not g["scaffold_present"]: return "CREATED"
    if not g["workflow_success"]: return "SCAFFOLDED"
    if not g["integration_registered"]: return "TESTED"
    return "INTEGRATED"
if __name__=="__main__":
    blocked={"justified":True,"bootstrap_manifest":True,"repository_exists":False,"scaffold_present":False,"workflow_success":False,"integration_registered":False}
    tested={"justified":True,"bootstrap_manifest":True,"repository_exists":True,"scaffold_present":True,"workflow_success":True,"integration_registered":False}
    assert state(blocked)=="JUSTIFIED" and state(tested)=="TESTED"
    matrix={f"F{i}":state(blocked) for i in range(60,74)}
    print(json.dumps({"status":"VERIFIED","matrix":matrix,"claim":"readiness state-machine test only"}))
