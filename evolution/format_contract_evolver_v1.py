#!/usr/bin/env python3
"""Evolve only the corrective-output contract, with validation/holdout separation.

No weights are changed. No F172/F173/F174 operational state is modified.
"""
import argparse, hashlib, json, re, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VAL_TARGETS=["SAPHEA","AELYS","ELYSION","PSI"]
HOLDOUT_TARGETS=["ETHERION","ELYRA","OMEGA","CEREBRON"]
KEYS=["ATTEMPT","ASSUMPTIONS","EVIDENCE_NEEDED","COUNTEREXAMPLE_OR_LIMIT","CONFIDENCE","UNKNOWN"]

CONTRACTS={
 "PLAIN6": (
   "Return exactly six plain lines, no Markdown, no bullets, no numbering, no blank lines.\n"
   "ATTEMPT: one concrete answer.\n"
   "ASSUMPTIONS: assumptions that must hold.\n"
   "EVIDENCE_NEEDED: what would verify the lesson.\n"
   "COUNTEREXAMPLE_OR_LIMIT: one failure case or scope limit.\n"
   "CONFIDENCE: LOW, MEDIUM, or HIGH with a short reason.\n"
   "UNKNOWN: what remains unresolved."
 ),
 "JSON6": (
   "Return exactly one JSON object and no other text. "
   "Use exactly these six string keys: ATTEMPT, ASSUMPTIONS, EVIDENCE_NEEDED, "
   "COUNTEREXAMPLE_OR_LIMIT, CONFIDENCE, UNKNOWN. All six values must be non-empty strings. "
   "CONFIDENCE must begin with LOW, MEDIUM, or HIGH."
 ),
 "TAG6": (
   "Return exactly these six XML-like tags and no other text: "
   "<ATTEMPT>...</ATTEMPT><ASSUMPTIONS>...</ASSUMPTIONS>"
   "<EVIDENCE_NEEDED>...</EVIDENCE_NEEDED>"
   "<COUNTEREXAMPLE_OR_LIMIT>...</COUNTEREXAMPLE_OR_LIMIT>"
   "<CONFIDENCE>...</CONFIDENCE><UNKNOWN>...</UNKNOWN>. "
   "Every tag must contain non-empty text."
 )
}

def ensure_tasks():
    p=ROOT/"artifacts/corrective_curriculum_g1_tasks.json"
    if not p.exists():
        subprocess.check_call([sys.executable,str(ROOT/"tools/build_corrective_curriculum_g1_tasks.py")])
    return json.loads(p.read_text())

def task_for(pack,target):
    return next(x for x in pack["tasks"] if x["task_id"]=="G1-"+target+"-01")

def parse_plain(raw):
    out={}; cur=None
    aliases={"EVIDENCE NEEDED":"EVIDENCE_NEEDED","COUNTEREXAMPLE OR LIMIT":"COUNTEREXAMPLE_OR_LIMIT"}
    aliases.update({k:k for k in KEYS})
    for line in raw.splitlines():
        s=line.strip().replace("**","").replace("__","").replace(chr(96),"").replace("：",":")
        if not s: continue
        if ":" in s:
            h,v=s.split(":",1)
            k=aliases.get(h.strip().upper())
            if k:
                cur=k; out[k]=v.strip(); continue
        if cur:
            out[cur]=(out[cur]+" "+s).strip()
    return out

def parse_json(raw):
    text=raw.strip()
    m=re.search(r"\{.*\}",text,re.S)
    if not m: return {}
    try:
        obj=json.loads(m.group())
    except Exception:
        return {}
    return {k:str(obj.get(k,"")).strip() for k in KEYS}

def parse_tags(raw):
    out={}
    for k in KEYS:
        m=re.search(r"<"+re.escape(k)+r">\s*(.*?)\s*</"+re.escape(k)+r">",raw,re.S|re.I)
        out[k]=m.group(1).strip() if m else ""
    return out

def parse_contract(name,raw):
    if name=="JSON6": return parse_json(raw)
    if name=="TAG6": return parse_tags(raw)
    return parse_plain(raw)

def valid(parsed):
    return all(str(parsed.get(k,"")).strip() for k in KEYS)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    a=ap.parse_args()

    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    tok=AutoTokenizer.from_pretrained(a.model_id,revision=a.revision)
    model=AutoModelForCausalLM.from_pretrained(
        a.model_id,revision=a.revision,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True
    )
    model.eval()
    pack=ensure_tasks()
    lineage=hashlib.sha256((a.model_id+"|"+a.revision).encode()).hexdigest()
    root=Path(a.output_root); root.mkdir(parents=True,exist_ok=True)

    def infer(target,contract_name,split):
        task=task_for(pack,target)
        system=(
          "You are generating an auditable candidate lesson for CEREBRON target AI "+target+". "
          "Stay within corrective axis "+task["corrective_axis"]+". "
          "Do not claim independent proof, weight training, or physical validation."
        )
        user=(
          "TASK_ID: "+task["task_id"]+"\n"
          "INSTRUCTION: "+task["instruction"]+"\n"
          "SPECIALIZATION_TAGS: "+", ".join(task.get("specialization_tags",[]))+"\n\n"
          +CONTRACTS[contract_name]
        )
        started=time.time()
        rec={
          "schema":"CEREBRON_FORMAT_EVOLUTION_RECEIPT_V1",
          "run_id":int(a.run_id),"split":split,"target_ai":target,
          "contract":contract_name,"task_id":task["task_id"],"task_sha256":task["task_sha256"],
          "model_id":a.model_id,"model_revision":a.revision,"lineage_fingerprint":lineage,
          "real_execution":True,"weight_change":False,"training_eligible":False,
          "operational_mutation_f172_f173_f174":False
        }
        try:
            msgs=[{"role":"system","content":system},{"role":"user","content":user}]
            try:
                kw={"tokenize":False,"add_generation_prompt":True}
                if "Qwen3" in a.model_id: kw["enable_thinking"]=False
                prompt=tok.apply_chat_template(msgs,**kw)
            except Exception:
                prompt=system+"\n\n"+user+"\nASSISTANT:\n"
            x=tok(prompt,return_tensors="pt")
            with torch.no_grad():
                y=model.generate(**x,max_new_tokens=220,do_sample=False,repetition_penalty=1.12,no_repeat_ngram_size=4)
            raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            parsed=parse_contract(contract_name,raw)
            echo=("task_id:" in raw.lower()) or ("return exactly" in raw.lower())
            rec.update(
              inference="PASS",raw_output=raw[:9000],parsed=parsed,
              parse_ok=valid(parsed) and not echo,prompt_echo=echo,
              output_sha256=hashlib.sha256(raw.encode()).hexdigest()
            )
            del x,y
        except Exception as e:
            rec.update(inference="FAIL",parse_ok=False,prompt_echo=False,
                       failure_class=type(e).__name__,failure_message=str(e)[:1600])
        rec["latency_s"]=round(time.time()-started,3)
        return rec

    validation=[]
    for cname in CONTRACTS:
        for target in VAL_TARGETS:
            r=infer(target,cname,"validation")
            validation.append(r)
            print(json.dumps({"split":"validation","target":target,"contract":cname,"parse_ok":r.get("parse_ok")}),flush=True)

    metrics={}
    for cname in CONTRACTS:
        xs=[r for r in validation if r["contract"]==cname]
        metrics[cname]={
          "parse_pass":sum(bool(r.get("parse_ok")) for r in xs),
          "inference_pass":sum(r.get("inference")=="PASS" for r in xs),
          "count":len(xs),
          "prompt_chars":len(CONTRACTS[cname])
        }
    winner=sorted(CONTRACTS,key=lambda c:(-metrics[c]["parse_pass"],-metrics[c]["inference_pass"],metrics[c]["prompt_chars"],c))[0]

    holdout=[]
    for cname in ("PLAIN6",winner):
        # If winner is baseline, run it once, not twice.
        if cname=="PLAIN6" and winner=="PLAIN6" and holdout:
            continue
        for target in HOLDOUT_TARGETS:
            r=infer(target,cname,"holdout")
            holdout.append(r)
            print(json.dumps({"split":"holdout","target":target,"contract":cname,"parse_ok":r.get("parse_ok")}),flush=True)

    base=[r for r in holdout if r["contract"]=="PLAIN6"]
    win=[r for r in holdout if r["contract"]==winner]
    if winner=="PLAIN6":
        win=base
    base_pass=sum(bool(r.get("parse_ok")) for r in base)
    win_pass=sum(bool(r.get("parse_ok")) for r in win)
    gain=win_pass-base_pass
    promoted=(winner!="PLAIN6" and gain>0 and win_pass>=3)

    all_rows=validation+holdout
    for idx,r in enumerate(all_rows):
        p=root/"receipts"/("%03d_%s_%s_%s.json"%(idx,r["split"],r["contract"],r["target_ai"]))
        p.parent.mkdir(parents=True,exist_ok=True)
        r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest()
        p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")

    summary={
      "schema":"CEREBRON_FORMAT_CONTRACT_EVOLUTION_V1",
      "run_id":int(a.run_id),"model_id":a.model_id,"model_revision":a.revision,
      "lineage_fingerprint":lineage,
      "validation_targets":VAL_TARGETS,"holdout_targets":HOLDOUT_TARGETS,
      "candidate_metrics":metrics,"winner":winner,
      "holdout_baseline_parse_pass":base_pass,
      "holdout_winner_parse_pass":win_pass,
      "holdout_gain":gain,
      "promotion_decision":"PROMOTE_CONTRACT_CANDIDATE" if promoted else "HOLD_NO_PROVEN_GAIN",
      "weight_change":False,"training_released":False,
      "operational_mutation_f172_f173_f174":False
    }
    (root/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,sort_keys=True))
    if any(r.get("inference")!="PASS" for r in all_rows):
        raise SystemExit(2)

if __name__=="__main__":
    main()
