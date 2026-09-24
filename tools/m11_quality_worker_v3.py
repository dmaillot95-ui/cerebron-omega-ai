#!/usr/bin/env python3
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

ENDPOINTS={
 "SAPHEA-A":"SAPHEA:A2_ANALYST",
 "SAPHEA-B":"SAPHEA:A4_AUDITOR",
 "SAPHEA-C":"SAPHEA:A5_COUNTER_AUDITOR",
 "SPIRALION-A":"SPIRALION:A7_SYNTHESIZER",
 "ETHERION-A":"ETHERION:A2_ANALYST"
}
LABELS=["DECISION","RESULT","ASSUMPTIONS","EVIDENCE","FAILURE_MODES","UNCERTAINTY"]

def parse_labels(raw):
    out={}
    current=None
    for line in raw.splitlines():
        s=line.strip()
        if not s: continue
        matched=False
        for lab in LABELS:
            pref=lab+":"
            if s.upper().startswith(pref):
                current=lab
                out[lab]=s[len(pref):].strip()
                matched=True
                break
        if not matched and current:
            out[current]=(out[current]+" "+s).strip()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worker",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    cfg=json.loads((ROOT/"config/m11-s5-v2-mission-v1.json").read_text())
    spec=next(x for x in cfg["workers"] if x["worker_id"]==args.worker)
    psha=cfg["problem_sha256"]
    payload={"problem":cfg["problem_text"],"problem_sha256":psha,"worker_id":spec["worker_id"],"role_id":spec["role_id"],"role_task":spec["role_task"]}
    inp=make_envelope(
      ENDPOINTS[args.worker],"CEREBRON",cfg["mission_id"]+"-V3","QUESTION",
      cfg["problem_text"],problem_ref=psha,evidence_level="E0",confidence=0.0,risk=0.3,
      dependencies=["config/m11-quality-pass1-v3-contract.json"],json_payload=payload
    )
    system=(
      "You are one specialist in CEREBRON. Answer the exact problem only. "
      "Do not repeat instructions or placeholders. Do not invent another example. "
      "Different prompts or repeated executions are not automatically independent evidence. "
      "Be concise and evidence-bounded."
    )
    user=f"""PROBLEM:
{cfg['problem_text']}

YOUR ROLE:
{spec['role_id']}

YOUR TASK:
{spec['role_task']}

Return exactly six labeled lines:
DECISION: your direct conclusion
RESULT: your role-specific answer
ASSUMPTIONS: key assumptions or NONE
EVIDENCE: what supports the conclusion
FAILURE_MODES: shared-dependency or reasoning failures
UNCERTAINTY: what remains unresolved
"""
    model_id=cfg["model"]["id"];rev=cfg["model"]["revision"];t=time.time()
    r={
      "schema":"CEREBRON_M11_V3_WORKER_RECEIPT",
      "mission_id":cfg["mission_id"]+"-V3","run_id":args.run_id,
      "worker_id":spec["worker_id"],"parent_ai":spec["parent_ai"],"role_id":spec["role_id"],
      "problem_sha256":psha,"model_id":model_id,"revision":rev,
      "real_execution":True,"llm_inference":False,
      "spiralix_input_envelope":inp,"spiralix_input_envelope_sha256":sha256_obj(inp)
    }
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
      model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
      messages=[{"role":"system","content":system},{"role":"user","content":user}]
      try:
        text_prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
      except Exception:
        text_prompt=system+"\n\n"+user+"\nASSISTANT:\n"
      x=tok(text_prompt,return_tensors="pt")
      with torch.no_grad():
        y=model.generate(**x,max_new_tokens=320,do_sample=False,repetition_penalty=1.05)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
      parsed=parse_labels(raw)
      parse_ok=all(parsed.get(k) for k in LABELS)
      echo_patterns=["PROBLEM_SHA256","WORKER_ID","ROLE_ID","return exactly","your role:","your task:"]
      prompt_echo=any(p.lower() in raw.lower() for p in echo_patterns)
      r.update(llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed_content=parsed,
               parse_ok=parse_ok,prompt_echo=prompt_echo,
               result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
      r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False)
    r["latency_s"]=round(time.time()-t,3)
    cognitive=r.get("parsed_content") or {"raw":r.get("raw_output","")}
    out_env=make_envelope(
      ENDPOINTS[args.worker],"AGORA",cfg["mission_id"]+"-V3","RESULT",
      r.get("raw_output") or r.get("failure_message") or "",
      problem_ref=psha,evidence_level="E1" if r.get("inference")=="PASS" else "E0",
      confidence=0.7 if r.get("inference")=="PASS" else 0.0,risk=0.3,
      dependencies=["model:"+model_id,"revision:"+rev,r["spiralix_input_envelope_sha256"]],
      json_payload=cognitive
    )
    r["spiralix_source_endpoint"]=ENDPOINTS[args.worker]
    r["spiralix_output_envelope"]=out_env
    r["spiralix_envelope_sha256"]=sha256_obj(out_env)
    r["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest()
    r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"worker":args.worker,"inference":r.get("inference"),"parse_ok":r.get("parse_ok"),"prompt_echo":r.get("prompt_echo"),"spiralix_envelope_sha256":r["spiralix_envelope_sha256"]},sort_keys=True))
    if not r.get("llm_inference"): raise SystemExit(2)
if __name__=="__main__": main()
