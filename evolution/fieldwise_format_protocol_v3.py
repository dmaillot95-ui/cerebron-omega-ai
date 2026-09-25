#!/usr/bin/env python3
import argparse, hashlib, json, re, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/cerebron-fieldwise-format-v3.json").read_text())

def ensure_tasks():
    p=ROOT/"artifacts/corrective_curriculum_g1_tasks.json"
    if not p.exists():
        subprocess.check_call([sys.executable,str(ROOT/"tools/build_corrective_curriculum_g1_tasks.py")])
    return json.loads(p.read_text())

def task_for(pack,target):
    return next(x for x in pack["tasks"] if x["task_id"]=="G1-"+target+"-01")

def clean_value(field,raw):
    s=raw.strip().replace("**","").replace("__","").replace(chr(96),"")
    s=re.sub(r"^\s*[-*#]+\s*","",s)
    # Remove accidental label prefix but do not require it.
    if ":" in s.splitlines()[0] if s.splitlines() else False:
        first,*rest=s.splitlines()
        h,v=first.split(":",1)
        if re.sub(r"[^A-Z]","",h.upper()).startswith(re.sub(r"[^A-Z]","",field.upper())[:6]):
            s=(v+"\n"+"\n".join(rest)).strip()
    s=" ".join(x.strip() for x in s.splitlines() if x.strip())
    if field=="CONFIDENCE":
        u=s.upper()
        level="HIGH" if "HIGH" in u else ("MEDIUM" if "MEDIUM" in u else ("LOW" if "LOW" in u else None))
        if level:
            tail=re.sub(r"(?i)\b(HIGH|MEDIUM|LOW)\b","",s,count=1).strip(" :-")
            return level + (": "+tail if tail else "")
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--targets",required=True)
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    args=ap.parse_args()

    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM

    targets=[x.strip() for x in args.targets.split(",") if x.strip()]
    pack=ensure_tasks()
    tok=AutoTokenizer.from_pretrained(args.model_id,revision=args.revision)
    if tok.pad_token_id is None:
        tok.pad_token=tok.eos_token
    tok.padding_side="left"
    model=AutoModelForCausalLM.from_pretrained(
        args.model_id,revision=args.revision,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True
    )
    model.eval()
    root=Path(args.output_root); root.mkdir(parents=True,exist_ok=True)
    lineage=hashlib.sha256((args.model_id+"|"+args.revision).encode()).hexdigest()
    receipts=[]

    for target in targets:
        task=task_for(pack,target)
        prompts=[]
        for f in CFG["fields"]:
            system=(
              "You provide one short field for an auditable CEREBRON record. "
              "Return only the requested field value, with no label, list marker, preface, or explanation."
            )
            user=(
              "TARGET_AI: "+target+"\n"
              "CORRECTIVE_AXIS: "+task["corrective_axis"]+"\n"
              "TASK: "+task["instruction"]+"\n"
              "REQUESTED_FIELD: "+f["key"]+"\n"
              "INSTRUCTION: "+f["instruction"]+"\n"
              "MAX_WORDS: "+str(f["max_words"])+"\n"
              "Return only the field value."
            )
            msgs=[{"role":"system","content":system},{"role":"user","content":user}]
            try:
                kw={"tokenize":False,"add_generation_prompt":True}
                if "Qwen3" in args.model_id:
                    kw["enable_thinking"]=False
                prompt=tok.apply_chat_template(msgs,**kw)
            except Exception:
                prompt=system+"\n\n"+user+"\nASSISTANT:\n"
            prompts.append(prompt)

        started=time.time()
        batch=tok(prompts,return_tensors="pt",padding=True)
        with torch.no_grad():
            generated=model.generate(
                **batch,
                max_new_tokens=int(CFG["generation"]["max_new_tokens_per_field"]),
                do_sample=False,
                repetition_penalty=1.08,
                no_repeat_ngram_size=3,
                pad_token_id=tok.pad_token_id
            )
        input_len=batch["input_ids"].shape[1]
        values={}
        raw_fields={}
        for i,f in enumerate(CFG["fields"]):
            raw=tok.decode(generated[i][input_len:],skip_special_tokens=True).strip()
            raw_fields[f["key"]]=raw[:3000]
            values[f["key"]]=clean_value(f["key"],raw)

        confidence_ok=bool(re.match(r"^(LOW|MEDIUM|HIGH)\b",values.get("CONFIDENCE",""),re.I))
        nonempty={k:bool(str(values.get(k,"")).strip()) for k in [f["key"] for f in CFG["fields"]]}
        structure_complete=all(nonempty.values())
        semantic_complete=structure_complete and confidence_ok
        assembled=json.dumps(values,sort_keys=True,ensure_ascii=False,separators=(",",":"))
        rec={
          "schema":"CEREBRON_FIELDWISE_FORMAT_RECEIPT_V3",
          "run_id":int(args.run_id),
          "target_ai":target,
          "task_id":task["task_id"],
          "task_sha256":task["task_sha256"],
          "model_id":args.model_id,
          "model_revision":args.revision,
          "lineage_fingerprint":lineage,
          "field_count":len(values),
          "nonempty_fields":sum(nonempty.values()),
          "structure_complete":structure_complete,
          "semantic_complete":semantic_complete,
          "confidence_canonical":confidence_ok,
          "values":values,
          "raw_fields":raw_fields,
          "assembled_sha256":hashlib.sha256(assembled.encode()).hexdigest(),
          "latency_s":round(time.time()-started,3),
          "real_execution":True,
          "weight_change":False,
          "training_eligible":False,
          "operational_mutation_f172_f173_f174":False
        }
        raw=json.dumps(rec,sort_keys=True,default=str,separators=(",",":")).encode()
        rec["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
        p=root/"receipts"/(target+".json")
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n")
        receipts.append(rec)
        print(json.dumps({
          "target":target,
          "structure_complete":structure_complete,
          "semantic_complete":semantic_complete,
          "nonempty_fields":sum(nonempty.values()),
          "confidence_canonical":confidence_ok,
          "latency_s":rec["latency_s"]
        },sort_keys=True),flush=True)

    summary={
      "schema":"CEREBRON_FIELDWISE_FORMAT_SHARD_V3",
      "run_id":int(args.run_id),
      "model_id":args.model_id,
      "model_revision":args.revision,
      "lineage_fingerprint":lineage,
      "targets":targets,
      "receipt_count":len(receipts),
      "structure_complete_count":sum(r["structure_complete"] for r in receipts),
      "semantic_complete_count":sum(r["semantic_complete"] for r in receipts),
      "mean_nonempty_fields":round(sum(r["nonempty_fields"] for r in receipts)/max(1,len(receipts)),3),
      "weight_change":False,
      "training_released":False,
      "operational_mutation_f172_f173_f174":False
    }
    (root/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
