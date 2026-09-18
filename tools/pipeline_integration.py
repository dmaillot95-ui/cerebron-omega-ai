#!/usr/bin/env python3
import json
STAGES=["SPIRALIX","SYADRIX","COALITION_DATABANK","COLLAPSE_GATE","AGORA","MICRO_IMPULSE","FORUM","SYNTHESIS_KERNEL","EVIDENCE_GATE"]
def run(packet):
    trail=[]
    for stage in STAGES:
        trail.append({"stage":stage,"status":"PASS","evidence_level":packet["evidence_level"]})
        if packet.get("contradiction") and stage=="EVIDENCE_GATE":
            trail[-1]["status"]="BLOCK"
            return {"decision":"ROLLBACK","trail":trail,"source_hashes":packet["source_hashes"]}
    return {"decision":"COMMIT","trail":trail,"source_hashes":packet["source_hashes"]}
if __name__=="__main__":
    a=run({"evidence_level":"E2","source_hashes":["h1"],"contradiction":False})
    b=run({"evidence_level":"E2","source_hashes":["h1","h2"],"contradiction":True})
    assert a["decision"]=="COMMIT" and b["decision"]=="ROLLBACK"
    assert all(x["evidence_level"]=="E2" for x in a["trail"])
    assert b["source_hashes"]==["h1","h2"]
    print(json.dumps({"status":"VERIFIED","nominal":a["decision"],"contradiction":b["decision"],"claim":"pipeline integration protocol test only"}))
