#!/usr/bin/env python3
import argparse, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/continuous-neural-training-v1.json").read_text())
COVER=json.loads((ROOT/"config/all-ai-neural-training-coverage-v1.json").read_text())

WAVE_RANK={w:i for i,w in enumerate(CFG["queue_order"])}
CLOSED=set(CFG["closed_roles"])
AVAILABLE={e["identity"]:e for e in COVER["entries"] if e.get("available")}
SAFE_WF=re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")

def canonical_sha(obj):
    x={k:v for k,v in obj.items() if k!="computed_release_sha256"}
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def discover():
    base=ROOT/"training"/"continuous-releases"
    rows=[]
    if not base.exists():
        return rows
    for p in sorted(base.glob("*.json")):
        try:
            r=json.loads(p.read_text())
        except Exception as e:
            rows.append({"path":str(p.relative_to(ROOT)),"eligible":False,"reason":"INVALID_JSON","error":type(e).__name__})
            continue
        path=str(p.relative_to(ROOT))
        reasons=[]
        if r.get("training_released") is not True: reasons.append("TRAINING_RELEASE_FALSE")
        if r.get("continuous_training_eligible") is not True: reasons.append("CONTINUOUS_ELIGIBLE_FALSE")
        if not r.get("release_sha256"): reasons.append("RELEASE_SHA_MISSING")
        roles=r.get("roles")
        if not isinstance(roles,list) or not roles: reasons.append("ROLES_MISSING")
        forbidden=json.dumps(r,sort_keys=True).upper()
        if r.get("uses_m6_as_training") is True: reasons.append("M6_IN_TRAIN_DENY")
        if r.get("uses_transfer_as_training") is True: reasons.append("TRANSFER_IN_TRAIN_DENY")
        if r.get("uses_red_as_training") is True or r.get("uses_adversarial_as_training") is True: reasons.append("RED_IN_TRAIN_DENY")
        wf=r.get("dispatch_workflow")
        if wf is not None and not SAFE_WF.fullmatch(str(wf)): reasons.append("UNSAFE_WORKFLOW_NAME")
        wave=r.get("wave")
        if wave not in WAVE_RANK: reasons.append("UNKNOWN_WAVE")
        tasks=[]
        if isinstance(roles,list):
            for role in roles:
                if role not in AVAILABLE:
                    tasks.append({"role":role,"eligible":False,"reason":"ROLE_UNAVAILABLE_OR_UNKNOWN"})
                    continue
                if role in CLOSED and r.get("materially_new_data_or_method") is not True:
                    tasks.append({"role":role,"eligible":False,"reason":"CLOSED_ROLE_REUSE_DENY"})
                    continue
                if role=="CEREBRON" and any(e.get("coverage_state","").startswith("PENDING_") and e["identity"]!="CEREBRON" for e in COVER["entries"] if e.get("available")):
                    tasks.append({"role":role,"eligible":False,"reason":"ORCHESTRATOR_TRAINS_LAST"})
                    continue
                tasks.append({"role":role,"eligible":True})
        row={
          "path":path,
          "release_id":r.get("release_id",p.stem),
          "wave":wave,
          "release_sha256":r.get("release_sha256"),
          "computed_release_sha256":canonical_sha(r),
          "eligible":len(reasons)==0 and any(t.get("eligible") for t in tasks),
          "reasons":reasons,
          "tasks":tasks,
          "dispatch_workflow":wf,
          "dispatch_ref":r.get("dispatch_ref","main"),
          "dispatch_inputs":r.get("dispatch_inputs",{}),
          "requires_rdx_f72":bool(r.get("requires_rdx_f72",False)),
          "scope":r.get("scope","ROLE")
        }
        if row["requires_rdx_f72"] and any(b["id"]=="PLATFORM_RDX_F72_FAIL" for b in CFG["current_known_blockers"]):
            row["eligible"]=False
            row["reasons"].append("KNOWN_RDX_F72_FAIL")
        rows.append(row)
    return rows

def plan(rows):
    candidates=[]
    for r in rows:
        if not r.get("eligible"): continue
        for t in r["tasks"]:
            if t.get("eligible"):
                candidates.append({
                  "role":t["role"],
                  "wave":r["wave"],
                  "release_id":r["release_id"],
                  "release_path":r["path"],
                  "release_sha256":r["release_sha256"],
                  "dispatch_workflow":r["dispatch_workflow"],
                  "dispatch_ref":r["dispatch_ref"],
                  "dispatch_inputs":r["dispatch_inputs"]
                })
    candidates.sort(key=lambda x:(WAVE_RANK.get(x["wave"],999),x["release_id"],x["role"]))
    selected=candidates[:CFG["max_parallel_real_trainings"]]
    requests=[]
    for x in selected:
        if x["dispatch_workflow"]:
            inp=dict(x["dispatch_inputs"])
            inp.setdefault("role",x["role"])
            inp.setdefault("release_path",x["release_path"])
            requests.append({
              "role":x["role"],
              "workflow":x["dispatch_workflow"],
              "ref":x["dispatch_ref"],
              "inputs":inp,
              "release_sha256":x["release_sha256"]
            })
    if requests:
        status="READY_TO_DISPATCH"
    elif selected:
        status="READY_NO_DISPATCH_CONTRACT"
    else:
        status="BLOCKED_NO_ELIGIBLE_RELEASE"
    return {
      "schema":"CEREBRON_CONTINUOUS_NEURAL_TRAINING_PLAN_V1",
      "status":status,
      "controller_status":CFG["status"],
      "max_parallel":CFG["max_parallel_real_trainings"],
      "discovered_release_count":len(rows),
      "eligible_task_count":len(candidates),
      "selected_count":len(selected),
      "selected":selected,
      "dispatch_requests":requests,
      "known_blockers":CFG["current_known_blockers"],
      "next_pending_wave":"WAVE3A",
      "next_pending_roles":["ELYSION","ELYSIUM","SAELION","NEXUS"],
      "training_executed":False,
      "weights_changed":False,
      "claim_boundary":"PLANNER_OUTPUT_NE_TRAINING_EXECUTION"
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="artifacts/continuous-neural-training-plan-v1.json")
    ap.add_argument("--dispatch-output",default="artifacts/continuous-neural-training-dispatch-v1.json")
    args=ap.parse_args()
    rows=discover()
    out=plan(rows)
    out["releases"]=rows
    out["plan_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
    p=ROOT/args.output
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    d=ROOT/args.dispatch_output
    d.write_text(json.dumps({"schema":"CEREBRON_CONTINUOUS_TRAINING_DISPATCH_V1","requests":out["dispatch_requests"]},indent=2)+"\n")
    print(json.dumps({k:out[k] for k in ["status","max_parallel","discovered_release_count","eligible_task_count","selected_count","next_pending_wave","next_pending_roles","plan_sha256"]},ensure_ascii=False))

if __name__=="__main__":
    main()
