#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import random
import time

import torch
from peft import LoraConfig,get_peft_model
from transformers import AutoModelForCausalLM,AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ROLE_LABELS={
  "AELYS":["ANSWER","CLARIFY","SUMMARIZE","LIMIT"],
  "ETHERION":["DEFINE","SOURCE","MODEL","CALCULATE","RED_TEAM","DESIGN_TEST"],
  "AFAH":["ACCEPT","HOLD","REJECT","CORRELATED"],
  "METRION":["PASS","FAIL_UNITS","FAIL_TOLERANCE","SIMULATION_ONLY"],
}
ROLE_SCOPE={
  "AELYS":"dialogue coordination human interaction action classification",
  "ETHERION":"R&D next-action and falsification classification",
  "AFAH":"evidence accept hold reject correlation classification",
  "METRION":"engineering metrology units tolerance simulation-boundary classification",
}
MAX_LENGTH=256
LR=5e-5
EPOCHS=1
GRAD_ACCUM=4
LORA_R=8
LORA_ALPHA=16
LORA_DROPOUT=0.05

def sha_obj(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def file_sha(p:pathlib.Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def adapter_tensor_sha(model):
    h=hashlib.sha256();n=0
    for name,p in sorted(model.named_parameters()):
        if "lora_" not in name:
            continue
        n+=1
        h.update(name.encode())
        h.update(str(tuple(p.shape)).encode())
        h.update(p.detach().cpu().contiguous().numpy().tobytes())
    if n==0: raise RuntimeError("NO_LORA_PARAMETERS")
    return h.hexdigest()

def system_prompt(role,labels):
    return (
      f"You are {role}, a scoped CEREBRON specialist for {ROLE_SCOPE[role]}. "
      f"Return exactly one allowed label from [{', '.join(labels)}]. "
      "Do not add explanation. Do not invent evidence."
    )

def render(tok,role,prompt):
    msgs=[{"role":"system","content":system_prompt(role,ROLE_LABELS[role])},{"role":"user","content":prompt}]
    return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def encode_supervised(tok,role,prompt,target):
    prefix=render(tok,role,prompt)
    prefix_ids=tok(prefix,add_special_tokens=False)["input_ids"]
    target_ids=tok(target+(tok.eos_token or ""),add_special_tokens=False)["input_ids"]
    if len(target_ids)>=MAX_LENGTH: raise RuntimeError("TARGET_TOO_LONG")
    max_prefix=MAX_LENGTH-len(target_ids)
    if len(prefix_ids)>max_prefix:
        head=min(80,max_prefix//3)
        tail=max_prefix-head
        prefix_ids=prefix_ids[:head]+prefix_ids[-tail:]
    ids=prefix_ids+target_ids
    labels=[-100]*len(prefix_ids)+target_ids
    return ids,labels

def pad(tok,ids_list,label_list):
    m=max(len(x) for x in ids_list)
    pid=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    xs=[];ys=[];ms=[]
    for ids,labs in zip(ids_list,label_list):
        n=m-len(ids)
        xs.append(ids+[pid]*n)
        ys.append(labs+[-100]*n)
        ms.append([1]*len(ids)+[0]*n)
    return torch.tensor(xs),torch.tensor(ys),torch.tensor(ms)

def parse_label(text,labels):
    s=str(text).strip().upper()
    if s in labels:return s
    for lab in labels:
        if lab in s.split():return lab
    return None

def evaluate(model,tok,role,records):
    labels=ROLE_LABELS[role]
    model.eval()
    rows=[];by={k:{"pass":0,"total":0} for k in labels}
    with torch.no_grad():
        for rec in records:
            p=render(tok,role,rec["prompt"])
            x=tok(p,return_tensors="pt")
            y=model.generate(**x,max_new_tokens=10,do_sample=False,repetition_penalty=1.05,pad_token_id=tok.eos_token_id)
            ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            pred=parse_label(ans,labels)
            ok=pred==rec["target"]
            rows.append({"id":rec["id"],"target":rec["target"],"prediction":pred,"raw":ans[:120],"pass":ok})
            by[rec["target"]]["total"]+=1;by[rec["target"]]["pass"]+=int(ok)
    score=sum(int(r["pass"]) for r in rows)
    return {"score":score,"max":len(rows),"accuracy":score/max(1,len(rows)),"by_label":by,"rows":rows}

def supervised_loss(model,tok,role,records):
    model.eval();vals=[]
    with torch.no_grad():
        for rec in records:
            ids,labs=encode_supervised(tok,role,rec["prompt"],rec["target"])
            x,y,m=pad(tok,[ids],[labs])
            o=model(input_ids=x,attention_mask=m,labels=y)
            vals.append(float(o.loss.detach().cpu()))
    model.train()
    return sum(vals)/max(1,len(vals))

def critical_regression(before,after):
    details={}
    critical=False
    for label in before["by_label"]:
        b=before["by_label"][label]["pass"];a=after["by_label"][label]["pass"]
        total=before["by_label"][label]["total"]
        delta=a-b
        threshold=max(1,math.ceil(total*0.25))
        iscrit=delta<=-threshold
        details[label]={"before":b,"after":a,"total":total,"delta":delta,"critical_threshold":-threshold,"critical":iscrit}
        critical=critical or iscrit
    return critical,details

def load_records(path):
    d=json.loads(pathlib.Path(path).read_text())
    return d,d["records"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--role",required=True)
    ap.add_argument("--split",required=True)
    ap.add_argument("--m6",required=True)
    ap.add_argument("--transfer",required=True)
    ap.add_argument("--red",required=True)
    ap.add_argument("--release",required=True)
    ap.add_argument("--output-root",required=True)
    a=ap.parse_args()
    role=a.role.upper()
    if role not in ROLE_LABELS: raise SystemExit("UNKNOWN_ROLE")
    seed=26092510+sum(ord(c) for c in role)
    random.seed(seed);torch.manual_seed(seed)
    started=time.perf_counter()

    release=json.loads(pathlib.Path(a.release).read_text())
    if release.get("state")!="RELEASED_FOR_SCOPED_LORA_TRAINING" or release.get("training_released") is not True:
        raise SystemExit("TRAINING_RELEASE_MISSING")
    rr=release["roles"][role]

    split=json.loads(pathlib.Path(a.split).read_text())
    train=[{"id":r["record_id"],"prompt":r["prompt"],"target":r["target"]} for r in split["train_records"]]
    validation=[{"id":r["record_id"],"prompt":r["prompt"],"target":r["target"]} for r in split["validation_records"]]
    if split["split_sha256"]!=rr["split_sha256"]: raise SystemExit("SPLIT_SHA_MISMATCH")
    if sorted(x["id"] for x in train)!=sorted(rr["train_record_ids"]): raise SystemExit("TRAIN_ID_RELEASE_MISMATCH")
    if sorted(x["id"] for x in validation)!=sorted(rr["validation_record_ids"]): raise SystemExit("VALIDATION_ID_RELEASE_MISMATCH")

    cold={}
    for name,path in [("M6",a.m6),("TRANSFER",a.transfer),("RED",a.red)]:
        d,records=load_records(path)
        if d.get("deny_training") is not True or d.get("training_eligible") is not False:
            raise SystemExit(f"{name}_TRAINING_DENY_MISSING")
        expected=rr["cold"][name]["dataset_sha256"]
        if d.get("dataset_sha256")!=expected: raise SystemExit(f"{name}_SHA_MISMATCH")
        cold[name]=(d,records)

    train_ids={x["id"] for x in train};val_ids={x["id"] for x in validation}
    cold_ids={x["id"] for _,records in cold.values() for x in records}
    if train_ids&val_ids or train_ids&cold_ids or val_ids&cold_ids:
        raise SystemExit("DATASET_ID_LEAKAGE")

    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None:tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True)
    cfg=LoraConfig(r=LORA_R,lora_alpha=LORA_ALPHA,lora_dropout=LORA_DROPO,bias="none",task_type="CAUSAL_LM",target_modules=["q_proj","v_proj"])
    model=get_peft_model(base,cfg)
    trainable=[n for n,p in model.named_parameters() if p.requires_grad]
    if not trainable or any("lora_" not in n for n in trainable):
        raise SystemExit("NON_LORA_TRAINABLE_PARAMETER")

    before={
      "VALIDATION":evaluate(model,tok,role,validation),
      "M6":evaluate(model,tok,role,cold["M6"][1]),
      "TRANSFER":evaluate(model,tok,role,cold["TRANSFER"][1]),
      "RED":evaluate(model,tok,role,cold["RED"][1]),
    }
    val_loss_before=supervised_loss(model,tok,role,validation)
    initial_sha=adapter_tensor_sha(model)

    rng=random.Random(seed)
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=LR,weight_decay=0.01)
    model.train();optimizer.zero_grad(set_to_none=True)
    loss_sum=0.0;steps=0;opt_steps=0
    for _ in range(EPOCHS):
        order=list(train);rng.shuffle(order)
        for idx,rec in enumerate(order,1):
            ids,labs=encode_supervised(tok,role,rec["prompt"],rec["target"])
            x,y,m=pad(tok,[ids],[labs])
            out=model(input_ids=x,attention_mask=m,labels=y)
            if not torch.isfinite(out.loss):raise SystemExit("NONFINITE_LOSS")
            (out.loss/GRAD_ACCUM).backward()
            loss_sum+=float(out.loss.detach().cpu());steps+=1
            if idx%GRAD_ACCUM==0 or idx==len(order):
                torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
                optimizer.step();optimizer.zero_grad(set_to_none=True);opt_steps+=1

    final_sha=adapter_tensor_sha(model)
    weights_changed=final_sha!=initial_sha
    after={
      "VALIDATION":evaluate(model,tok,role,validation),
      "M6":evaluate(model,tok,role,cold["M6"][1]),
      "TRANSFER":evaluate(model,tok,role,cold["TRANSFER"][1]),
      "RED":evaluate(model,tok,role,cold["RED"][1]),
    }
    val_loss_after=supervised_loss(model,tok,role,validation)

    regressions={};any_critical=False
    gains={}
    for suite in ["VALIDATION","M6","TRANSFER","RED"]:
        crit,detail=critical_regression(before[suite],after[suite])
        regressions[suite]={"critical":crit,"by_label":detail}
        any_critical=any_critical or crit
        gains[suite]=after[suite]["score"]-before[suite]["score"]

    validation_gate=(gains["VALIDATION"]>=0 and val_loss_after<val_loss_before and not regressions["VALIDATION"]["critical"])
    cold_gate=(gains["M6"]>0 and gains["TRANSFER"]>0 and gains["RED"]>=0 and not any_critical)
    decision="G6_CANDIDATE_HOLD_F72_AFAH" if (weights_changed and validation_gate and cold_gate) else "ROLLBACK_RETAIN_EVIDENCE"

    outroot=pathlib.Path(a.output_root);outroot.mkdir(parents=True,exist_ok=True)
    adapter_dir=outroot/"adapter";adapter_dir.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(adapter_dir,safe_serialization=True)
    adapter_file=adapter_dir/"adapter_model.safetensors"
    adapter_cfg=adapter_dir/"adapter_config.json"
    report={
      "schema":"CEREBRON_WAVE1_ROLE_LORA_TRAINING_V1",
      "role":role,
      "scope":ROLE_SCOPE[role],
      "base_model_id":MODEL_ID,
      "base_revision":REVISION,
      "seed":seed,
      "training_source_manifest_sha256":release["source_manifest_sha256"],
      "release_sha256":release["release_sha256"],
      "split_sha256":split["split_sha256"],
      "train_count":len(train),
      "validation_count":len(validation),
      "cold_dataset_sha256":{k:v[0]["dataset_sha256"] for k,v in cold.items()},
      "cold_deny_training":True,
      "train_ids_match_release":True,
      "only_lora_trainable":True,
      "weights_changed":weights_changed,
      "initial_adapter_tensor_sha256":initial_sha,
      "final_adapter_tensor_sha256":final_sha,
      "adapter_file_sha256":file_sha(adapter_file),
      "adapter_config_sha256":file_sha(adapter_cfg),
      "hyperparameters":{"lr":LR,"epochs":EPOCHS,"grad_accum":GRAD_ACCUM,"r":LORA_R,"alpha":LORA_ALPHA,"dropout":LORA_DROPOUT,"max_length":MAX_LENGTH},
      "before":before,
      "after":after,
      "gains":gains,
      "regressions":regressions,
      "any_critical_regression":any_critical,
      "validation_loss_before":val_loss_before,
      "validation_loss_after":val_loss_after,
      "validation_gate_pass":validation_gate,
      "cold_gate_pass":cold_gate,
      "train_mean_loss":loss_sum/max(1,steps),
      "optimizer_steps":opt_steps,
      "decision":decision,
      "promotion":"NOT_PROMOTED",
      "pending":["HF_PRIVATE_WRITE_READBACK_SHA","F72_REVIEW","AFAH_FINAL_AUTHORITY"] if decision.startswith("G6") else ["REPAIR_OR_NEW_DATA"],
      "claim_ceiling":"REAL_SCOPED_LORA_WEIGHT_CHANGE_AND_COLD_EVALUATION_ONLY_NO_GENERAL_CAPABILITY",
      "elapsed_s":round(time.perf_counter()-started,3)
    }
    report["report_sha256"]=sha_obj(report)
    (outroot/"training-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "role":role,
      "weights_changed":weights_changed,
      "adapter_sha256":report["adapter_file_sha256"],
      "gains":gains,
      "validation_gate_pass":validation_gate,
      "cold_gate_pass":cold_gate,
      "critical_regression":any_critical,
      "decision":decision,
      "report_sha256":report["report_sha256"]
    },sort_keys=True))

if __name__=="__main__":
    main()
