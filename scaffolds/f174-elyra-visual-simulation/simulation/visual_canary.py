#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()

def simulate(scenario_id: str, steps: int = 6):
    if steps < 2 or steps > 120:
        raise ValueError("steps must be between 2 and 120")
    frames=[]
    for i in range(steps):
        phase=i/(steps-1)
        frame={
            "frame":i,
            "t_norm":round(phase,6),
            "elyra_pose":{
                "x":round(0.25*phase,6),
                "y":0.0,
                "z":1.0,
                "yaw_deg":round(30.0*phase,6)
            },
            "world_state":{
                "scene":"CANARY_ROOM",
                "light":"STATIC",
                "contact_state":"NO_CONTACT"
            }
        }
        frames.append(frame)
    payload={
        "schema":"ELYRA_VISUAL_CANARY_RESULT_V1",
        "scenario_id":scenario_id,
        "simulation_kind":"DETERMINISTIC_VISUAL_STATE_SEQUENCE",
        "physical_model_claimed":False,
        "physical_validation_claimed":False,
        "frames":frames
    }
    raw=canonical(payload)
    payload["result_sha256"]=hashlib.sha256(raw).hexdigest()
    return payload

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario",default="F174-CANARY-001")
    ap.add_argument("--steps",type=int,default=6)
    ap.add_argument("--out",default="artifacts/f174_visual_canary.json")
    args=ap.parse_args()
    result=simulate(args.scenario,args.steps)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "status":"PASS",
        "scenario_id":result["scenario_id"],
        "frames":len(result["frames"]),
        "result_sha256":result["result_sha256"],
        "physical_validation_claimed":False
    },sort_keys=True))

if __name__=="__main__":
    main()
