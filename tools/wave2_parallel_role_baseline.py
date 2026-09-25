#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT=pathlib.Path(__file__).resolve().parents[1]
CFG=ROOT/"config/wave2-parallel-role-baseline-v1.json"

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def parse_label(text,labels):
    s=text.strip().upper()
    exact=re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)
    if exact in labels:return exact
    for lab in sorted(labels,key=len,reverse=True):
        if re.search(rf"(?<![A-Z_]){re.escape(lab)}(?![A-Z_])",s):
            return lab
    return None

def prompt(role,spec,scenario):
    labels=", ".join(spec["labels"])
    system=(
      f"You are the scoped {role} baseline evaluator inside CEREBRON. "
      f"Specialization: {spec['specialization']}. "
      "This is a frozen cold baseline, not training. "
      "Choose exactly one label justified by the scenario. "
      "Do not invent evidence and do not explain."
    )
    user=f"Scenario: {scenario}\nAllowed labels: [{labels}]\nReturn exactly one label."
    return system,user

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--role",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    cfg=json.loads(CFG.read_text())
    role=a.role.upper()
    if role not in cfg["roles"]: raise SystemExit(f"UNKNOWN_ROLE:{role}")
    spec=cfg["roles"][role]
    mid=spec["model"]["id"]; rev=spec["model"]["revision"]
    tasks=[{"id":x[0],"target":x[1],"scenario":x[2]} for x in spec["tasks"]]
    bench={"schema":cfg["schema"],"role":role,"labels":spec["labels"],"tasks":tasks,"deny_training":True}
    bench_sha=h(bench)

    tok=AutoTokenizer.from_pretrained(mid,revision=rev)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    mdl=AutoModelForCausalLM.from_pretrained(mid,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    mdl.eval()

    rows=[];started=time.perf_counter()
    with torch.no_grad():
        for task in tasks:
            system,user=prompt(role,spec,task["scenario"])
            msgs=[{"role":"system","content":system},{"role":"user","content":user}]
            try:
                if getattr(tok,"chat_template",None):
                    rendered=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True,enable_thinking=False)
                else:
                    rendered=system+"\nUSER: "+user+"\nASSISTANT:\n"
            except TypeError:
                rendered=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
            x=tok(rendered,return_tensors="pt")
            y=mdl.generate(**x,max_new_tokens=12,do_sample=False,repetition_penalty=1.05,pad_token_id=tok.eos_token_id)
            ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            pred=parse_label(ans,spec["labels"])
            rows.append({"id":task["id"],"target":task["target"],"prediction":pred,"raw_output":ans[:240],"pass":pred==task["target"]})

    score=sum(int(r["pass"]) for r in rows)
    receipt={
      "schema":"CEREBRON_WAVE2_ROLE_BASELINE_RECEIPT_V1",
      "run_id":int(a.run_id),
      "role":role,
      "specialization":spec["specialization"],
      "training_readiness":spec["training_readiness"],
      "real_inference":True,
      "training_executed":False,
      "benchmark_deny_training":True,
      "benchmark_sha256":bench_sha,
      "model_id":mid,
      "revision":rev,
      "lineage_fingerprint":hashlib.sha256(f"{mid}|{rev}".encode()).hexdigest(),
      "independent_evidence":False,
      "task_count":len(tasks),
      "score":score,
      "accuracy":score/max(1,len(tasks)),
      "results":rows,
      "elapsed_s":round(time.perf_counter()-started,3),
      "claim_ceiling":"SCOPED_COLD_ROLE_BASELINE_ONLY_NOT_TRAINING_OR_GENERAL_CAPABILITY"
    }
    receipt["receipt_sha256"]=h(receipt)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "role":role,"score":score,"max":len(tasks),"accuracy":receipt["accuracy"],
      "model_id":mid,"revision":rev,"training_readiness":receipt["training_readiness"],
      "benchmark_sha256":bench_sha
    },sort_keys=True))

if __name__=="__main__":
    main()
