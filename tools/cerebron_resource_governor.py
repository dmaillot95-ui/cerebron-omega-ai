#!/usr/bin/env python3
"""CEREBRON resource governor planner.

Plans logical AI work into bounded waves. It does not execute models.
"""
import json, hashlib, argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/cerebron-resource-governor-v1.json").read_text())

PRIORITY={name:i for i,name in enumerate(CFG["priority_order"])}

def work_key(task):
    body={
      "objective":task.get("objective"),
      "method":task.get("method"),
      "configuration_id":task.get("configuration_id"),
      "input_hashes":task.get("input_hashes",[]),
      "engine":task.get("engine"),
      "engine_version":task.get("engine_version"),
      "model_id":task.get("model_id"),
      "model_revision":task.get("model_revision")
    }
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def classify(task):
    c=str(task.get("execution_class","")).upper()
    if c in CFG["execution_classes"]:
        return c
    if task.get("training"):
        return "TRAINING"
    if task.get("model_id"):
        size=float(task.get("model_size_b",0) or 0)
        return "HEAVY" if size>=3 else "MEDIUM"
    return "LIGHT"

def plan(tasks, verified=None, inflight=None):
    verified=verified or {}
    inflight=inflight or {}
    caps=CFG["limits"]
    prepared=[]
    for n,t0 in enumerate(tasks):
        t=dict(t0)
        t["ordinal"]=n
        t["work_key"]=work_key(t)
        t["execution_class"]=classify(t)
        if t["work_key"] in verified:
            t["decision"]="REUSE_VERIFIED"
            t["reuse_artifact"]=verified[t["work_key"]]
        elif t["work_key"] in inflight:
            t["decision"]="JOIN_INFLIGHT"
            t["join_run_id"]=inflight[t["work_key"]]
        else:
            t["decision"]="QUEUE"
        prepared.append(t)

    queued=[t for t in prepared if t["decision"]=="QUEUE"]
    queued.sort(key=lambda t:(PRIORITY.get(t.get("priority","OPTIONAL_EXPLORATION"),999),t["ordinal"]))

    waves=[]
    remaining=list(queued)
    while remaining:
        wave=[]
        heavy=0
        training=0
        heavy_lineages=set()
        used_lineage_loads={}
        next_remaining=[]
        for t in remaining:
            cls=t["execution_class"]
            lineage=(t.get("model_id"),t.get("model_revision")) if t.get("model_id") else None
            can=True
            if cls=="HEAVY":
                if heavy>=caps["default_heavy_model_parallelism"]:
                    can=False
                if lineage and lineage not in heavy_lineages and len(heavy_lineages)>=caps["default_distinct_heavy_lineages_parallel"]:
                    can=False
                if lineage and used_lineage_loads.get(lineage,0)>=caps["per_model_lineage_heavy_loads_default"]:
                    # Compatible same-lineage tasks should be batched behind one load.
                    t["batch_with_lineage"]=True
            elif cls=="TRAINING":
                if training>=caps["training_parallelism_max"]:
                    can=False
            elif cls=="LIGHT":
                if sum(1 for x in wave if x["execution_class"]=="LIGHT")>=caps["light_jobs_parallelism_soft"]:
                    can=False
            if can:
                t["decision"]="EXECUTE_IN_WAVE"
                t["wave_index"]=len(waves)+1
                wave.append(t)
                if cls=="HEAVY":
                    heavy+=1
                    if lineage:
                        heavy_lineages.add(lineage)
                        used_lineage_loads[lineage]=used_lineage_loads.get(lineage,0)+1
                elif cls=="TRAINING":
                    training+=1
            else:
                next_remaining.append(t)
        if not wave:
            raise RuntimeError("resource planner deadlock")
        waves.append(wave)
        remaining=next_remaining

    return {
      "schema":"CEREBRON_RESOURCE_PLAN_V1",
      "status":"PLANNED_NOT_EXECUTED",
      "task_count":len(tasks),
      "reuse_verified_count":sum(t["decision"]=="REUSE_VERIFIED" for t in prepared),
      "join_inflight_count":sum(t["decision"]=="JOIN_INFLIGHT" for t in prepared),
      "queued_new_count":len(queued),
      "wave_count":len(waves),
      "waves":[
        {
          "wave_index":i+1,
          "task_count":len(w),
          "heavy_count":sum(t["execution_class"]=="HEAVY" for t in w),
          "training_count":sum(t["execution_class"]=="TRAINING" for t in w),
          "distinct_heavy_lineages":len({(t.get("model_id"),t.get("model_revision")) for t in w if t["execution_class"]=="HEAVY"}),
          "tasks":w
        } for i,w in enumerate(waves)
      ],
      "nonexecuted_decisions":[t for t in prepared if t["decision"] in ("REUSE_VERIFIED","JOIN_INFLIGHT")],
      "claim_boundary":"PLAN_ONLY_NOT_EXECUTION"
    }

def selftest():
    tasks=[]
    for i in range(38):
        tasks.append({
          "ai_id":f"AI-{i+1:02d}",
          "objective":f"mission-{i+1}",
          "method":"inference",
          "configuration_id":"test",
          "input_hashes":[f"h{i}"],
          "engine":"transformers",
          "engine_version":"4",
          "model_id":"Qwen/Qwen3-4B" if i%2==0 else "HuggingFaceTB/SmolLM3-3B",
          "model_revision":"qrev" if i%2==0 else "srev",
          "model_size_b":4 if i%2==0 else 3,
          "priority":"BACKGROUND_RESEARCH"
        })
    out=plan(tasks)
    assert out["task_count"]==38
    assert all(w["heavy_count"]<=CFG["limits"]["default_heavy_model_parallelism"] for w in out["waves"])
    assert all(w["distinct_heavy_lineages"]<=CFG["limits"]["default_distinct_heavy_lineages_parallel"] for w in out["waves"])
    assert sum(w["task_count"] for w in out["waves"])==38
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selftest",action="store_true")
    ap.add_argument("--output",default="artifacts/cerebron-resource-governor-selftest.json")
    args=ap.parse_args()
    if not args.selftest:
        raise SystemExit("use --selftest")
    out=selftest()
    p=ROOT/args.output
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "status":out["status"],
      "task_count":out["task_count"],
      "wave_count":out["wave_count"],
      "max_heavy":max(w["heavy_count"] for w in out["waves"]),
      "max_lineages":max(w["distinct_heavy_lineages"] for w in out["waves"])
    },sort_keys=True))

if __name__=="__main__":
    main()
