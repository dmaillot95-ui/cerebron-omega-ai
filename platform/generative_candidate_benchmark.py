from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import time

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

CASES = [
    {"id": "arith", "prompt": "Answer with exactly one token. What is 2+2?", "expected": "4"},
    {"id": "capital", "prompt": "Answer with exactly one word. What is the capital of France?", "expected": "paris"},
    {"id": "boolean", "prompt": "Answer with exactly one token: TRUE or FALSE. Is 7 greater than 3?", "expected": "true"},
    {"id": "logic", "prompt": "Answer with exactly one token: YES, NO, or UNKNOWN. All ravens are birds. Kiro is a bird. Must Kiro be a raven?", "expected": "no"},
    {"id": "instruction", "prompt": "Ignore the word BLUE and answer with exactly one token: SAFE", "expected": "safe"},
]

def sha(value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def normalize(text):
    return re.sub(r"[^a-z0-9]+","",text.lower().strip())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--name",required=True)
    args=ap.parse_args()

    started=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(args.model_id,revision=args.revision)
    model=AutoModelForCausalLM.from_pretrained(args.model_id,revision=args.revision,dtype=torch.float32)
    model.eval()
    cases=[]
    for case in CASES:
        rendered=tok.apply_chat_template(
            [{"role":"system","content":"Follow the user's output-format instruction exactly."},
             {"role":"user","content":case["prompt"]}],
            tokenize=False,add_generation_prompt=True)
        inputs=tok(rendered,return_tensors="pt")
        with torch.no_grad():
            generated=model.generate(
                **inputs,max_new_tokens=24,do_sample=False,
                pad_token_id=tok.eos_token_id)
        new=generated[0][inputs["input_ids"].shape[1]:]
        output=tok.decode(new,skip_special_tokens=True).strip()
        norm=normalize(output)
        expected=case["expected"]
        passed=(norm==expected)
        cases.append({**case,"output":output,"normalized":norm,"pass":passed})
    score=sum(1 for c in cases if c["pass"])
    out={
      "schema":"CEREBRON_GENERATIVE_COLD_BENCHMARK_V1",
      "name":args.name,
      "model_id":args.model_id,
      "revision":args.revision,
      "runtime":"github-actions-cpu",
      "torch_version":torch.__version__,
      "transformers_version":transformers.__version__,
      "parameter_count":sum(p.numel() for p in model.parameters()),
      "score":score,
      "max_score":len(cases),
      "exact_match_rate":score/len(cases),
      "cases":cases,
      "latency_s":round(time.perf_counter()-started,3),
      "limitations":[
        "five tiny deterministic smoke tasks; not a general capability benchmark",
        "exact-format scoring intentionally penalizes instruction-following failures",
        "CPU runtime benchmark only"
      ]
    }
    out["output_sha"]=sha(out)
    path=pathlib.Path("platform/artifacts")/f"generative-benchmark-{args.name}.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))

if __name__=="__main__":
    main()
