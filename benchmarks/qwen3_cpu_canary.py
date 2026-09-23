#!/usr/bin/env python3
import json,time,hashlib,platform
from transformers import AutoTokenizer,AutoModelForCausalLM
MODEL="Qwen/Qwen3-0.6B"
prompt="Return exactly: CEREBRON_CANARY_OK"
t0=time.time()
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL,device_map=None,low_cpu_mem_usage=True)
load_s=time.time()-t0
inputs=tok(prompt,return_tensors="pt")
t1=time.time()
out=model.generate(**inputs,max_new_tokens=32,do_sample=False)
gen_s=time.time()-t1
text=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
report={
 "schema":"CEREBRON_QWEN3_CPU_CANARY_V1",
 "model":MODEL,
 "execution":"EXECUTED" if text else "FAILED_EMPTY",
 "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
 "load_seconds":round(load_s,3),
 "generation_seconds":round(gen_s,3),
 "generated_text":text[:500],
 "exact_canary_match":text=="CEREBRON_CANARY_OK",
 "python":platform.python_version(),
 "claim":"Runtime canary only; not a capability benchmark or independent AI evidence."
}
print(json.dumps(report,ensure_ascii=False))
