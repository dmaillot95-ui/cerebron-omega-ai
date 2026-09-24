#!/usr/bin/env python3
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

LABELS=["DECISION","RESULT","ASSUMPTIONS","EVIDENCE","FAILURE_MODES","UNCERTAINTY"]

def parse_labels(raw):
    out={}; current=None
    for line in raw.splitlines():
        s=line.strip()
        if not s: continue
        matched=False
        for lab in LABELS:
            if s.upper().startswith(lab+":"):
                current=lab; out[lab]=s.split(":",1)[1].strip(); matched=True; break
        if not matched and current:
            out[current]=(out[current]+" "+s).strip()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worker",required=True)
    ap.add_argument("--wave",choices=["BASELINE","GVL"],required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    cfg=json.loads((ROOT/"config/gvl-b3-causal-confounding-v1.json").read_text())
    spec=next(x for x in cfg["workers"] if x["worker_id"]==args.worker)
    psha=hashlib.sha256(cfg["problem_text"].encode()).hexdigest()

    gvl=json.loads((ROOT/"config/geometric-vector-learning-v1.json").read_text())
    coax=gvl["coaxial_axis"]["invariants"] if args.wave=="GVL" else []
    payload={"problem":cfg["problem_text"],"role_id":spec["role_id"],"role_task":spec["role_task"],"wave":args.wave,"coaxial_invariants":coax}
    inp=make_envelope(spec["endpoint"],"CEREBRON",cfg["mission_id"]+"-"+args.wave,"QUESTION",cfg["problem_text"],problem_ref=psha,evidence_level="E0",confidence=0.0,risk=0.4,dependencies=["config/gvl-b3-causal-confounding-v1.json"]+(["config/geometric-vector-learning-v1.json"] if args.wave=="GVL" else []),json_payload=payload)

    system=(
      "You are one specialist in a controlled causal-evidence benchmark. "
      "Answer only the exact problem. Do not echo instructions. Do not invent another dataset. "
      "State what the evidence supports, what it does not establish, and what uncertainty remains."
    )
    if coax:
      system += " Apply these generic CEREBRON coaxial invariants: " + "; ".join(coax) + "."
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
    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]; t=time.time()
    r={"schema":"CEREBRON_GVL_B3_WORKER_V1","run_id":args.run_id,"mission_id":cfg["mission_id"],"wave":args.wave,"worker_id":args.worker,"parent_ai":spec["parent_ai"],"role_id":spec["role_id"],"problem_sha256":psha,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,"spiralix_input_envelope":inp,"spiralix_input_envelope_sha256":sha256_obj(inp)}
    try:
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
        model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
        try: prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        except Exception: prompt=system+"\n\n"+user+"\nASSISTANT:\n"
        x=tok(prompt,return_tensors="pt")
        with torch.no_grad(): y=model.generate(**x,max_new_tokens=320,do_sample=False,repetition_penalty=1.05)
        raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        parsed=parse_labels(raw)
        echo=any(p in raw.lower() for p in ["return exactly","problem_sha256","worker_id","role_id","your task:"])
        r.update(llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed_content=parsed,parse_ok=all(parsed.get(k) for k in LABELS),prompt_echo=echo,result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
        r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False)
    r["latency_s"]=round(time.time()-t,3)
    env=make_envelope(spec["endpoint"],"AGORA",cfg["mission_id"]+"-"+args.wave,"RESULT",r.get("raw_output") or r.get("failure_message") or "",problem_ref=psha,evidence_level="E1" if r.get("inference")=="PASS" else "E0",confidence=.7 if r.get("inference")=="PASS" else 0.0,risk=.4,dependencies=["model:"+model_id,"revision:"+rev,r["spiralix_input_envelope_sha256"]],json_payload=r.get("parsed_content") or {"raw":r.get("raw_output","")})
    r["spiralix_source_endpoint"]=spec["endpoint"]; r["spiralix_output_envelope"]=env; r["spiralix_envelope_sha256"]=sha256_obj(env)
    r["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest()
    r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"wave":args.wave,"worker":args.worker,"inference":r.get("inference"),"parse_ok":r.get("parse_ok"),"prompt_echo":r.get("prompt_echo")},sort_keys=True))
    if not r.get("llm_inference"): raise SystemExit(2)
if __name__=="__main__": main()
