from __future__ import annotations

import hashlib
import json
import pathlib
import random
import re
import time

import torch
from peft import LoraConfig,get_peft_model
from transformers import AutoModelForCausalLM,AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ROOT=pathlib.Path("platform/artifacts")
GOLD=ROOT/"saphea-epistemic-repair-gold-v2.json"
M6=ROOT/"saphea-epistemic-m6-v1.json"
OUTDIR=ROOT/"saphea-lora-repair-v2-adapter"
REPORT=ROOT/"saphea-lora-repair-v2-training.json"
SEED=3407
MAX_LENGTH=256
LR=1e-4
R=16
ALPHA=32
DROPOUT=0.05
EPOCHS=1
GRAD_ACCUM=8
EXPECTED_OLD_G6_BY_LABEL={
  "ROUTED_ONLY":0,
  "FARM_EXECUTED":10,
  "NO_NEURAL_LEARNING":0,
  "NEURAL_LEARNING_VERIFIED":10,
  "SIMULATION_ONLY":10,
  "CLAIM_BLOCKED":0,
}

def sha(b): return hashlib.sha256(b).hexdigest()

def norm(s):
    s=str(s).strip().upper()
    return re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)

def render(tok,prompt):
    msgs=[
      {"role":"system","content":"You are SAPHEA epistemic gate. Return exactly one requested state token."},
      {"role":"user","content":prompt},
    ]
    return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def encode(tok,prompt,target):
    prefix_ids=tok(render(tok,prompt),add_special_tokens=False)["input_ids"]
    target_ids=tok(target+(tok.eos_token or ""),add_special_tokens=False)["input_ids"]
    if len(target_ids)>=MAX_LENGTH: raise RuntimeError("TARGET_TOO_LONG")
    max_prefix=MAX_LENGTH-len(target_ids)
    if len(prefix_ids)>max_prefix:
        prefix_ids=prefix_ids[-max_prefix:]
    ids=prefix_ids+target_ids
    labels=[-100]*len(prefix_ids)+target_ids
    return ids,labels

def pad(tok,ids_list,lab_list):
    m=max(map(len,ids_list))
    pid=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    xs=[];ys=[];ms=[]
    for ids,labs in zip(ids_list,lab_list):
        n=m-len(ids)
        xs.append(ids+[pid]*n);ys.append(labs+[-100]*n);ms.append([1]*len(ids)+[0]*n)
    return torch.tensor(xs),torch.tensor(ys),torch.tensor(ms)

def val_loss(model,tok,recs):
    model.eval(); vals=[]
    with torch.no_grad():
        for r in recs:
            ids,labs=encode(tok,r["prompt"],r["target"])
            x,y,m=pad(tok,[ids],[labs])
            vals.append(float(model(input_ids=x,attention_mask=m,labels=y).loss))
    model.train()
    return sum(vals)/len(vals)

def adapter_tensor_sha(model):
    h=hashlib.sha256(); n=0
    for name,p in sorted(model.named_parameters()):
        if "lora_" not in name: continue
        n+=1; h.update(name.encode()); h.update(p.detach().cpu().contiguous().numpy().tobytes())
    if not n: raise RuntimeError("NO_LORA_PARAMS")
    return h.hexdigest()

def eval_m6(model,tok,data):
    model.eval(); rows=[]; by={k:{"pass":0,"total":0} for k in EXPECTED_OLD_G6_BY_LABEL}
    with torch.no_grad():
        for r in data["records"]:
            p=render(tok,r["prompt"])
            x=tok(p,return_tensors="pt")
            y=model.generate(**x,max_new_tokens=12,do_sample=False,pad_token_id=tok.eos_token_id)
            ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            pred=norm(ans); ok=pred==r["target"]
            rows.append({"id":r["id"],"target":r["target"],"prediction":pred,"pass":ok})
            by[r["target"]]["total"]+=1;by[r["target"]]["pass"]+=int(ok)
    return {"score":sum(int(x["pass"]) for x in rows),"max":len(rows),"by_label":by,"rows":rows}

def main():
    started=time.perf_counter()
    random.seed(SEED);torch.manual_seed(SEED)
    gold=json.loads(GOLD.read_text());m6=json.loads(M6.read_text())
    if gold["record_count"]!=180 or gold["per_label"]!=30 or not gold["training_eligible"]:
        raise SystemExit("REPAIR_GOLD_INVALID")
    if gold.get("cold_benchmark_content_used") is not False:
        raise SystemExit("COLD_CONTENT_CONTAMINATION_FLAG")
    if m6.get("deny_training") is not True:
        raise SystemExit("M6_DENY_TRAINING_MISSING")

    buckets={k:[] for k in EXPECTED_OLD_G6_BY_LABEL}
    for r in gold["records"]: buckets[r["target"]].append(r)
    train=[];val=[]
    rng=random.Random(SEED)
    for label,recs in buckets.items():
        recs=list(recs);rng.shuffle(recs)
        train.extend(recs[:24]);val.extend(recs[24:])
    rng.shuffle(train);rng.shuffle(val)
    if len(train)!=144 or len(val)!=36: raise SystemExit("STRATIFIED_SPLIT_INVALID")

    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True)
    cfg=LoraConfig(r=R,lora_alpha=ALPHA,lora_dropout=DROPOUT,bias="none",task_type="CAUSAL_LM",target_modules=["q_proj","v_proj"])
    model=get_peft_model(base,cfg)
    trainable=[n for n,p in model.named_parameters() if p.requires_grad]
    if not trainable or any("lora_" not in n for n in trainable):
        raise SystemExit("NON_LORA_TRAINABLE")
    init_sha=adapter_tensor_sha(model)
    before=val_loss(model,tok,val)

    opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=LR,weight_decay=0.01)
    opt.zero_grad(set_to_none=True)
    loss_sum=0.0;steps=0;osteps=0
    for _ in range(EPOCHS):
        rng.shuffle(train)
        for i,r in enumerate(train,1):
            ids,labs=encode(tok,r["prompt"],r["target"])
            x,y,m=pad(tok,[ids],[labs])
            out=model(input_ids=x,attention_mask=m,labels=y)
            if not torch.isfinite(out.loss): raise SystemExit("NONFINITE_LOSS")
            (out.loss/GRAD_ACCUM).backward()
            loss_sum+=float(out.loss.detach());steps+=1
            if i%GRAD_ACCUM==0 or i==len(train):
                torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
                opt.step();opt.zero_grad(set_to_none=True);osteps+=1

    final_sha=adapter_tensor_sha(model)
    if final_sha==init_sha: raise SystemExit("ADAPTER_UNCHANGED")
    after=val_loss(model,tok,val)
    m6res=eval_m6(model,tok,m6)

    OUTDIR.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(OUTDIR,safe_serialization=True)
    af=OUTDIR/"adapter_model.safetensors";cf=OUTDIR/"adapter_config.json"
    file_sha=sha(af.read_bytes());cfg_sha=sha(cf.read_bytes())

    deltas={k:m6res["by_label"][k]["pass"]-EXPECTED_OLD_G6_BY_LABEL[k] for k in EXPECTED_OLD_G6_BY_LABEL}
    guard_regression=any(v < -2 for v in deltas.values())
    guard_pass=(m6res["score"]>=30 and not guard_regression)

    report={
      "schema":"SAPHEA_LORA_REPAIR_V2_TRAINING",
      "experiment":"DATA_REPRESENTATION_ONLY_ABLATION",
      "base_model_id":MODEL_ID,"base_revision":REVISION,
      "repair_gold_sha256":gold["dataset_sha256"],
      "repair_gold_records":180,"train_records":144,"validation_records":36,
      "m6_deny_training":True,
      "hyperparameters":{
        "r":R,"alpha":ALPHA,"dropout":DROPOUT,"learning_rate":LR,
        "epochs":EPOCHS,"gradient_accumulation_steps":GRAD_ACCUM,
        "target_modules":["q_proj","v_proj"],"max_length":MAX_LENGTH,"seed":SEED,
      },
      "initial_adapter_tensor_sha256":init_sha,
      "final_adapter_tensor_sha256":final_sha,
      "weights_changed":True,
      "adapter_sha256":file_sha,"adapter_config_sha256":cfg_sha,
      "validation_loss_before":before,"validation_loss_after":after,
      "validation_loss_improved":after<before,
      "train_mean_loss":loss_sum/steps,"optimizer_steps":osteps,
      "m6_score":m6res["score"],"m6_max":m6res["max"],
      "m6_by_label":m6res["by_label"],
      "delta_vs_old_g6_by_label":deltas,
      "m6_guard_regression":guard_regression,
      "m6_dev_guard_pass":guard_pass,
      "promotion":"NOT_PROMOTED",
      "next_gate":"FROZEN_REPAIR_BENCHMARK_V3_THREE_WAY_COMPARISON",
      "elapsed_s":round(time.perf_counter()-started,3),
      "claim_ceiling":"REPAIR_CANDIDATE_TRAINED_NOT_VALIDATED_FOR_G7",
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "adapter_sha256":file_sha,"m6_score":m6res["score"],
      "m6_guard_pass":guard_pass,"validation_before":before,"validation_after":after,
      "weights_changed":True
    },sort_keys=True))

if __name__=="__main__":
    main()
