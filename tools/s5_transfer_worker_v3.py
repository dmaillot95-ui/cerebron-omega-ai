#!/usr/bin/env python3
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

PARENTS={"SAPHEA-A":"SAPHEA","SAPHEA-B":"SAPHEA","SAPHEA-C":"SAPHEA","SPIRALION-A":"SPIRALION","ETHERION-A":"ETHERION"}
LABELS=["DECISION","RESULT","ASSUMPTIONS","EVIDENCE","FAILURE_MODES","UNCERTAINTY"]

def parse(raw):
    out={};current=None
    for line in raw.splitlines():
        s=line.strip()
        if not s: continue
        hit=False
        for lab in LABELS:
            if s.upper().startswith(lab+":"):
                current=lab;out[lab]=s.split(":",1)[1].strip();hit=True;break
        if not hit and current: out[current]=(out[current]+" "+s).strip()
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--worker",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    cfg=json.loads((ROOT/"config/s5-quality-transfer-pass2-v1.json").read_text())
    spec=next(x for x in cfg["workers"] if x["worker_id"]==args.worker)
    overlays=json.loads((ROOT/"config/role-overlays-v1.json").read_text()).get("overlays",{})
    role_overlay=overlays.get(spec["role_id"])
    role_contract=None
    if spec["role_id"]=="SYSTEM_ARCHITECT":
      role_contract=json.loads((ROOT/"config/system-architect-evidence-contract-v1.json").read_text())
    psha=hashlib.sha256(cfg["problem_text"].encode()).hexdigest()
    inp=make_envelope(spec["endpoint"],"CEREBRON",cfg["mission_id"],"QUESTION",cfg["problem_text"],problem_ref=psha,evidence_level="E0",confidence=0.0,risk=0.3,dependencies=["config/s5-quality-transfer-pass2-v1.json"]+(["config/system-architect-evidence-contract-v1.json"] if role_contract else []),json_payload={"problem":cfg["problem_text"],"role_id":spec["role_id"],"role_task":spec["role_task"],"role_contract":role_contract["invariant_rules"] if role_contract else None})
    system="Answer the exact engineering validation problem only. Simulation is model-based evidence, not automatically a physical test. Do not echo instructions or invent a different example. Be concise and explicit about evidence limits."
    if role_contract:
      system += " As SYSTEM_ARCHITECT, apply these invariant rules: " + "; ".join(role_contract["invariant_rules"]) + ". Minimum validation chain: " + "; ".join(role_contract["minimum_validation_chain"]) + "."
    if role_overlay:
      system += " ROLE OVERLAY: " + role_overlay.get("objective","") + " Canonical rule: " + role_overlay.get("canonical_rule","") + ". MUST: " + "; ".join(role_overlay.get("must",[])) + ". MUST NOT: " + "; ".join(role_overlay.get("must_not",[]))
    user=f"""PROBLEM:
{cfg['problem_text']}

ROLE:
{spec['role_id']}

TASK:
{spec['role_task']}

Return exactly six labeled lines:
DECISION:
RESULT:
ASSUMPTIONS:
EVIDENCE:
FAILURE_MODES:
UNCERTAINTY:
"""
    model_id="HuggingFaceTB/SmolLM3-3B";rev="a07cc9a04f16550a088caea529712d1d335b0ac1";t=time.time()
    r={"schema":"CEREBRON_S5_TRANSFER_PASS2_V3_WORKER","run_id":args.run_id,"mission_id":cfg["mission_id"],"worker_id":args.worker,"parent_ai":PARENTS[args.worker],"role_id":spec["role_id"],"problem_sha256":psha,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,"spiralix_input_envelope":inp,"spiralix_input_envelope_sha256":sha256_obj(inp)}
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(model_id,revision=rev);model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
      messages=[{"role":"system","content":system},{"role":"user","content":user}]
      try: prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
      except Exception: prompt=system+"\n\n"+user+"\nASSISTANT:\n"
      x=tok(prompt,return_tensors="pt")
      with torch.no_grad(): y=model.generate(**x,max_new_tokens=320,do_sample=False,repetition_penalty=1.05)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip();parsed=parse(raw)
      echo=any(p in raw.lower() for p in ["return exactly","your task","problem_sha256","worker_id","role_id"])
      r.update(llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed_content=parsed,parse_ok=all(parsed.get(k) for k in LABELS),prompt_echo=echo,result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False)
    r["latency_s"]=round(time.time()-t,3)
    env=make_envelope(spec["endpoint"],"AGORA",cfg["mission_id"],"RESULT",r.get("raw_output") or r.get("failure_message") or "",problem_ref=psha,evidence_level="E1" if r.get("inference")=="PASS" else "E0",confidence=.7 if r.get("inference")=="PASS" else 0.0,risk=.3,dependencies=["model:"+model_id,"revision:"+rev,r["spiralix_input_envelope_sha256"]],json_payload=r.get("parsed_content") or {"raw":r.get("raw_output","")})
    r["spiralix_source_endpoint"]=spec["endpoint"];r["spiralix_output_envelope"]=env;r["spiralix_envelope_sha256"]=sha256_obj(env);r["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest();r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"worker":args.worker,"inference":r.get("inference"),"parse_ok":r.get("parse_ok"),"prompt_echo":r.get("prompt_echo")},sort_keys=True))
    if not r.get("llm_inference"):raise SystemExit(2)
if __name__=="__main__":main()
