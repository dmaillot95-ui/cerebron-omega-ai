#!/usr/bin/env python3
import json
FARMS={
60:("hardware-system-architecture","requirements-interfaces"),
61:("pcb-design","signal-power-integrity"),62:("embedded-firmware","mcu-fpga-rtos"),
63:("hardware-hil","fault-injection-E4"),64:("hardware-reliability","fmea-fmeda-derating"),
65:("physical-prototype","qualification-E5plus"),66:("knowledge-graph","vector-index"),
67:("cross-farm-communication","forum-agora-transport"),68:("experiment-orchestration","closed-loop-task-routing"),
69:("causal-discovery","causal-hypothesis-tests"),70:("theorem-proof-engineering","formal-proof-checking"),
71:("scientific-reproduction","independent-reproduction"),72:("reality-evidence-gate","claim-evidence-enforcement"),
73:("system-integration","qualification-gate")}
def qualify(existing_caps):
    seen=set(existing_caps); out={}
    for i,caps in FARMS.items():
        gain=[c for c in caps if c not in seen]
        out[f"F{i}"]={"status":"JUSTIFIED" if gain else "REJECT_REDUNDANT","new_capabilities":gain}
        seen.update(gain)
    return out
if __name__=="__main__":
    q=qualify({"engineering-systems","simulation-modeling","formal-audit","metrology"})
    assert len(q)==14 and all(v["status"]=="JUSTIFIED" for v in q.values())
    print(json.dumps({"status":"VERIFIED","qualified":q,"claim":"pre-qualification protocol test only"}))
