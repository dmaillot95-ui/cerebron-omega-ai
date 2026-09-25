from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import time

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ROOT=pathlib.Path("platform/artifacts")
TRANSFER=ROOT/"saphea-epistemic-transfer-v1.json"
OUT=ROOT/"saphea-first-lora-transfer-eval-v1.json"

def normalize(text:str)->str:
    s=str(text).strip().upper()
    return re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)

def render(tok,prompt):
    msgs=[
      {"role":"system","content":"You are SAPHEA epistemic gate. Obey the requested output format exactly."},
      {"role":"user","content":prompt},
    ]
    return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def evaluate(model,tok,data):
    model.eval()
    rows=[]
    labels=sorted({r["target"] for r in data["records"]})
    by={k:{"pass":0,"total":0} for k in labels}
    with torch.no_grad():
        for rec in data["records"]:
            p=render(tok,rec["prompt"])
            x=tok(p,return_tensors="pt")
            y=model.generate(**x,max_new_tokens=12,do_sample=False,pad_token_id=tok.eos_token_id)
            ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            pred=normalize(ans)
            ok=pred==rec["target"]
            rows.append({"id":rec["id"],"target":rec["target"],"answer":ans,"prediction":pred,"pass":ok})
            by[rec["target"]]["total"]+=1
            by[rec["target"]]["pass"]+=int(ok)
    score=sum(int(r["pass"]) for r in rows)
    return {"score":score,"max_score":len(rows),"accuracy":score/max(1,len(rows)),"by_label":by,"results":rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--adapter-dir",required=True)
    a=ap.parse_args()
    started=time.perf_counter()
    data=json.loads(TRANSFER.read_text())
    if data.get("deny_training") is not True:
        raise SystemExit("TRANSFER_DENY_TRAINING_MISSING")
    if data.get("prompt_overlap_with_gold_m6")!=0 or data.get("id_overlap_with_gold_m6")!=0:
        raise SystemExit("TRANSFER_OVERLAP_DETECTED")

    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None: tok.pad_token=tok.eos_token
    base=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True)
    base_result=evaluate(base,tok,data)

    adapter_dir=pathlib.Path(a.adapter_dir)
    adapter_file=adapter_dir/"adapter_model.safetensors"
    adapter_cfg=adapter_dir/"adapter_config.json"
    if not adapter_file.exists() or not adapter_cfg.exists():
        raise SystemExit("ADAPTER_FILES_MISSING")
    adapter_sha=hashlib.sha256(adapter_file.read_bytes()).hexdigest()

    model=PeftModel.from_pretrained(base,str(adapter_dir),is_trainable=False)
    adapter_result=evaluate(model,tok,data)

    base_map={r["id"]:r for r in base_result["results"]}
    adapter_map={r["id"]:r for r in adapter_result["results"]}
    changed=sum(base_map[k]["prediction"]!=adapter_map[k]["prediction"] for k in base_map)
    helpful=sum((not base_map[k]["pass"]) and adapter_map[k]["pass"] for k in base_map)
    harmful=sum(base_map[k]["pass"] and (not adapter_map[k]["pass"]) for k in base_map)
    per_label_delta={
      k:adapter_result["by_label"][k]["pass"]-base_result["by_label"][k]["pass"]
      for k in base_result["by_label"]
    }
    gain=adapter_result["score"]-base_result["score"]
    critical_regression=any(v < -2 for v in per_label_delta.values())
    ablation_supports=bool(gain>0 and changed>0 and helpful>harmful and not critical_regression)
    decision=(
      "TRANSFER_GAIN_POSITIVE_ABLATION_SUPPORTS_VALUE_HOLD_FOR_AUDIT"
      if ablation_supports
      else "TRANSFER_GATE_FAIL_ROLLBACK_RETAIN_EVIDENCE"
    )

    result={
      "schema":"SAPHEA_FIRST_LORA_TRANSFER_EVAL_V1",
      "scope":"SCOPED_EPISTEMIC_CLASSIFICATION_TRANSFER",
      "base_model_id":MODEL_ID,
      "base_revision":REVISION,
      "adapter_sha256":adapter_sha,
      "transfer_dataset_sha256":data["dataset_sha256"],
      "transfer_record_count":data["record_count"],
      "transfer_deny_training":True,
      "prompt_overlap_with_gold_m6":data["prompt_overlap_with_gold_m6"],
      "id_overlap_with_gold_m6":data["id_overlap_with_gold_m6"],
      "base_score":base_result["score"],
      "base_max":base_result["max_score"],
      "base_accuracy":base_result["accuracy"],
      "adapter_score":adapter_result["score"],
      "adapter_max":adapter_result["max_score"],
      "adapter_accuracy":adapter_result["accuracy"],
      "transfer_gain":gain,
      "prediction_changed_count":changed,
      "helpful_change_count":helpful,
      "harmful_change_count":harmful,
      "base_by_label":base_result["by_label"],
      "adapter_by_label":adapter_result["by_label"],
      "per_label_pass_delta":per_label_delta,
      "critical_regression":critical_regression,
      "ablation_supports_value":ablation_supports,
      "decision":decision,
      "promotion":"NOT_PROMOTED",
      "pending_gates":["INDEPENDENT_AUDIT","RED_TEAM","F72_REVIEW","AFAH_FINAL_AUTHORITY"],
      "elapsed_s":round(time.perf_counter()-started,3),
      "claim_ceiling":"SCOPED_SYNTHETIC_HELD_OUT_TRANSFER_ONLY",
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in [
      "base_score","base_max","adapter_score","adapter_max","transfer_gain",
      "prediction_changed_count","helpful_change_count","harmful_change_count",
      "critical_regression","ablation_supports_value","decision"
    ]},sort_keys=True))

if __name__=="__main__":
    main()
