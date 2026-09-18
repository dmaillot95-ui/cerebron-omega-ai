#!/usr/bin/env python3
import json
def decide(a,b):
    if a["hash"]==b["hash"]: return "MERGE_REFERENCE"
    if a["claim"]!=b["claim"]: return "KEEP_CONTRADICTION"
    shared=bool(set(a.get("dependencies",[])) & set(b.get("dependencies",[])))
    if shared: return "MERGE_REFERENCE"
    if a.get("method")!=b.get("method"): return "KEEP_INDEPENDENT"
    return "RECOMPUTE_REQUIRED"
if __name__=="__main__":
    base={"claim":"P","method":"algebra","dependencies":["A"],"hash":"h1"}
    assert decide(base,{**base})=="MERGE_REFERENCE"
    assert decide(base,{"claim":"P","method":"audit","dependencies":["B"],"hash":"h2"})=="KEEP_INDEPENDENT"
    assert decide(base,{"claim":"not-P","method":"red-team","dependencies":["C"],"hash":"h3"})=="KEEP_CONTRADICTION"
    assert decide(base,{"claim":"P","method":"algebra","dependencies":["B"],"hash":"h4"})=="RECOMPUTE_REQUIRED"
    print(json.dumps({"status":"VERIFIED","claim":"collapse decision protocol test only"}))
