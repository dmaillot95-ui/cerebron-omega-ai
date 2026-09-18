#!/usr/bin/env python3
import json,sys
C=json.load(open("config/causal-action-gate.json"))
ALLOW=set(C["message_gate"]["allow_if_any"])
def gate(event):
    reasons=set(event.get("reasons",[]))
    allowed=bool(reasons & ALLOW)
    return {"emit_message":allowed,"matched":sorted(reasons&ALLOW),"chain":C["chain"],"status":"VERIFIED" if allowed else "SUPPRESSED"}
if __name__=="__main__": print(json.dumps(gate(json.load(sys.stdin)),ensure_ascii=False))
