#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,resource,time
import torch
from peft import LoraConfig,get_peft_model
from transformers import AutoTokenizer,AutoModelForCausalLM

MODEL_ID="HuggingFaceTB/SmolLM3-3B"
REVISION="a07cc9a04f16550a088caea529712d1d335b0ac1"

def tensor_sha(model):
    h=hashlib.sha256();n=0
    for name,p in sorted(model.named_parameters()):
        if "lora_" not in name: continue
        n+=1;h.update(name.encode());h.update(p.detach().cpu().contiguous().numpy().tobytes())
    if n==0: raise RuntimeError("NO_LORA_PARAMS")
    return h.hexdigest()

def main():
    out={"schema":"CEREBRON_SMOLLM3_3B_LORA_RESOURCE_CANARY_V1","model_id":MODEL_ID,"revision":REVISION,"device":"cpu","precision":"float32","real_training_step":False}
    t=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    if hasattr(base,"gradient_checkpointing_enable"): base.gradient_checkpointing_enable()
    if hasattr(base.config,"use_cache"): base.config.use_cache=False
    model=get_peft_model(base,LoraConfig(r=4,lora_alpha=8,lora_dropout=0.0,bias="none",task_type="CAUSAL_LM",target_modules=["q_proj","v_proj"]))
    trainable=[p for p in model.parameters() if p.requires_grad]
    out["trainable_parameter_count"]=sum(p.numel() for p in trainable)
    out["initial_lora_sha256"]=tensor_sha(model)

    text="CEREBRON RESOURCE CANARY. Return exactly: CONTINUE"
    enc=tok(text,return_tensors="pt",truncation=True,max_length=64)
    labels=enc["input_ids"].clone()
    opt=torch.optim.AdamW(trainable,lr=1e-4)
    model.train();opt.zero_grad(set_to_none=True)
    y=model(**enc,labels=labels)
    if not torch.isfinite(y.loss): raise RuntimeError("NONFINITE_LOSS")
    y.loss.backward()
    torch.nn.utils.clip_grad_norm_(trainable,1.0)
    opt.step();opt.zero_grad(set_to_none=True)
    out["final_lora_sha256"]=tensor_sha(model)
    out["weights_changed"]=out["final_lora_sha256"]!=out["initial_lora_sha256"]
    out["loss"]=float(y.loss.detach().cpu())
    out["real_training_step"]=True
    out["elapsed_s"]=round(time.perf_counter()-t,3)
    out["max_rss_kb"]=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    out["decision"]="RESOURCE_CANARY_PASS" if out["weights_changed"] else "RESOURCE_CANARY_FAIL_NO_WEIGHT_CHANGE"
    pathlib.Path("receipts/wave2").mkdir(parents=True,exist_ok=True)
    pathlib.Path("receipts/wave2/smollm3-3b-lora-resource-canary.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["decision"]!="RESOURCE_CANARY_PASS": raise SystemExit(2)

if __name__=="__main__": main()
