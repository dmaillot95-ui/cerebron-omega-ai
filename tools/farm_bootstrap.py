#!/usr/bin/env python3
import json
FARMS={60:"hardware-architecture",61:"electronics-pcb",62:"embedded-firmware",63:"hardware-test-hil",
64:"hardware-reliability-safety",65:"physical-prototype-qualification",66:"knowledge-graph-vector-index",
67:"cross-farm-communication",68:"autonomous-experiment-orchestrator",69:"causal-discovery",
70:"theorem-proof-engineering",71:"scientific-reproduction",72:"reality-evidence-gate",
73:"system-integration-qualification"}
def manifest(i,d):
    return {"farm_id":f"F{i}","domain":d,"protocol":"SPIRALIX-OMEGA","evidence_ceiling":"E2-before-real-tests",
            "required":["README.md","farm.json","tools/spiralix_adapter.py",".github/workflows/spiralix-interop.yml"]}
if __name__=="__main__":
    ms=[manifest(i,d) for i,d in FARMS.items()]
    assert len(ms)==14 and ms[0]["farm_id"]=="F60" and ms[-1]["farm_id"]=="F73"
    assert all(m["evidence_ceiling"]=="E2-before-real-tests" for m in ms)
    print(json.dumps({"status":"VERIFIED","count":len(ms),"manifests":ms,"claim":"bootstrap manifest generation test only"}))
