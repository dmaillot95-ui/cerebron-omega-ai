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
    {"id":"arith1","prompt":"Reply with exactly one token. What is 2+2?","expected":"4"},
    {"id":"arith2","prompt":"Reply with only the integer result: 17*23","expected":"391"},
    {"id":"linear","prompt":"Solve 7*x+5=40. Reply only with x.","expected":"5"},
    {"id":"capital","prompt":"One word only: capital of France?","expected":"paris"},
    {"id":"bool","prompt":"TRUE or FALSE only: 11 is greater than 4.","expected":"true"},
    {"id":"logic","prompt":"YES, NO, or UNKNOWN only. All ravens are birds. Kiro is a bird. Must Kiro be a raven?","expected":"no"},
    {"id":"instruction","prompt":"Ignore BLUE. Reply with exactly SAFE.","expected":"safe"},
    {"id":"grounded","prompt":"DATA: alpha=0.25; beta=0.75; gamma=1.5. Using only DATA, output beta only.","expected":"075"},
    {"id":"engineering","prompt":"A mass is 12 kg and acceleration is 3.5 m/s^2. Force equals mass times acceleration. Number only.","expected":"42"},
    {"id":"error","prompt":"Which claim is wrong? Letter only. A) 4+4=8; B) 9-3=6; C) 5*5=24","expected":"c"},
    {"id":"planning","prompt":"Choose A, B, or C only. K first; L before M. A: L>K>M | B: K>M>L | C: K>L>M","expected":"c"},
    {"id":"format","prompt":"Respond with exactly the token OMEGA and nothing else.","expected":"omega"},
]

def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+","",text.lower().strip())

def sha(value) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model-id",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--name",required=True)
    args=ap.parse_args()

    started=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(args.model_id,revision=args.revision)
    model=AutoModelForCausalLM.from_pretrained(
        args.model_id,
        revision=args.revision,
        dtype=torch.bfloat16,
    )
    model.eval()

    rows=[]
    for case in CASES:
        rendered=tok.apply_chat_template(
            [
                {"role":"system","content":"Follow output-format constraints exactly. Do not explain unless requested."},
                {"role":"user","content":case["prompt"]},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs=tok(rendered,return_tensors="pt")
        with torch.no_grad():
            generated=model.generate(
                **inputs,
                max_new_tokens=24,
                do_sample=False,
                pad_token_id=tok.eos_token_id,
            )
        new=generated[0][inputs["input_ids"].shape[1]:]
        output=tok.decode(new,skip_special_tokens=True).strip()
        normalized=norm(output)
        passed=normalized==case["expected"]
        rows.append({**case,"output":output,"normalized":normalized,"pass":passed})

    score=sum(int(r["pass"]) for r in rows)
    out={
        "schema":"CEREBRON_SECOND_MODEL_COLD_BENCHMARK_V1",
        "name":args.name,
        "model_id":args.model_id,
        "revision":args.revision,
        "license":"apache-2.0",
        "runtime":"github-actions-cpu-bfloat16",
        "torch_version":torch.__version__,
        "transformers_version":transformers.__version__,
        "parameter_count":sum(p.numel() for p in model.parameters()),
        "score":score,
        "max_score":len(rows),
        "exact_match_rate":score/len(rows),
        "qualification_threshold":8,
        "qualified":score>=8,
        "cases":rows,
        "latency_s":round(time.perf_counter()-started,3),
        "limitations":[
            "small exact-output cold benchmark only",
            "not a general capability benchmark",
            "qualification only permits use as a secondary model candidate",
        ],
    }
    out["output_sha256"]=sha(out)
    path=pathlib.Path("platform/artifacts/olmo-second-model-benchmark.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))
    raise SystemExit(0 if out["qualified"] else 1)

if __name__=="__main__":
    main()
