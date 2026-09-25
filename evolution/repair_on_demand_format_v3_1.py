#!/usr/bin/env python3
import argparse, glob, hashlib, json, re, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/cerebron-repair-on-demand-format-v3-1.json").read_text())
KEYS=CFG["fields"]

def canon(label):
    s=re.sub(r"[^A-Z]","",str(label).upper())
    if s.startswith("ATTEMPT"): return "ATTEMPT"
    if s.startswith("ASSUMPT"): return "ASSUMPTIONS"
    if "EVIDENCE" in s and ("NEED" in s or "REQ" in s): return "EVIDENCE_NEEDED"
    if "COUNTEREXAMPLE" in s or "LIMIT" in s: return "COUNTEREXAMPLE_OR_LIMIT"
    if s.startswith("CONFID"): return "CONFIDENCE"
    if s.startswith("UNKNOWN") or "UNRESOLVED" in s: return "UNKNOWN"
    return None

def robust_parse(raw):
    out={}
    # JSON/Python-like pairs.
    for m in re.finditer(r'''["']?([^"'\\n:{}]+)["']?\\s*:\\s*["']([^"'\\n}]*)["']''',raw):
        k=canon(m.group(1))
        if k and m.group(2).strip(): out[k]=m.group(2).strip()
    # XML-like tags.
    for m in re.finditer(r"<\\s*([^>/]+)\\s*>\\s*(.*?)(?=<\\s*/|<\\s*[^>]+>|$)",raw,re.S):
        k=canon(m.group(1))
        if k and m.group(2).strip(): out.setdefault(k,m.group(2).strip())
    # Plain labeled lines.
    cur=None
    for line in raw.splitlines():
        s=line.strip().replace("**","").replace("__","").replace(chr(96),"").replace("：",":")
        if not s: continue
        if ":" in s:
            h,v=s.split(":",1)
            k=canon(h)
            if k:
                cur=k
                if v.strip(): out.setdefault(k,v.strip())
                continue
        if cur and not s.startswith("<"):
            out[cur]=(out.get(cur,"")+" "+s).strip()
    return out

def confidence_ok(v):
    return bool(re.match(r"^(LOW|MEDIUM|HIGH)\\b",str(v).strip(),re.I))

def complete(d):
    return all(str(d.get(k,"")).strip() for k in KEYS) and confidence_ok(d.get("CONFIDENCE",""))

def clean_repair(field,raw):
    s=" ".join(x.strip() for x in raw.replace("**","").replace("__","").replace(chr(96),"").splitlines() if x.strip())
    if ":" in s:
        h,v=s.split(":",1)
        if canon(h)==field and v.strip(): s=v.strip()
    if field=="CONFIDENCE":
        u=s.upper()
        for level in ("LOW","MEDIUM","HIGH"):
            if level in u: return level
        return ""
    return s.strip()

def load_baselines(directory,targets):
    rows=[]
    for p in glob.glob(str(Path(directory)/"**/*.json"),recursive=True):
        try: r=json.load(open(p))
        except Exception: continue
        if r.get("contract")=="PLAIN6" and r.get("target_ai") in targets:
            rows.append(r)
    by={r["target_ai"]:r for r in rows}
    missing=[t for t in targets if t not in by]
    if missing: raise SystemExit("missing baseline receipts: "+",".join(missing))
    return by

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--baseline-dir",required=True)
    ap.add_argument("--targets",required=True)
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    a=ap.parse_args()
    targets=[x.strip() for x in a.targets.split(",") if x.strip()]
    baselines=load_baselines(a.baseline_dir,targets)

    parsed={t:robust_parse(baselines[t].get("raw_output","")) for t in targets}
    baseline_complete={t:complete(parsed[t]) for t in targets}
    repair_items=[]
    for t in targets:
        for k in KEYS:
            if not str(parsed[t].get(k,"")).strip() or (k=="CONFIDENCE" and not confidence_ok(parsed[t].get(k,""))):
                repair_items.append((t,k))

    started=time.time()
    repaired_raw={}
    if repair_items:
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        tok=AutoTokenizer.from_pretrained(a.model_id,revision=a.revision)
        if tok.pad_token_id is None: tok.pad_token=tok.eos_token
        tok.padding_side="left"
        model=AutoModelForCausalLM.from_pretrained(a.model_id,revision=a.revision,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True)
        model.eval()
        prompts=[]
        for target,field in repair_items:
            existing="; ".join(f"{k}={parsed[target][k]}" for k in KEYS if str(parsed[target].get(k,"")).strip())
            if field=="CONFIDENCE":
                instr="Return exactly one word: LOW, MEDIUM, or HIGH."
            elif field=="UNKNOWN":
                instr="State in at most 12 words what remains unresolved."
            else:
                instr="Return only the missing field value in at most 18 words."
            system="Repair one missing field in an auditable record. Do not repeat existing fields. "+instr
            user=f"TARGET_AI: {target}\nMISSING_FIELD: {field}\nEXISTING_FIELDS: {existing}\nReturn only the missing value."
            msgs=[{"role":"system","content":system},{"role":"user","content":user}]
            try:
                kw={"tokenize":False,"add_generation_prompt":True}
                if "Qwen3" in a.model_id: kw["enable_thinking"]=False
                prompt=tok.apply_chat_template(msgs,**kw)
            except Exception:
                prompt=system+"\n\n"+user+"\nASSISTANT:\n"
            prompts.append(prompt)
        batch=tok(prompts,return_tensors="pt",padding=True)
        with torch.no_grad():
            gen=model.generate(**batch,max_new_tokens=int(CFG["repair"]["max_new_tokens"]),do_sample=False,repetition_penalty=1.06,no_repeat_ngram_size=3,pad_token_id=tok.pad_token_id)
        n=batch["input_ids"].shape[1]
        for i,(target,field) in enumerate(repair_items):
            raw=tok.decode(gen[i][n:],skip_special_tokens=True).strip()
            repaired_raw[f"{target}:{field}"]=raw[:2000]
            val=clean_repair(field,raw)
            if val: parsed[target][field]=val

    receipts=[]
    for target in targets:
        final=parsed[target]
        rec={
          "schema":"CEREBRON_REPAIR_ON_DEMAND_RECEIPT_V3_1",
          "run_id":int(a.run_id),
          "target_ai":target,
          "model_id":a.model_id,
          "model_revision":a.revision,
          "source_output_sha256":baselines[target].get("output_sha256"),
          "baseline_robust_complete":baseline_complete[target],
          "missing_field_count_before":sum(1 for k in KEYS if not str(robust_parse(baselines[target].get("raw_output","")).get(k,"")).strip() or (k=="CONFIDENCE" and not confidence_ok(robust_parse(baselines[target].get("raw_output","")).get(k,"")))),
          "final_fields":final,
          "final_complete":complete(final),
          "repaired_fields":[k for tt,k in repair_items if tt==target],
          "repair_raw":{k.split(":",1)[1]:v for k,v in repaired_raw.items() if k.startswith(target+":")},
          "weight_change":False,
          "training_eligible":False,
          "operational_mutation_f172_f173_f174":False
        }
        raw=json.dumps(rec,sort_keys=True,separators=(",",":")).encode()
        rec["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
        receipts.append(rec)

    root=Path(a.output_root); root.mkdir(parents=True,exist_ok=True)
    for r in receipts:
        (root/(r["target_ai"]+".json")).write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    b=sum(bool(x) for x in baseline_complete.values())
    c=sum(r["final_complete"] for r in receipts)
    summary={
      "schema":"CEREBRON_REPAIR_ON_DEMAND_SHARD_V3_1",
      "run_id":int(a.run_id),
      "model_id":a.model_id,
      "model_revision":a.revision,
      "targets":targets,
      "baseline_robust_complete_count":b,
      "candidate_complete_count":c,
      "gain":c-b,
      "repair_prompt_count":len(repair_items),
      "latency_s":round(time.time()-started,3),
      "strict_gain":c>b,
      "all_complete":c==len(targets),
      "weight_change":False,
      "training_released":False
    }
    (root/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
