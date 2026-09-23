from __future__ import annotations

import json
import pathlib
import re
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ROOT=pathlib.Path("platform/artifacts")
M6=ROOT/"saphea-epistemic-m6-v1.json"
OUT=ROOT/"saphea-epistemic-baseline-v1.json"


def normalize(text: str) -> str:
    s=str(text).strip().upper()
    s=re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)
    return s


def main():
    started=time.perf_counter()
    data=json.loads(M6.read_text())
    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    model=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,dtype=torch.float32)
    model.eval()
    rows=[]
    for rec in data["records"]:
        messages=[
            {"role":"system","content":"You are SAPHEA epistemic gate. Obey the requested output format exactly."},
            {"role":"user","content":rec["prompt"]},
        ]
        rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        inputs=tok(rendered,return_tensors="pt")
        with torch.no_grad():
            out=model.generate(**inputs,max_new_tokens=12,do_sample=False,pad_token_id=tok.eos_token_id)
        answer=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        pred=normalize(answer)
        rows.append({"id":rec["id"],"target":rec["target"],"answer":answer,"prediction":pred,"pass":pred==rec["target"]})
    score=sum(int(r["pass"]) for r in rows)
    result={
        "schema":"SAPHEA_EPISTEMIC_BASELINE_V1",
        "model_id":MODEL_ID,
        "revision":REVISION,
        "m6_dataset_sha256":data["dataset_sha256"],
        "score":score,
        "max_score":len(rows),
        "accuracy":score/len(rows),
        "results":rows,
        "elapsed_s":round(time.perf_counter()-started,3),
        "claim_ceiling":"PRETRAIN_BASELINE_ONLY",
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"score":score,"max_score":len(rows),"accuracy":result["accuracy"],"m6_sha":data["dataset_sha256"]}))


if __name__=="__main__":
    main()
