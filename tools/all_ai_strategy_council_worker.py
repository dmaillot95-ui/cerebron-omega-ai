#!/usr/bin/env python3
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

LABELS=["PRIORITY","PROPOSAL","TEST","STOP","UNIQUE_VALUE","BENCHMARK","DUAL_CORE","RISK"]

def parse_labels(raw):
    out={}; cur=None
    for line in raw.splitlines():
        s=line.strip()
        if not s: continue
        # Accept plain labels and common Markdown wrappers such as **PRIORITY:**.
        cleaned=re.sub(r"^[\\s>\\-#*]+","",s)
        hit=False
        for lab in LABELS:
            m=re.match(r"^\\*{0,2}"+re.escape(lab)+r"\\*{0,2}\\s*:\\s*\\*{0,2}(.*)$",cleaned,re.I)
            if m:
                cur=lab
                out[lab]=m.group(1).strip().strip("*").strip()
                hit=True
                break
        if not hit and cur:
            continuation=re.sub(r"^[\\s>\\-#*]+","",s).strip()
            out[cur]=(out[cur]+" "+continuation).strip()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ai",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    cfg=json.loads((ROOT/"config/all-ai-strategy-council-v1.json").read_text())
    reg=json.loads((ROOT/cfg["registry"]).read_text())
    spec=next(x for x in reg["ais"] if x["ai_id"]==a.ai)
    if not spec.get("available"): raise SystemExit("AI_NOT_AVAILABLE")
    endpoint=f'{a.ai}:{cfg["representative_slot"]}'
    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]
    route="\n".join(cfg["line_of_route"])
    questions="\n".join(f"- {q}" for q in cfg["questions"])
    system=(
      "You are producing one advisory proposal under a CEREBRON logical-AI specialization contract. "
      "You are not an independent model identity and must not claim independent evidence. "
      f"Logical AI: {spec['identity']} ({a.ai}). Functional specialization: {spec['parent_function']}. "
      f"Specialization tags: {', '.join(spec['specialization_tags'])}. "
      "Stay inside this specialization. Give concrete, testable, nonredundant advice for improving the system. "
      "Respect REALITY>COHERENCE, CLAIM<=EVIDENCE, REPAIR BEFORE SCALE, TRANSFER BEFORE GENERALITY, and QUALITY>QUANTITY."
    )
    user=f"""CURRENT LINE OF ROUTE:
{route}

QUESTIONS:
{questions}

Return exactly eight labeled lines:
PRIORITY:
PROPOSAL:
TEST:
STOP:
UNIQUE_VALUE:
BENCHMARK:
DUAL_CORE:
RISK:
"""
    problem_sha=hashlib.sha256((route+"\n"+questions).encode()).hexdigest()
    inp=make_envelope(endpoint,"CEREBRON",cfg["mission_id"],"QUESTION",user,
        problem_ref=problem_sha,evidence_level="E0",confidence=0.0,risk=0.4,
        dependencies=[cfg["registry"],"config/geometric-vector-learning-v1.json"],
        json_payload={"ai_id":a.ai,"identity":spec["identity"],"function":spec["parent_function"],"tags":spec["specialization_tags"],"line_of_route":cfg["line_of_route"]})
    rec={"schema":"CEREBRON_ALL_AI_STRATEGY_COUNCIL_RECEIPT_V1","mission_id":cfg["mission_id"],"run_id":a.run_id,
         "ai_id":a.ai,"identity":spec["identity"],"parent_function":spec["parent_function"],
         "specialization_tags":spec["specialization_tags"],"specialization_vector":spec["specialization_vector"],
         "endpoint":endpoint,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,
         "format_contract_version":"V2_MARKDOWN_TOLERANT",
         "spiralix_input_envelope":inp,"spiralix_input_sha256":sha256_obj(inp)}
    t=time.time()
    try:
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
        model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
        msgs=[{"role":"system","content":system},{"role":"user","content":user}]
        try: prompt=tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
        except Exception: prompt=system+"\n\n"+user+"\nASSISTANT:\n"
        x=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            y=model.generate(**x,max_new_tokens=420,do_sample=False,repetition_penalty=1.05)
        raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        parsed=parse_labels(raw)
        echo=any(p in raw.lower() for p in ["return exactly eight","current line of route:","questions:"])
        rec.update(llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed=parsed,
                   parse_ok=all(parsed.get(k) for k in LABELS),prompt_echo=echo,
                   output_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
        rec.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False)
    rec["latency_s"]=round(time.time()-t,3)
    out_env=make_envelope(endpoint,"AGORA",cfg["mission_id"],"SYNTHESIS",
        rec.get("raw_output") or rec.get("failure_message") or "",
        problem_ref=problem_sha,evidence_level="E1" if rec.get("inference")=="PASS" else "E0",
        confidence=0.55 if rec.get("inference")=="PASS" else 0.0,risk=0.5,
        dependencies=["model:"+model_id,"revision:"+rev,rec["spiralix_input_sha256"]],
        json_payload=rec.get("parsed") or {"raw":rec.get("raw_output","")})
    rec["spiralix_output_envelope"]=out_env
    rec["spiralix_output_sha256"]=sha256_obj(out_env)
    rec["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest()
    rec["independent_evidence"]=False
    rec["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in rec.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(rec,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"ai":a.ai,"inference":rec.get("inference"),"parse_ok":rec.get("parse_ok"),"spiralix":bool(rec.get("spiralix_output_sha256"))},sort_keys=True))
    if not rec.get("llm_inference"): raise SystemExit(2)
if __name__=="__main__": main()
