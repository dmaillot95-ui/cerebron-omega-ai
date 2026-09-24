#!/usr/bin/env python3
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

LABELS=["DECISION","RESULT","ASSUMPTIONS","EVIDENCE","FAILURE_MODES","UNCERTAINTY"]

def parse_labels(raw):
    out={};current=None
    for line in raw.splitlines():
        s=line.strip()
        if not s: continue
        hit=False
        for lab in LABELS:
            if s.upper().startswith(lab+":"):
                current=lab
                out[lab]=s.split(":",1)[1].strip()
                hit=True
                break
        if not hit and current:
            out[current]=(out[current]+" "+s).strip()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worker",required=True)
    ap.add_argument("--wave",choices=["A","B"],required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    cfg=json.loads((ROOT/"config/s10-marginal-gain-mission-v1.json").read_text())
    pool=cfg["wave_A_baseline"] if args.wave=="A" else cfg["wave_B_extension"]
    spec=next(x for x in pool if x["worker_id"]==args.worker)
    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]
    problem_sha=hashlib.sha256(cfg["problem_text"].encode()).hexdigest()

    deps=["config/s10-marginal-gain-mission-v1.json","config/geometric-vector-learning-v1.json"]
    role_contract=None
    if spec["role_id"]=="SYSTEM_ARCHITECT":
        role_contract=json.loads((ROOT/"config/system-architect-evidence-contract-v1.json").read_text())
        deps.append("config/system-architect-evidence-contract-v1.json")

    inp=make_envelope(
        spec["endpoint"],"CEREBRON",cfg["mission_id"],"QUESTION",
        cfg["problem_text"],problem_ref=problem_sha,evidence_level="E0",
        confidence=0.0,risk=0.4,dependencies=deps,
        json_payload={
          "wave":args.wave,"worker_id":spec["worker_id"],"parent_ai":spec["parent_ai"],
          "role_id":spec["role_id"],"task":spec["task"],"problem":cfg["problem_text"]
        }
    )

    system=(
      "You are a specialist in CEREBRON. Address only the exact readiness-validation problem. "
      "Do not repeat instructions, do not invent a different scenario, and do not claim that shared-model outputs are independent evidence. "
      "Simulation, subsystem benches, and analogous-system telemetry must be bounded by their actual evidentiary scope. "
      "Identify concrete evidence gaps, failure modes, and next tests relevant to your assigned role."
    )
    if role_contract:
        system += " SYSTEM_ARCHITECT invariants: "+"; ".join(role_contract["invariant_rules"])+"."    
    user=f"""PROBLEM:
{cfg['problem_text']}

ROLE:
{spec['role_id']}

ROLE TASK:
{spec['task']}

Return exactly six labeled lines:
DECISION:
RESULT:
ASSUMPTIONS:
EVIDENCE:
FAILURE_MODES:
UNCERTAINTY:
"""

    t=time.time()
    r={
      "schema":"CEREBRON_S10_MARGINAL_WORKER_RECEIPT_V1",
      "mission_id":cfg["mission_id"],"run_id":args.run_id,"wave":args.wave,
      "worker_id":spec["worker_id"],"parent_ai":spec["parent_ai"],"role_id":spec["role_id"],
      "model_id":model_id,"revision":rev,"problem_sha256":problem_sha,
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
            prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        except Exception:
            prompt=system+"\n\n"+user+"\nASSISTANT:\n"
        x=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            y=model.generate(**x,max_new_tokens=360,do_sample=False,repetition_penalty=1.05)
        raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        parsed=parse_labels(raw)
        echo=any(p in raw.lower() for p in ["return exactly","role task:","problem_sha256","worker_id","role_id"])
        r.update(
          llm_inference=True,inference="PASS",raw_output=raw[:8000],
          parsed_content=parsed,parse_ok=all(parsed.get(k) for k in LABELS),
          prompt_echo=echo,result_sha256=hashlib.sha256(raw.encode()).hexdigest()
        )
    except Exception as e:
        r.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1600],parse_ok=False,prompt_echo=False)

    r["latency_s"]=round(time.time()-t,3)
    out_env=make_envelope(
      spec["endpoint"],"AGORA",cfg["mission_id"],"RESULT",
      r.get("raw_output") or r.get("failure_message") or "",
      problem_ref=problem_sha,evidence_level="E1" if r.get("inference")=="PASS" else "E0",
      confidence=0.7 if r.get("inference")=="PASS" else 0.0,risk=0.3,
      dependencies=["model:"+model_id,"revision:"+rev,r["spiralix_input_envelope_sha256"]],
      json_payload=r.get("parsed_content") or {"raw":r.get("raw_output","")}
    )
    r["spiralix_source_endpoint"]=spec["endpoint"]
    r["spiralix_output_envelope"]=out_env
    r["spiralix_envelope_sha256"]=sha256_obj(out_env)
    r["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest()
    r["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(r,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({
      "wave":args.wave,"worker":args.worker,"inference":r.get("inference"),
      "parse_ok":r.get("parse_ok"),"prompt_echo":r.get("prompt_echo"),
      "spiralix":bool(r.get("spiralix_envelope_sha256"))
    },sort_keys=True))
    if not r.get("llm_inference"): raise SystemExit(2)

if __name__=="__main__":
    main()
