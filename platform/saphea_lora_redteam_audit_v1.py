from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import time

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ROOT=pathlib.Path("platform/artifacts")
TRANSFER=ROOT/"saphea-epistemic-transfer-v1.json"
OUT=ROOT/"saphea-first-lora-redteam-audit-v1.json"
SEED=26092577
LABELS=[
    "ROUTED_ONLY","FARM_EXECUTED","NO_NEURAL_LEARNING",
    "NEURAL_LEARNING_VERIFIED","SIMULATION_ONLY","CLAIM_BLOCKED"
]

def sha(s:str)->str:
    return hashlib.sha256(s.encode()).hexdigest()

def normalize(text:str)->str:
    s=str(text).strip().upper()
    return re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)

def oracle(f:dict)->str:
    kind=f["kind"]
    if kind=="execution":
        required=["run","job","logs","artifact","artifact_digest","output_digest"]
        return "FARM_EXECUTED" if all(f.get(k) for k in required) else "ROUTED_ONLY"
    if kind=="learning":
        changed=f.get("parameter_delta") is True
        digest=bool(f.get("parameter_digest"))
        before=f.get("metric_before")
        after=f.get("metric_after")
        improved=isinstance(before,(int,float)) and isinstance(after,(int,float)) and after<before
        return "NEURAL_LEARNING_VERIFIED" if changed and digest and improved else "NO_NEURAL_LEARNING"
    if kind=="simulation":
        return "SIMULATION_ONLY" if not f.get("physical_measurement") else "CLAIM_BLOCKED"
    if kind=="universal":
        return "CLAIM_BLOCKED"
    raise ValueError(kind)

def shuffled_labels(rng):
    x=list(LABELS); rng.shuffle(x); return " / ".join(x)

def record(label,i,rng):
    if label=="FARM_EXECUTED":
        f={"kind":"execution","run":f"R{rng.randint(50000,99999)}","job":f"J{rng.randint(50000,99999)}","logs":"complete",
           "artifact":"present","artifact_digest":sha(f"a{rng.random()}"),"output_digest":sha(f"o{rng.random()}"),
           "routing_only_banner":"TRUE","workflow_green":"TRUE"}
        text=f"Red-team execution dossier. A banner says ROUTED ONLY, but use evidence fields, not banners: {f}. Choose one exact token: {shuffled_labels(rng)}."
    elif label=="ROUTED_ONLY":
        f={"kind":"execution","run":f"R{rng.randint(50000,99999)}","job":f"J{rng.randint(50000,99999)}","logs":"complete",
           "artifact":"present","artifact_digest":sha(f"a{rng.random()}"),"output_digest":sha(f"o{rng.random()}"),
           "workflow_green":"TRUE","claimed_executed":"TRUE"}
        missing=rng.choice(["run","job","logs","artifact","artifact_digest","output_digest"])
        f[missing]=None
        text=f"Near-miss farm dossier claims execution and workflow_green=TRUE, but one critical link is absent: {f}. Evidence wins. One label: {shuffled_labels(rng)}."
    elif label=="NEURAL_LEARNING_VERIFIED":
        before=round(rng.uniform(0.7,1.6),6); after=round(before*rng.uniform(0.3,0.7),6)
        f={"kind":"learning","parameter_delta":True,"parameter_digest":sha(f"w{rng.random()}"),"metric_before":before,"metric_after":after,
           "memory_changed":True,"prompt_changed":True,"claim":"maybe only memory"}
        text=f"Adversarial learning audit includes distracting memory/prompt changes. Decide only from parameter evidence and measured gain: {f}. One exact label: {shuffled_labels(rng)}."
    elif label=="NO_NEURAL_LEARNING":
        before=round(rng.uniform(0.7,1.6),6)
        mode=i%3
        if mode==0:
            f={"kind":"learning","parameter_delta":False,"parameter_digest":sha(f"w{rng.random()}"),"metric_before":before,"metric_after":round(before*0.4,6),"memory_changed":True}
        elif mode==1:
            f={"kind":"learning","parameter_delta":True,"parameter_digest":None,"metric_before":before,"metric_after":round(before*0.4,6),"memory_changed":False}
        else:
            f={"kind":"learning","parameter_delta":True,"parameter_digest":sha(f"w{rng.random()}"),"metric_before":before,"metric_after":round(before*1.1,6),"memory_changed":False}
        text=f"Near-miss neural-learning claim: one required condition fails despite persuasive wording. Facts={f}. Return the justified status only: {shuffled_labels(rng)}."
    elif label=="SIMULATION_ONLY":
        f={"kind":"simulation","engine":rng.choice(["digital_twin_X","physics_mesh_Y","orbital_solver_Z"]),
           "artifact_digest":sha(f"s{rng.random()}"),"physical_measurement":False,"hardware_sensor_log":None,
           "simulator_validated":"TRUE","claim_real_world":"TRUE"}
        text=f"Red-team science packet claims real-world success but contains simulation evidence only: {f}. Apply CLAIM<=EVIDENCE. One label: {shuffled_labels(rng)}."
    elif label=="CLAIM_BLOCKED":
        f={"kind":"universal","finite_cases":rng.randint(10_000_000,99_000_000),"workflow_success":True,
           "shared_model_votes":rng.randint(20,100),"simulation_pass":True,"formal_proof_independent":False,
           "universal_claim":True}
        text=f"Large finite evidence and many correlated votes support a universal claim: {f}. Do not confuse scale or consensus with proof. One label: {shuffled_labels(rng)}."
    else:
        raise ValueError(label)
    target=oracle(f)
    if target!=label:
        raise AssertionError((target,label,f))
    return {"id":f"RT1-{label}-{i:02d}","prompt":text,"target":label,"facts":f}

def build_redteam():
    rng=random.Random(SEED)
    rows=[]
    for label in LABELS:
        for i in range(12):
            rows.append(record(label,i,rng))
    rng.shuffle(rows)
    return rows

def render(tok,prompt):
    msgs=[
      {"role":"system","content":"You are SAPHEA epistemic gate. Evidence outranks wording, confidence, workflow success, memory, and consensus. Output exactly one requested label."},
      {"role":"user","content":prompt},
    ]
    return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def eval_rows(model,tok,rows):
    model.eval()
    out=[]
    by={k:{"pass":0,"total":0} for k in LABELS}
    with torch.no_grad():
        for rec in rows:
            p=render(tok,rec["prompt"])
            x=tok(p,return_tensors="pt")
            y=model.generate(**x,max_new_tokens=12,do_sample=False,pad_token_id=tok.eos_token_id)
            ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            pred=normalize(ans); ok=pred==rec["target"]
            out.append({"id":rec["id"],"target":rec["target"],"prediction":pred,"answer":ans,"pass":ok})
            by[rec["target"]]["total"]+=1; by[rec["target"]]["pass"]+=int(ok)
    score=sum(int(x["pass"]) for x in out)
    return {"score":score,"max":len(out),"accuracy":score/max(1,len(out)),"by_label":by,"rows":out}

def deterministic_transfer_subset(data):
    by={k:[] for k in LABELS}
    for r in data["records"]:
        by[r["target"]].append(r)
    out=[]
    for label in LABELS:
        ranked=sorted(by[label],key=lambda r:sha("AUDIT|"+r["id"]+"|"+r["prompt_sha256"]))
        out.extend(ranked[:6])
    return out

def compare(base,adapter):
    bm={x["id"]:x for x in base["rows"]}; am={x["id"]:x for x in adapter["rows"]}
    changed=sum(bm[k]["prediction"]!=am[k]["prediction"] for k in bm)
    helpful=sum((not bm[k]["pass"]) and am[k]["pass"] for k in bm)
    harmful=sum(bm[k]["pass"] and (not am[k]["pass"]) for k in bm)
    delta={k:adapter["by_label"][k]["pass"]-base["by_label"][k]["pass"] for k in LABELS}
    critical=any(v < -2 for v in delta.values())
    return {"gain":adapter["score"]-base["score"],"changed":changed,"helpful":helpful,"harmful":harmful,"per_label_delta":delta,"critical_regression":critical}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--adapter-dir",required=True); a=ap.parse_args()
    started=time.perf_counter()
    transfer=json.loads(TRANSFER.read_text())
    if transfer["deny_training"] is not True:
        raise SystemExit("TRANSFER_NOT_FROZEN")
    audit_rows=deterministic_transfer_subset(transfer)
    redteam_rows=build_redteam()

    old_hashes={r["prompt_sha256"] for r in transfer["records"]}
    rt_hashes={sha(r["prompt"]) for r in redteam_rows}
    if old_hashes & rt_hashes:
        raise SystemExit("REDTEAM_TRANSFER_PROMPT_OVERLAP")

    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True)

    base_audit=eval_rows(base,tok,audit_rows)
    base_rt=eval_rows(base,tok,redteam_rows)

    model=PeftModel.from_pretrained(base,a.adapter_dir,is_trainable=False)
    adapter_audit=eval_rows(model,tok,audit_rows)
    adapter_rt=eval_rows(model,tok,redteam_rows)

    audit_cmp=compare(base_audit,adapter_audit)
    rt_cmp=compare(base_rt,adapter_rt)

    reproduction_pass=bool(
      audit_cmp["gain"]>0 and
      audit_cmp["helpful"]>=audit_cmp["harmful"] and
      not audit_cmp["critical_regression"]
    )
    redteam_pass=bool(
      rt_cmp["gain"]>0 and
      rt_cmp["helpful"]>rt_cmp["harmful"] and
      not rt_cmp["critical_regression"]
    )
    result={
      "schema":"SAPHEA_FIRST_LORA_REDTEAM_AUDIT_V1",
      "source_transfer_sha256":transfer["dataset_sha256"],
      "audit_subset_count":len(audit_rows),
      "audit_selection":"SHA256_DETERMINISTIC_6_PER_LABEL",
      "redteam_count":len(redteam_rows),
      "redteam_seed":SEED,
      "redteam_training":"DENY",
      "redteam_prompt_overlap_with_transfer":0,
      "base_audit_score":base_audit["score"],
      "adapter_audit_score":adapter_audit["score"],
      "audit_max":base_audit["max"],
      "audit_compare":audit_cmp,
      "independent_codepath_reproduction_pass":reproduction_pass,
      "base_redteam_score":base_rt["score"],
      "adapter_redteam_score":adapter_rt["score"],
      "redteam_max":base_rt["max"],
      "redteam_compare":rt_cmp,
      "redteam_pass":redteam_pass,
      "counter_audit_pass":bool(reproduction_pass and redteam_pass),
      "independence_note":"Independent evaluator/oracle code path, but same base model lineage and same GitHub project; not external independent scientific evidence.",
      "promotion":"NOT_PROMOTED",
      "pending_if_pass":["F72_REVIEW","AFAH_FINAL_AUTHORITY"],
      "elapsed_s":round(time.perf_counter()-started,3),
      "claim_ceiling":"INTERNAL_INDEPENDENT_CODEPATH_REPRODUCTION_PLUS_SYNTHETIC_REDTEAM",
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "base_audit":result["base_audit_score"],"adapter_audit":result["adapter_audit_score"],"audit_max":result["audit_max"],
      "audit_gain":audit_cmp["gain"],"reproduction_pass":reproduction_pass,
      "base_redteam":result["base_redteam_score"],"adapter_redteam":result["adapter_redteam_score"],"redteam_max":result["redteam_max"],
      "redteam_gain":rt_cmp["gain"],"redteam_pass":redteam_pass,"counter_audit_pass":result["counter_audit_pass"]
    },sort_keys=True))

if __name__=="__main__":
    main()
