#!/usr/bin/env python3
import argparse,hashlib,json,time
from pathlib import Path
from tools.spiralix_bus import make_envelope,sha256_obj
from tools.spiralix_receipt_bridge import bridge_receipt

ENDPOINTS={"SAPHEA-A":"SAPHEA:A2_ANALYST","SAPHEA-B":"SAPHEA:A4_AUDITOR","SAPHEA-C":"SAPHEA:A5_COUNTER_AUDITOR","SPIRALION-A":"SPIRALION:A7_SYNTHESIZER","ETHERION-A":"ETHERION:A2_ANALYST"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--worker",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    cfg=json.loads(Path("config/m11-s5-v2-mission-v1.json").read_text());spec=next(x for x in cfg["workers"] if x["worker_id"]==args.worker)
    psha=hashlib.sha256(cfg["problem_text"].encode()).hexdigest()
    if psha!=cfg["problem_sha256"]: raise SystemExit("PROBLEM_SHA_MISMATCH")
    input_payload={"problem_sha256":psha,"problem_text":cfg["problem_text"],"worker_id":spec["worker_id"],"role_id":spec["role_id"],"role_task":spec["role_task"]}
    input_env=make_envelope(ENDPOINTS[args.worker],"CEREBRON",cfg["mission_id"],"QUESTION",cfg["problem_text"],problem_ref=psha,evidence_level="E0",confidence=0.0,risk=0.4,dependencies=["config/m11-s5-v2-mission-v1.json","config/role-diverse-prompt-contract-v2.json"],json_payload=input_payload)
    prompt=f"""SPIRALIX INPUT
GLYPH={input_env['glyph_expression']}
VECTOR={json.dumps(input_env['V'],ensure_ascii=False)}
PAYLOAD_SHA256={input_env['payload_sha256']}

SYSTEM CONTRACT
Answer ONLY the exact problem below.
Do NOT replace it with another example or theorem.
Do NOT echo these instructions.
If evidence is insufficient, use INSUFFICIENT_EVIDENCE.

PROBLEM_SHA256={psha}
PROBLEM={cfg['problem_text']}
WORKER_ID={spec['worker_id']}
ROLE_ID={spec['role_id']}
ROLE_TASK={spec['role_task']}

Return one JSON object and nothing else with exactly these keys:
problem_sha256, worker_id, role_id, decision, result, assumptions, evidence_used, evidence_needed, failure_modes, residual_uncertainty, unrelated_example_used, instruction_echo_detected.
decision must be one of SUPPORTED, REFUTED, UNRESOLVED, INSUFFICIENT_EVIDENCE.
unrelated_example_used and instruction_echo_detected must be booleans.
"""
    model_id=cfg["model"]["id"];rev=cfg["model"]["revision"];t=time.time()
    r={"schema":"CEREBRON_M11_WORKER_RECEIPT_V2","mission_id":cfg["mission_id"],"run_id":args.run_id,"worker_id":spec["worker_id"],"parent_ai":spec["parent_ai"],"role_id":spec["role_id"],"problem_sha256":psha,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,"spiralix_input_envelope":input_env,"spiralix_input_envelope_sha256":sha256_obj(input_env)}
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
      model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
      x=tok(prompt,return_tensors="pt")
      with torch.no_grad(): y=model.generate(**x,max_new_tokens=260,do_sample=False)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
      parsed=None
      try:
        s=raw.find("{");e=raw.rfind("}")
        if s>=0 and e>s: parsed=json.loads(raw[s:e+1])
      except Exception: parsed=None
      required={"problem_sha256","worker_id","role_id","decision","result","assumptions","evidence_used","evidence_needed","failure_modes","residual_uncertainty","unrelated_example_used","instruction_echo_detected"}
      schema_ok=isinstance(parsed,dict) and set(parsed.keys())==required
      hash_ok=bool(schema_ok and parsed["problem_sha256"]==psha)
      identity_ok=bool(schema_ok and parsed["worker_id"]==spec["worker_id"] and parsed["role_id"]==spec["role_id"])
      no_drift=bool(schema_ok and parsed["unrelated_example_used"] is False and parsed["instruction_echo_detected"] is False)
      decision_ok=bool(schema_ok and parsed["decision"] in ["SUPPORTED","REFUTED","UNRESOLVED","INSUFFICIENT_EVIDENCE"])
      valid=bool(schema_ok and hash_ok and identity_ok and no_drift and decision_ok)
      r.update(llm_inference=True,inference="PASS",raw_output=raw[:6000],parsed_output=parsed,schema_ok=schema_ok,hash_ok=hash_ok,identity_ok=identity_ok,no_drift=no_drift,decision_ok=decision_ok,contract_valid=valid,result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
      r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1200],contract_valid=False)
    r["latency_s"]=round(time.time()-t,3);r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,default=str).encode()).hexdigest();r=bridge_receipt(r,"AGORA","RESULT")
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"worker":args.worker,"inference":r.get("inference"),"contract_valid":r.get("contract_valid"),"spiralix_source_endpoint":r.get("spiralix_source_endpoint"),"spiralix_envelope_sha256":r.get("spiralix_envelope_sha256"),"receipt_sha256":r["receipt_sha256"]},sort_keys=True))
if __name__=="__main__": main()
