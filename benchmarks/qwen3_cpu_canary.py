#!/usr/bin/env python3
import json,time,hashlib,platform
from transformers import AutoTokenizer,AutoModelForCausalLM
MODEL="Qwen/Qwen3-0.6B"
EXPECTED="CEREBRON_CANARY_OK"
messages=[
 {"role":"system","content":"You are a deterministic runtime canary. Follow the user instruction exactly. Output only the requested literal token and nothing else."},
 {"role":"user","content":"Output exactly CEREBRON_CANARY_OK and nothing else."}
]
t0=time.time()
tok=AutoTokenizer.from_pretrained(MODEL)
model=AutoModelForCausalLM.from_pretrained(MODEL,device_map=None,low_cpu_mem_usage=True)
load_s=time.time()-t0
rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
inputs=tok(rendered,return_tensors="pt")
t1=time.time()
out=model.generate(**inputs,max_new_tokens=16,do_sample=False,pad_token_id=tok.eos_token_id)
gen_s=time.time()-t1
text=tok.decode(out[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
report={
 "schema":"CEREBRON_QWEN3_CPU_CANARY_V2",
 "model":MODEL,
 "chat_template":True,
 "thinking_disabled":True,
 "execution":"EXECUTED" if text else "FAILED_EMPTY",
 "prompt_sha256":hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest(),
 "load_seconds":round(load_s,3),
 "generation_seconds":round(gen_s,3),
 "generated_text":text[:500],
 "exact_canary_match":text==EXPECTED,
 "promotion_gate":"PASS" if text==EXPECTED else "BLOCKED",
 "python":platform.python_version(),
 "claim":"Instruction-format runtime canary only; not a capability benchmark or independent AI evidence."
}
print(json.dumps(report,ensure_ascii=False))
