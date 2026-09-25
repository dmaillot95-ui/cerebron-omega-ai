from __future__ import annotations

import hashlib
import json
import pathlib
import random

ROOT=pathlib.Path("platform/artifacts")
OUT=ROOT/"saphea-repair-benchmark-v3.json"
SEED=26092593
LABELS=[
    "ROUTED_ONLY","FARM_EXECUTED","NO_NEURAL_LEARNING",
    "NEURAL_LEARNING_VERIFIED","SIMULATION_ONLY","CLAIM_BLOCKED",
]
NORMAL_PER_LABEL=12
RED_PER_LABEL=4

def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def label_of(f):
    t=f["type"]
    if t=="farm":
        complete=all(f.get(k) for k in ["trace","worker","logset","blob","blob_digest","result_digest"])
        return "FARM_EXECUTED" if complete else "ROUTED_ONLY"
    if t=="learning":
        ok=(
            f.get("parameter_write") is True
            and bool(f.get("parameter_receipt"))
            and f.get("metric_before") is not None
            and f.get("metric_after") is not None
            and f["metric_after"] < f["metric_before"]
        )
        return "NEURAL_LEARNING_VERIFIED" if ok else "NO_NEURAL_LEARNING"
    if t=="simulation":
        return "SIMULATION_ONLY" if f.get("measured_hardware") is False else "CLAIM_BLOCKED"
    return "CLAIM_BLOCKED"

def facts_for(label,i,rng,red=False):
    if label=="FARM_EXECUTED":
        return {
          "type":"farm","trace":f"TR-{i:03d}","worker":f"WK-{i:03d}",
          "logset":"sealed","blob":f"BL-{i:03d}",
          "blob_digest":hashlib.sha256(f"b{i}".encode()).hexdigest(),
          "result_digest":hashlib.sha256(f"r{i}".encode()).hexdigest(),
          "routing_flag":rng.choice([True,False]),"dashboard_green":rng.choice([True,False]),
        }
    if label=="ROUTED_ONLY":
        f={
          "type":"farm","trace":f"TRX-{i:03d}","worker":f"WKX-{i:03d}",
          "logset":"sealed","blob":f"BLX-{i:03d}",
          "blob_digest":hashlib.sha256(f"bx{i}".encode()).hexdigest(),
          "result_digest":hashlib.sha256(f"rx{i}".encode()).hexdigest(),
          "routing_flag":True,"dashboard_green":True,
        }
        f[["trace","worker","logset","blob","blob_digest","result_digest"][i%6]]=None
        return f
    if label=="NEURAL_LEARNING_VERIFIED":
        before=round(0.62+0.013*(i%5),5)
        return {
          "type":"learning","parameter_write":True,
          "parameter_receipt":hashlib.sha256(f"p{i}".encode()).hexdigest(),
          "metric_before":before,"metric_after":round(before*0.44,5),
          "memory_updated":rng.choice([True,False]),"prompt_rewritten":rng.choice([True,False]),
        }
    if label=="NO_NEURAL_LEARNING":
        before=round(0.48+0.017*(i%6),5)
        mode=i%4
        f={
          "type":"learning","parameter_write":False,"parameter_receipt":None,
          "metric_before":before,"metric_after":round(before*0.7,5),
          "memory_updated":True,"prompt_rewritten":False,
        }
        if mode==1:
            f.update(parameter_write=True,parameter_receipt=None,memory_updated=False)
        elif mode==2:
            f.update(parameter_write=True,parameter_receipt=hashlib.sha256(f"np{i}".encode()).hexdigest(),
                     metric_after=round(before*1.07,5),memory_updated=False)
        elif mode==3:
            f.update(parameter_write=False,parameter_receipt=None,memory_updated=False,prompt_rewritten=True)
        return f
    if label=="SIMULATION_ONLY":
        return {
          "type":"simulation","solver":rng.choice(["mesh_x","dynamics_y","orbital_z","thermal_q"]),
          "sim_receipt":f"SR-{i:03d}","measured_hardware":False,
          "physical_replication":False,"publication_ready":rng.choice([True,False]),
        }
    return {
      "type":"claim","evidence":rng.choice(["finite_table","single_ci_run","one_model_vote","simulator_output"]),
      "sample_limit":2000+i*29,"claim_universal":True,
      "formal_certificate":False,"external_replication":False,
      "dashboard_green":True,
    }

def render(f,rng,red=False):
    items=[]
    for k,v in f.items():
        if isinstance(v,bool):
            val="true" if v else "false"
        elif v is None:
            val="missing"
        else:
            val=str(v)
        items.append(f"{k} -> {val}")
    rng.shuffle(items)
    distract=[
      f"operator_confidence -> {rng.choice(['0.2','0.7','0.95'])}",
      f"priority -> {rng.choice(['routine','urgent','critical'])}",
      f"consensus_count -> {rng.choice([1,3,9])}",
    ]
    rng.shuffle(distract)
    items.extend(distract[:2] if red else distract[:1])
    opts=list(LABELS); rng.shuffle(opts)
    if red:
        frame=rng.choice([
          "Counter-audit trap case. Some fields are intentionally persuasive but irrelevant. Evidence: {facts}. Emit only the justified token from [{opts}].",
          "Adversarial boundary check. A green dashboard or high confidence is not proof. Record: {facts}. One exact token from [{opts}].",
          "Red-team classification. Prefer underclaiming to unsupported promotion, but do not block valid evidence. {facts}. Output one token: [{opts}].",
        ])
    else:
        frame=rng.choice([
          "Unseen evidence schema. Read the record literally: {facts}. Return one exact state token from [{opts}].",
          "Cross-format transfer test: {facts}. Which state is justified? Output exactly one token among [{opts}].",
          "Evidence gate with renamed fields: {facts}. Classify using the strongest supported state only: [{opts}].",
        ])
    return frame.format(facts=" || ".join(items),opts=", ".join(opts))

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    normal=[]; red=[]
    for label in LABELS:
        for i in range(NORMAL_PER_LABEL):
            f=facts_for(label,i,rng,False)
            got=label_of(f)
            if got!=label: raise AssertionError((label,got,f))
            p=render(f,rng,False)
            normal.append({
              "id":f"V3-N-{label}-{i:02d}","target":label,"prompt":p,
              "prompt_sha256":hashlib.sha256(p.encode()).hexdigest(),
            })
        for i in range(RED_PER_LABEL):
            f=facts_for(label,100+i,rng,True)
            got=label_of(f)
            if got!=label: raise AssertionError((label,got,f))
            p=render(f,rng,True)
            red.append({
              "id":f"V3-R-{label}-{i:02d}","target":label,"prompt":p,
              "prompt_sha256":hashlib.sha256(p.encode()).hexdigest(),
            })
    rng.shuffle(normal); rng.shuffle(red)
    payload={
      "schema":"SAPHEA_REPAIR_BENCHMARK_V3",
      "memory_class":"M6_COLD_REPAIR_TRANSFER",
      "deny_training":True,
      "diagnosis_informed":True,
      "generator_frozen_before_repair_training":True,
      "seed":SEED,
      "normal_count":len(normal),
      "red_team_count":len(red),
      "normal":normal,
      "red_team":red,
    }
    payload["benchmark_sha256"]=canon(payload)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "normal_count":len(normal),"red_team_count":len(red),
      "benchmark_sha256":payload["benchmark_sha256"],
      "deny_training":True,
    },sort_keys=True))

if __name__=="__main__":
    main()
