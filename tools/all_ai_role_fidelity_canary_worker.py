#!/usr/bin/env python3
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj
from tools.all_ai_strategy_council_worker import LABELS,parse_labels

DUAL_MODEL_CANDIDATES={"ELYSION","ELYSIUM","SAELION","NEXUS","F148-ALPHA","F150-DELTA","F149-OMEGA"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ai",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    cfg=json.loads((ROOT/"config/all-ai-strategy-council-v1.json").read_text())
    reg=json.loads((ROOT/cfg["registry"]).read_text())
    spec=next(x for x in reg["ais"] if x["ai_id"]==a.ai)
    if not spec.get("available"):
        raise SystemExit("AI_NOT_AVAILABLE")

    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]
    endpoint=f'{a.ai}:{cfg["representative_slot"]}'
    tags=", ".join(spec["specialization_tags"])
    dual_rule=(
      "You ARE an existing Greek native dual-model candidate. DUAL_CORE may be YES only if two distinct model functions are necessary and you state an ablation against the best single-model baseline."
      if a.ai in DUAL_MODEL_CANDIDATES else
      "You are NOT an existing Greek native dual-model candidate. DUAL_CORE must be NO unless you identify a specific existing candidate that should receive your function; do not create a new dual-core AI."
    )
    system=(
      "You are one specialization inside CEREBRON, not a generic strategist. "
      f"AI={a.ai}; identity={spec['identity']}; parent_function={spec['parent_function']}; specialization_tags={tags}. "
      "Your answer is invalid if another unrelated role could give essentially the same answer. "
      "Anchor PRIORITY, PROPOSAL, TEST, UNIQUE_VALUE and BENCHMARK directly in your parent function and specialization tags. "
      "The global roadmap is context, not a default topic. Do NOT choose GVL, geometric gates, transfer families or dual-core merely because they appear in the roadmap. "
      "Mention GVL only when your declared specialization directly requires it. "
      "Prefer a concrete role-specific failure, measurement, interface, experiment, uncertainty or decision. "
      + dual_rule + " "
      "Respect REALITY>COHERENCE, CLAIM<=EVIDENCE, REPAIR BEFORE SCALE, TRANSFER BEFORE GENERALITY, QUALITY>QUANTITY."
    )
    user=f"""ROLE CONTRACT
AI: {a.ai}
PARENT_FUNCTION: {spec['parent_function']}
SPECIALIZATION_TAGS: {tags}

CURRENT SYSTEM FACTS
- Operational coalition scale remains 5 after measured marginal-gain test.
- Knowledge banks and provenance are active.
- GVL geometric-growth gate remains 1/4 and is NOT a universal priority.
- Platform/local runtime, memory, AGORA and farm bridge have scoped evidence.
- Greek dual-model architecture exists only for ELYSION, ELYSIUM, SAELION, ALPHA, OMEGA, DELTA and NEXUS.
- Double core means one Greek AI containing two distinct models, not two logical roles.

OUTPUT EXACTLY 8 PLAIN LINES, 8-35 words per value:
PRIORITY: one next action that is specific to YOUR role.
PROPOSAL: one implementation/repair specific to YOUR role.
TEST: one role-specific falsifiable test.
STOP: one waste or false-confidence pattern YOUR role should stop.
UNIQUE_VALUE: why YOUR role is nonredundant over the next three cycles.
BENCHMARK: one observable metric tied to YOUR role.
DUAL_CORE: YES only under the candidate/evidence rule above; otherwise NO with a concrete reason.
RISK: one role-specific unknown that could invalidate your proposal.
"""
    problem_sha=hashlib.sha256((a.ai+"|"+spec["parent_function"]+"|"+tags).encode()).hexdigest()
    inp=make_envelope(endpoint,"CEREBRON",cfg["mission_id"],"QUESTION",user,
        problem_ref=problem_sha,evidence_level="E0",confidence=0.0,risk=0.4,
        dependencies=[cfg["registry"],"config/geometric-vector-learning-v1.json"],
        json_payload={"ai_id":a.ai,"parent_function":spec["parent_function"],"tags":spec["specialization_tags"],"anti_convergence":True})

    rec={"schema":"CEREBRON_ROLE_FIDELITY_CANARY_RECEIPT_V1","mission_id":"M42-ROLE-FIDELITY-REPAIR-001",
         "run_id":a.run_id,"ai_id":a.ai,"identity":spec["identity"],"parent_function":spec["parent_function"],
         "specialization_tags":spec["specialization_tags"],"specialization_vector":spec["specialization_vector"],
         "endpoint":endpoint,"model_id":model_id,"revision":rev,"real_execution":True,"llm_inference":False,
         "format_contract_version":"ROLE_FIDELITY_V1","dual_candidate":a.ai in DUAL_MODEL_CANDIDATES,
         "spiralix_input_envelope":inp,"spiralix_input_sha256":sha256_obj(inp)}
    t=time.time()
    try:
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
        dtype=torch.bfloat16 if "Qwen3" in model_id else torch.float32
        model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,torch_dtype=dtype,low_cpu_mem_usage=True)
        msgs=[{"role":"system","content":system},{"role":"user","content":user}]
        kwargs={"tokenize":False,"add_generation_prompt":True}
        if "Qwen3" in model_id: kwargs["enable_thinking"]=False
        prompt=tok.apply_chat_template(msgs,**kwargs)
        x=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            y=model.generate(**x,max_new_tokens=300,do_sample=False,repetition_penalty=1.15,no_repeat_ngram_size=4)
        raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        parsed=parse_labels(raw)
        echo=any(p in raw.lower() for p in ["output exactly 8","role contract","parent_function:","specialization_tags:"])
        rec.update(llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed=parsed,
                   parse_ok=all(parsed.get(k) for k in LABELS) and not echo,prompt_echo=echo,
                   output_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
        rec.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False)
    rec["latency_s"]=round(time.time()-t,3)
    out_env=make_envelope(endpoint,"AGORA","M42-ROLE-FIDELITY-REPAIR-001","SYNTHESIS",
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
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(rec,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"ai":a.ai,"inference":rec.get("inference"),"parse_ok":rec.get("parse_ok"),"dual_candidate":rec["dual_candidate"]},sort_keys=True))
    if not rec.get("llm_inference"):
        raise SystemExit(2)

if __name__=="__main__":
    main()
