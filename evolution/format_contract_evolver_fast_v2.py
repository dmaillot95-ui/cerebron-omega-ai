#!/usr/bin/env python3
"""Fast format-contract evolution with one selection lineage and cross-lineage holdout.

Stage select: Qwen3 only, 3 contracts x 2 validation targets.
Stage holdout: selected contract vs baseline on 2 sealed targets for each pinned lineage.
No weights are changed.
"""
import argparse, hashlib, json, re, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
KEYS=["ATTEMPT","ASSUMPTIONS","EVIDENCE_NEEDED","COUNTEREXAMPLE_OR_LIMIT","CONFIDENCE","UNKNOWN"]
CONTRACTS={
 "PLAIN6":(
   "Return exactly six plain lines, no Markdown or numbering. "
   "Use ATTEMPT:, ASSUMPTIONS:, EVIDENCE_NEEDED:, COUNTEREXAMPLE_OR_LIMIT:, CONFIDENCE:, UNKNOWN:. "
   "Every field must be non-empty."
 ),
 "JSON6":(
   "Return one JSON object and no other text, with exactly six non-empty string keys: "
   "ATTEMPT, ASSUMPTIONS, EVIDENCE_NEEDED, COUNTEREXAMPLE_OR_LIMIT, CONFIDENCE, UNKNOWN."
 ),
 "TAG6":(
   "Return only six non-empty tags: <ATTEMPT>...</ATTEMPT><ASSUMPTIONS>...</ASSUMPTIONS>"
   "<EVIDENCE_NEEDED>...</EVIDENCE_NEEDED><COUNTEREXAMPLE_OR_LIMIT>...</COUNTEREXAMPLE_OR_LIMIT>"
   "<CONFIDENCE>...</CONFIDENCE><UNKNOWN>...</UNKNOWN>."
 )
}
SELECT_TARGETS=["SAPHEA","AELYS"]
HOLDOUT_TARGETS=["ETHERION","PSI"]

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
        if cur: out[cur]=(out[cur]+" "+s).strip()
    return out

def parse_json(raw):
    m=re.search(r"\{.*\}",raw,re.S)
    if not m: return {}
    try: obj=json.loads(m.group())
    except Exception: return {}
    return {k:str(obj.get(k,"")).strip() for k in KEYS}

def parse_tags(raw):
    out={}
    for k in KEYS:
        m=re.search(r"<"+re.escape(k)+r">\s*(.*?)\s*</"+re.escape(k)+r">",raw,re.S|re.I)
        out[k]=m.group(1).strip() if m else ""
    return out

def parse(name,raw):
    if name=="JSON6": return parse_json(raw)
    if name=="TAG6": return parse_tags(raw)
    return parse_plain(raw)

def valid(d):
    return all(str(d.get(k,"")).strip() for k in KEYS)

def load_model(model_id,revision):
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    tok=AutoTokenizer.from_pretrained(model_id,revision=revision)
    model=AutoModelForCausalLM.from_pretrained(
        model_id,revision=revision,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True
    )
    model.eval()
    return tok,model,torch

def infer(tok,model,torch,model_id,target,contract,pack):
    task=task_for(pack,target)
    system=(
      "Generate an auditable candidate lesson for target AI "+target+". "
      "Do not claim independent proof, neural training, or physical validation."
    )
    user=(
      "TASK_ID: "+task["task_id"]+"\n"
      "CORRECTIVE_AXIS: "+task["corrective_axis"]+"\n"
      "INSTRUCTION: "+task["instruction"]+"\n\n"+CONTRACTS[contract]
    )
    msgs=[{"role":"system","content":system},{"role":"user","content":user}]
    try:
        kw={"tokenize":False,"add_generation_prompt":True}
        if "Qwen3" in model_id: kw["enable_thinking"]=False
        prompt=tok.apply_chat_template(msgs,**kw)
    except Exception:
        prompt=system+"\n\n"+user+"\nASSISTANT:\n"
    started=time.time()
    x=tok(prompt,return_tensors="pt")
    with torch.no_grad():
        y=model.generate(**x,max_new_tokens=120,do_sample=False,repetition_penalty=1.08,no_repeat_ngram_size=3)
    raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
    parsed=parse(contract,raw)
    echo=("task_id:" in raw.lower()) or ("return exactly" in raw.lower())
    return {
      "target_ai":target,"task_id":task["task_id"],"task_sha256":task["task_sha256"],
      "contract":contract,"raw_output":raw[:6000],"parsed":parsed,
      "parse_ok":valid(parsed) and not echo,"prompt_echo":echo,
      "latency_s":round(time.time()-started,3),
      "output_sha256":hashlib.sha256(raw.encode()).hexdigest()
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",choices=["select","holdout"],required=True)
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    ap.add_argument("--winner-file")
    a=ap.parse_args()
    pack=ensure_tasks()
    tok,model,torch=load_model(a.model_id,a.revision)
    lineage=hashlib.sha256((a.model_id+"|"+a.revision).encode()).hexdigest()
    root=Path(a.output_root); root.mkdir(parents=True,exist_ok=True)
    rows=[]

    if a.stage=="select":
        for cname in CONTRACTS:
            for target in SELECT_TARGETS:
                r=infer(tok,model,torch,a.model_id,target,cname,pack)
                rows.append(r)
                print(json.dumps({"stage":"select","target":target,"contract":cname,"parse_ok":r["parse_ok"]}),flush=True)
        metrics={}
        for cname in CONTRACTS:
            xs=[r for r in rows if r["contract"]==cname]
            metrics[cname]={
              "parse_pass":sum(bool(x["parse_ok"]) for x in xs),
              "count":len(xs),
              "prompt_chars":len(CONTRACTS[cname]),
              "latency_s":round(sum(x["latency_s"] for x in xs),3)
            }
        winner=sorted(CONTRACTS,key=lambda c:(-metrics[c]["parse_pass"],metrics[c]["prompt_chars"],metrics[c]["latency_s"],c))[0]
        baseline_parse=metrics["PLAIN6"]["parse_pass"]
        winner_parse=metrics[winner]["parse_pass"]
        selection_gain=winner_parse-baseline_parse
        selection_eligible=(winner!="PLAIN6" and selection_gain>0)
        summary={
          "schema":"CEREBRON_FORMAT_EVOLUTION_FAST_SELECT_V2",
          "run_id":int(a.run_id),"model_id":a.model_id,"model_revision":a.revision,
          "lineage_fingerprint":lineage,"selection_targets":SELECT_TARGETS,
          "candidate_metrics":metrics,"winner":winner,
          "baseline_parse_pass":baseline_parse,
          "winner_parse_pass":winner_parse,
          "selection_gain":selection_gain,
          "selection_eligible":selection_eligible,
          "selection_decision":"ADVANCE_TO_HOLDOUT" if selection_eligible else "HOLD_NO_VALIDATION_GAIN",
          "weight_change":False,"training_released":False
        }
        (root/"winner.json").write_text(json.dumps(summary,indent=2)+"\n")
    else:
        if not a.winner_file:
            raise SystemExit("winner-file required")
        win=json.loads(Path(a.winner_file).read_text())["winner"]
        contracts=["PLAIN6"] if win=="PLAIN6" else ["PLAIN6",win]
        for cname in contracts:
            for target in HOLDOUT_TARGETS:
                r=infer(tok,model,torch,a.model_id,target,cname,pack)
                rows.append(r)
                print(json.dumps({"stage":"holdout","target":target,"contract":cname,"parse_ok":r["parse_ok"]}),flush=True)
        base=[r for r in rows if r["contract"]=="PLAIN6"]
        cand=[r for r in rows if r["contract"]==win] if win!="PLAIN6" else base
        bp=sum(bool(x["parse_ok"]) for x in base)
        cp=sum(bool(x["parse_ok"]) for x in cand)
        summary={
          "schema":"CEREBRON_FORMAT_EVOLUTION_FAST_HOLDOUT_V1",
          "run_id":int(a.run_id),"model_id":a.model_id,"model_revision":a.revision,
          "lineage_fingerprint":lineage,"holdout_targets":HOLDOUT_TARGETS,
          "winner":win,"baseline_parse_pass":bp,"candidate_parse_pass":cp,"gain":cp-bp,
          "candidate_not_worse":cp>=bp,
          "candidate_strict_gain":cp>bp,
          "weight_change":False,"training_released":False
        }
        (root/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")

    for i,r in enumerate(rows):
        p=root/"receipts"/("%02d_%s_%s.json"%(i,r["contract"],r["target_ai"]))
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
