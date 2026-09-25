#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,json,math,pathlib,random,time
import torch
from peft import LoraConfig,get_peft_model
from transformers import AutoModelForCausalLM,AutoTokenizer

ROLE_SCOPE={
 "SPIRALION":"cumulative reasoning checkpoint continuity and contradiction management",
 "HYPERION":"divergent hypotheses alternative mechanisms and counterfactual search",
 "ASTRION":"aerospace R&D systems physics trajectory propulsion and validation",
 "SAPHEA_MICRO":"routing compact specialist selection and minimal useful coalition"
}
MAX_LENGTH=128
LR=5e-5
EPOCHS=1
GRAD_ACCUM=8
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
        if "lora_" not in name: continue
        n+=1
        h.update(name.encode());h.update(str(tuple(p.shape)).encode())
        h.update(p.detach().cpu().contiguous().numpy().tobytes())
    if n==0: raise RuntimeError("NO_LORA_PARAMETERS")
    return h.hexdigest()

def choose_codes(tok,n):
    pool=list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out=[]
    for c in pool:
        ids=tok(c,add_special_tokens=False)["input_ids"]
        if len(ids)==1 and ids[0] not in [x[1] for x in out]:
            out.append((c,ids[0]))
        if len(out)>=n: break
    if len(out)<n: raise RuntimeError("NOT_ENOUGH_SINGLE_TOKEN_CODES")
    return out

def render(tok,role,labels,codes,prompt):
    mapping="; ".join(f"{code}={label}" for label,(code,_) in zip(labels,codes))
    system=(
      f"You are {role}, scoped for {ROLE_SCOPE[role]}. "
      f"Classify the user record. Mapping: {mapping}. "
      "Return exactly one code and nothing else. Do not invent evidence."
    )
    msgs=[{"role":"system","content":system},{"role":"user","content":prompt}]
    try:
        return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def encode_supervised(tok,role,labels,codes,prompt,target):
    prefix=render(tok,role,labels,codes,prompt)
    prefix_ids=tok(prefix,add_special_tokens=False)["input_ids"]
    code_id=dict((lab,tid) for lab,(_,tid) in zip(labels,codes))[target]
    max_prefix=MAX_LENGTH-1
    if len(prefix_ids)>max_prefix:
        head=min(64,max_prefix//3);tail=max_prefix-head
        prefix_ids=prefix_ids[:head]+prefix_ids[-tail:]
    ids=prefix_ids+[code_id]
    labs=[-100]*len(prefix_ids)+[code_id]
    return ids,labs

def pad(tok,ids_list,label_list):
    m=max(len(x) for x in ids_list)
    pid=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    xs=[];ys=[];ms=[]
    for ids,labs in zip(ids_list,label_list):
        n=m-len(ids)
        xs.append(ids+[pid]*n);ys.append(labs+[-100]*n);ms.append([1]*len(ids)+[0]*n)
    return torch.tensor(xs),torch.tensor(ys),torch.tensor(ms)

def evaluate(model,tok,role,labels,codes,records):
    label_to_code={lab:(code,tid) for lab,(code,tid) in zip(labels,codes)}
    token_ids=[tid for _,tid in codes]
    rows=[];by={lab:{"pass":0,"total":0} for lab in labels}
    model.eval()
    with torch.no_grad():
        for rec in records:
            p=render(tok,role,labels,codes,rec["prompt"])
            x=tok(p,return_tensors="pt",truncation=True,max_length=MAX_LENGTH)
            logits=model(**x).logits[0,-1,token_ids]
            idx=int(torch.argmax(logits).item())
            pred=labels[idx]
            ok=pred==rec["target"]
            rows.append({"id":rec["id"],"target":rec["target"],"prediction":pred,"pass":ok})
            by[rec["target"]]["total"]+=1;by[rec["target"]]["pass"]+=int(ok)
    score=sum(int(r["pass"]) for r in rows)
    return {"score":score,"max":len(rows),"accuracy":score/max(1,len(rows)),"by_label":by,"rows":rows}

def supervised_loss(model,tok,role,labels,codes,records):
    vals=[];model.eval()
    with torch.no_grad():
        for rec in records:
            ids,labs=encode_supervised(tok,role,labels,codes,rec["prompt"],rec["target"])
            x,y,m=pad(tok,[ids],[labs])
            vals.append(float(model(input_ids=x,attention_mask=m,labels=y).loss.detach().cpu()))
    model.train()
    return sum(vals)/max(1,len(vals))

def critical_regression(before,after):
    details={};critical=False
    for label in before["by_label"]:
        b=before["by_label"][label]["pass"];a=after["by_label"][label]["pass"]
        total=before["by_label"][label]["total"]
        threshold=max(1,math.ceil(total*0.25))
        delta=a-b;crit=delta<=-threshold
        details[label]={"before":b,"after":a,"total":total,"delta":delta,"critical_threshold":-threshold,"critical":crit}
        critical=critical or crit
    return critical,details

def load_suite(path):
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
    if role not in ROLE_SCOPE: raise SystemExit("UNKNOWN_ROLE")

    release=json.loads(pathlib.Path(a.release).read_text())
    if release.get("state")!="RELEASED_FOR_SCOPED_LORA_TRAINING" or release.get("training_released") is not True:
        raise SystemExit("TRAINING_RELEASE_MISSING")
    rr=release["roles"][role]
    model_id=rr["model"]["id"];revision=rr["model"]["revision"]

    split=json.loads(pathlib.Path(a.split).read_text())
    labels=list(split["per_label"].keys())
    train=[{"id":r["record_id"],"prompt":r["prompt"],"target":r["target"]} for r in split["train_records"]]
    validation=[{"id":r["record_id"],"prompt":r["prompt"],"target":r["target"]} for r in split["validation_records"]]
    if split["split_sha256"]!=rr["split_sha256"]: raise SystemExit("SPLIT_SHA_MISMATCH")
    if sorted(x["id"] for x in train)!=sorted(rr["train_record_ids"]): raise SystemExit("TRAIN_ID_RELEASE_MISMATCH")

    cold={}
    for name,path in [("M6",a.m6),("TRANSFER",a.transfer),("RED",a.red)]:
        d,records=load_suite(path)
        if d.get("deny_training") is not True or d.get("training_eligible") is not False:
            raise SystemExit(f"{name}_TRAINING_DENY_MISSING")
        if d.get("dataset_sha256")!=rr["cold"][name]["dataset_sha256"]:
            raise SystemExit(f"{name}_SHA_MISMATCH")
        cold[name]=(d,records)

    seed=26092530+sum(ord(c) for c in role)
    random.seed(seed);torch.manual_seed(seed)
    started=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(model_id,revision=revision)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    codes=choose_codes(tok,len(labels))
    base=AutoModelForCausalLM.from_pretrained(model_id,revision=revision,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    if hasattr(base.config,"use_cache"): base.config.use_cache=False
    model=get_peft_model(base,LoraConfig(r=LORA_R,lora_alpha=LORA_ALPHA,lora_dropout=LORA_DROPOUT,bias="none",task_type="CAUSAL_LM",target_modules=["q_proj","v_proj"]))
    if hasattr(model,"enable_input_require_grads"): model.enable_input_require_grads()
    if hasattr(model,"gradient_checkpointing_enable"): model.gradient_checkpointing_enable()
    trainable=[p for p in model.parameters() if p.requires_grad]
    if not trainable or any("lora_" not in n for n,p in model.named_parameters() if p.requires_grad):
        raise SystemExit("NON_LORA_TRAINABLE_PARAMETER")

    before={
      "VALIDATION":evaluate(model,tok,role,labels,codes,validation),
      "M6":evaluate(model,tok,role,labels,codes,cold["M6"][1]),
      "TRANSFER":evaluate(model,tok,role,labels,codes,cold["TRANSFER"][1]),
      "RED":evaluate(model,tok,role,labels,codes,cold["RED"][1])
    }
    val_loss_before=supervised_loss(model,tok,role,labels,codes,validation)
    initial_sha=adapter_tensor_sha(model)

    opt=torch.optim.AdamW(trainable,lr=LR,weight_decay=0.01)
    rng=random.Random(seed);model.train();opt.zero_grad(set_to_none=True)
    loss_sum=0.0;steps=0;opt_steps=0
    order=list(train);rng.shuffle(order)
    for idx,rec in enumerate(order,1):
        ids,labs=encode_supervised(tok,role,labels,codes,rec["prompt"],rec["target"])
        x,y,m=pad(tok,[ids],[labs])
        out=model(input_ids=x,attention_mask=m,labels=y)
        if not torch.isfinite(out.loss): raise SystemExit("NONFINITE_LOSS")
        (out.loss/GRAD_ACCUM).backward()
        loss_sum+=float(out.loss.detach().cpu());steps+=1
        if idx%GRAD_ACCUM==0 or idx==len(order):
            torch.nn.utils.clip_grad_norm_(trainable,1.0)
            opt.step();opt.zero_grad(set_to_none=True);opt_steps+=1

    final_sha=adapter_tensor_sha(model)
    after={
      "VALIDATION":evaluate(model,tok,role,labels,codes,validation),
      "M6":evaluate(model,tok,role,labels,codes,cold["M6"][1]),
      "TRANSFER":evaluate(model,tok,role,labels,codes,cold["TRANSFER"][1]),
      "RED":evaluate(model,tok,role,labels,codes,cold["RED"][1])
    }
    val_loss_after=supervised_loss(model,tok,role,labels,codes,validation)
    gains={k:after[k]["score"]-before[k]["score"] for k in before}
    regressions={};anycrit=False
    for suite in before:
        crit,detail=critical_regression(before[suite],after[suite])
        regressions[suite]={"critical":crit,"by_label":detail};anycrit=anycrit or crit

    validation_gate=(gains["VALIDATION"]>=0 and val_loss_after<val_loss_before and not regressions["VALIDATION"]["critical"])
    cold_gate=(gains["M6"]>0 and gains["TRANSFER"]>0 and gains["RED"]>=0 and not anycrit)
    decision="G6_CANDIDATE_HOLD_F72_AFAH" if (final_sha!=initial_sha and validation_gate and cold_gate) else "ROLLBACK_RETAIN_EVIDENCE"

    root=pathlib.Path(a.output_root);root.mkdir(parents=True,exist_ok=True)
    ad=root/"adapter";ad.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(ad,safe_serialization=True)
    report={
      "schema":"CEREBRON_WAVE2_ROLE_LORA_TRAINING_V1",
      "role":role,"scope":ROLE_SCOPE[role],
      "base_model_id":model_id,"base_revision":revision,
      "label_codes":{lab:code for lab,(code,_) in zip(labels,codes)},
      "evaluation_mode":"NEXT_TOKEN_CODE_CLASSIFICATION",
      "seed":seed,"release_sha256":release["release_sha256"],
      "split_sha256":split["split_sha256"],
      "train_count":len(train),"validation_count":len(validation),
      "cold_dataset_sha256":{k:v[0]["dataset_sha256"] for k,v in cold.items()},
      "cold_deny_training":True,
      "weights_changed":final_sha!=initial_sha,
      "initial_adapter_tensor_sha256":initial_sha,"final_adapter_tensor_sha256":final_sha,
      "adapter_file_sha256":file_sha(ad/"adapter_model.safetensors"),
      "adapter_config_sha256":file_sha(ad/"adapter_config.json"),
      "before":before,"after":after,"gains":gains,"regressions":regressions,
      "any_critical_regression":anycrit,
      "validation_loss_before":val_loss_before,"validation_loss_after":val_loss_after,
      "validation_gate_pass":validation_gate,"cold_gate_pass":cold_gate,
      "train_mean_loss":loss_sum/max(1,steps),"optimizer_steps":opt_steps,
      "decision":decision,"promotion":"NOT_PROMOTED",
      "pending":["HF_PRIVATE_WRITE_READBACK_SHA","F72_REVIEW","AFAH_FINAL_AUTHORITY"] if decision.startswith("G6") else ["NEW_DATA_OR_METHOD"],
      "claim_ceiling":"REAL_SCOPED_LORA_NEXT_TOKEN_CLASSIFIER_WITH_FROZEN_COLD_TESTS_NO_GENERAL_CAPABILITY",
      "elapsed_s":round(time.perf_counter()-started,3)
    }
    report["report_sha256"]=sha_obj(report)
    (root/"training-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"role":role,"model_id":model_id,"weights_changed":report["weights_changed"],"gains":gains,"validation_gate_pass":validation_gate,"cold_gate_pass":cold_gate,"critical_regression":anycrit,"decision":decision,"adapter_sha256":report["adapter_file_sha256"],"report_sha256":report["report_sha256"]},sort_keys=True))

if __name__=="__main__": main()
