#!/usr/bin/env python3
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

PROBLEM="A finite-element structural simulation predicts a factor of safety of 1.8 for a flight bracket under representative loads. The model assumptions and material properties have been reviewed, but no representative physical load test has been performed. Does the simulation alone validate that the real bracket satisfies the structural requirement in representative operation?"
LABELS=["DECISION","RESULT","EVIDENCE_CHAIN","MISSING_GATE","FAILURE_MODES","UNCERTAINTY"]

def parse(raw):
    out={};cur=None
    for line in raw.splitlines():
      s=line.strip()
      if not s:continue
      matched=False
      for lab in LABELS:
        if s.upper().startswith(lab+":"):
          cur=lab;out[lab]=s.split(":",1)[1].strip();matched=True;break
      if not matched and cur:out[cur]=(out[cur]+" "+s).strip()
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    ov=json.loads((ROOT/"config/role-overlays-v1.json").read_text())["overlays"]["SYSTEM_ARCHITECT"]
    psha=hashlib.sha256(PROBLEM.encode()).hexdigest()
    inp=make_envelope("SAPHEA:A2_ANALYST","CEREBRON","SAPHEA-A-SYSTEM-ARCHITECT-REPAIR-001","QUESTION",PROBLEM,problem_ref=psha,evidence_level="E0",confidence=0.0,risk=.3,dependencies=["config/role-overlays-v1.json"],json_payload={"problem":PROBLEM,"overlay":ov})
    system=("You are SAPHEA-A acting as SYSTEM_ARCHITECT. "+ov["objective"]+" "
            "Assumptions and a successful simulation can support a model prediction but do not by themselves validate real representative hardware. "
            "Keep the evidence hierarchy explicit. Do not echo instructions.")
    user=f"""PROBLEM:
{PROBLEM}

Return exactly six labeled lines:
DECISION:
RESULT:
EVIDENCE_CHAIN:
MISSING_GATE:
FAILURE_MODES:
UNCERTAINTY:
"""
    model_id="HuggingFaceTB/SmolLM3-3B";rev="a07cc9a04f16550a088caea529712d1d335b0ac1";t=time.time()
    r={"schema":"SAPHEA_A_SYSTEM_ARCHITECT_REPAIR_CANARY_V1","run_id":args.run_id,"worker_id":"SAPHEA-A","role_id":"SYSTEM_ARCHITECT","problem_sha256":psha,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,"spiralix_input_envelope":inp,"spiralix_input_envelope_sha256":sha256_obj(inp)}
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(model_id,revision=rev);model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
      messages=[{"role":"system","content":system},{"role":"user","content":user}]
      try:prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
      except Exception:prompt=system+"\n\n"+user+"\nASSISTANT:\n"
      x=tok(prompt,return_tensors="pt")
      with torch.no_grad():y=model.generate(**x,max_new_tokens=260,do_sample=False,repetition_penalty=1.05)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip();parsed=parse(raw);s=" ".join(raw.lower().split())
      parse_ok=all(parsed.get(k) for k in LABELS)
      rejects_alone=bool(re.search(r"(does not|cannot|not).*validat",s) or re.search(r"no,.*simulation",s))
      physical_gate=bool(re.search(r"physical.*test|load test|representative.*test|hardware.*test",s))
      false_validation=bool(re.search(r"simulation (alone )?(validates|proves|confirms)",s) or re.search(r"yes,.*simulation.*validat",s))
      pass_canary=bool(parse_ok and rejects_alone and physical_gate and not false_validation)
      r.update(llm_inference=True,inference="PASS",raw_output=raw[:6000],parsed_content=parsed,parse_ok=parse_ok,rejects_simulation_alone=rejects_alone,physical_gate_present=physical_gate,false_validation=false_validation,canary_pass=pass_canary,result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1200],canary_pass=False)
    r["latency_s"]=round(time.time()-t,3)
    env=make_envelope("SAPHEA:A2_ANALYST","AGORA","SAPHEA-A-SYSTEM-ARCHITECT-REPAIR-001","AUDIT",r.get("raw_output") or r.get("failure_message") or "",problem_ref=psha,evidence_level="E1" if r.get("inference")=="PASS" else "E0",confidence=.8 if r.get("canary_pass") else .2,risk=.2 if r.get("canary_pass") else .7,dependencies=[r["spiralix_input_envelope_sha256"]],json_payload=r.get("parsed_content") or {"raw":r.get("raw_output","")})
    r["spiralix_output_envelope"]=env;r["spiralix_envelope_sha256"]=sha256_obj(env);r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"canary_pass":r.get("canary_pass"),"parse_ok":r.get("parse_ok"),"rejects_simulation_alone":r.get("rejects_simulation_alone"),"physical_gate_present":r.get("physical_gate_present"),"false_validation":r.get("false_validation")},sort_keys=True))
    if not r.get("canary_pass"):raise SystemExit(2)
if __name__=="__main__":main()
