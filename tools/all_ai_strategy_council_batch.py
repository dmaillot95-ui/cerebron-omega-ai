#!/usr/bin/env python3
import argparse,hashlib,json,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from tools.spiralix_bus import make_envelope,sha256_obj
from tools.all_ai_strategy_council_worker import LABELS,parse_labels

def build_prompt(cfg,spec,ai_id):
    route="\n".join(cfg["line_of_route"])
    questions="\n".join(f"- {q}" for q in cfg["questions"])
    system=(
      "You are producing one advisory proposal under a CEREBRON logical-AI specialization contract. "
      "You are not an independent model identity and must not claim independent evidence. "
      f"Logical AI: {spec['identity']} ({ai_id}). Functional specialization: {spec['parent_function']}. "
      f"Specialization tags: {', '.join(spec['specialization_tags'])}. "
      "Stay inside this specialization. Give concrete, testable, nonredundant advice for improving the system. "
      "Respect REALITY>COHERENCE, CLAIM<=EVIDENCE, REPAIR BEFORE SCALE, TRANSFER BEFORE GENERALITY, and QUALITY>QUANTITY."
    )
    user=f"""CEREBRON LINE OF ROUTE:
{route}

OUTPUT CONTRACT — EXACTLY 8 PLAIN LINES.
No Markdown. No bullets. No numbering. No blank lines. Do not repeat a label inside a value.
Keep each value between 8 and 30 words.
PRIORITY: state the single highest-leverage next action.
PROPOSAL: state one concrete implementation or repair.
TEST: state one exact verification test.
STOP: state one thing CEREBRON should stop or avoid.
UNIQUE_VALUE: state your specialization's unique value for the next three cycles.
BENCHMARK: state one observable or numeric metric deciding whether your contribution is useful.
DUAL_CORE: for Greek dual-model architecture only, say YES with two model-core functions plus ablation, or NO with reason.
RISK: state the main unknown or failure mode that could invalidate the proposal.
"""
    problem_sha=hashlib.sha256((route+"\n"+questions).encode()).hexdigest()
    return system,user,problem_sha

def run_one(ai_id,run_id,out_root,cfg,reg,tok,model,torch):
    spec=next(x for x in reg["ais"] if x["ai_id"]==ai_id)
    if not spec.get("available"):
        raise RuntimeError(f"AI_NOT_AVAILABLE:{ai_id}")
    endpoint=f'{ai_id}:{cfg["representative_slot"]}'
    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]
    system,user,problem_sha=build_prompt(cfg,spec,ai_id)
    inp=make_envelope(
        endpoint,"CEREBRON",cfg["mission_id"],"QUESTION",user,
        problem_ref=problem_sha,evidence_level="E0",confidence=0.0,risk=0.4,
        dependencies=[cfg["registry"],"config/geometric-vector-learning-v1.json"],
        json_payload={
          "ai_id":ai_id,"identity":spec["identity"],"function":spec["parent_function"],
          "tags":spec["specialization_tags"],"line_of_route":cfg["line_of_route"]
        }
    )
    rec={
      "schema":"CEREBRON_ALL_AI_STRATEGY_COUNCIL_RECEIPT_V1",
      "mission_id":cfg["mission_id"],"run_id":run_id,
      "ai_id":ai_id,"identity":spec["identity"],"parent_function":spec["parent_function"],
      "specialization_tags":spec["specialization_tags"],"specialization_vector":spec["specialization_vector"],
      "endpoint":endpoint,"model_id":model_id,"revision":rev,
      "real_execution":True,"llm_inference":False,
      "execution_mode":"BATCH_SHARD_SHARED_MODEL_LOAD",
      "format_contract_version":"V7_QWEN3_UNICODE_ALIAS_STRICT",
      "spiralix_input_envelope":inp,"spiralix_input_sha256":sha256_obj(inp)
    }
    t=time.time()
    try:
        msgs=[{"role":"system","content":system},{"role":"user","content":user}]
        try:
            kwargs={"tokenize":False,"add_generation_prompt":True}
            if "Qwen3" in model_id:
                kwargs["enable_thinking"]=False
            prompt=tok.apply_chat_template(msgs,**kwargs)
        except Exception:
            prompt=system+"\n\n"+user+"\nASSISTANT:\n"
        x=tok(prompt,return_tensors="pt")
        with torch.no_grad():
            y=model.generate(
              **x,max_new_tokens=160,do_sample=False,
              repetition_penalty=1.15,no_repeat_ngram_size=4
            )
        raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        parsed=parse_labels(raw)
        echo=any(p in raw.lower() for p in [
          "output contract","state the single highest leverage",
          "return exactly eight","current line of route:","questions:"
        ])
        rec.update(
          llm_inference=True,inference="PASS",raw_output=raw[:7000],parsed=parsed,
          parse_ok=all(parsed.get(k) for k in LABELS) and not echo,prompt_echo=echo,
          output_sha256=hashlib.sha256(raw.encode()).hexdigest()
        )
        del x,y
    except Exception as e:
        rec.update(
          inference="FAIL",failure_class=type(e).__name__,
          failure_message=str(e)[:1500],parse_ok=False,prompt_echo=False
        )
    rec["latency_s"]=round(time.time()-t,3)
    out_env=make_envelope(
        endpoint,"AGORA",cfg["mission_id"],"SYNTHESIS",
        rec.get("raw_output") or rec.get("failure_message") or "",
        problem_ref=problem_sha,
        evidence_level="E1" if rec.get("inference")=="PASS" else "E0",
        confidence=0.55 if rec.get("inference")=="PASS" else 0.0,risk=0.5,
        dependencies=["model:"+model_id,"revision:"+rev,rec["spiralix_input_sha256"]],
        json_payload=rec.get("parsed") or {"raw":rec.get("raw_output","")}
    )
    rec["spiralix_output_envelope"]=out_env
    rec["spiralix_output_sha256"]=sha256_obj(out_env)
    rec["lineage_fingerprint"]=hashlib.sha256((model_id+"|"+rev).encode()).hexdigest()
    rec["independent_evidence"]=False
    rec["receipt_sha256"]=hashlib.sha256(
      json.dumps({k:v for k,v in rec.items() if k!="receipt_sha256"},
                 sort_keys=True,default=str).encode()
    ).hexdigest()
    p=Path(out_root)/ai_id/"receipt.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(rec,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({
      "ai":ai_id,"inference":rec.get("inference"),
      "parse_ok":rec.get("parse_ok"),"latency_s":rec["latency_s"]
    },sort_keys=True),flush=True)
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ais",required=True,help="Comma-separated AI IDs")
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output-root",required=True)
    a=ap.parse_args()
    ais=[x.strip() for x in a.ais.split(",") if x.strip()]
    if not ais:
        raise SystemExit("NO_AI_IDS")
    cfg=json.loads((ROOT/"config/all-ai-strategy-council-v1.json").read_text())
    reg=json.loads((ROOT/cfg["registry"]).read_text())
    model_id=cfg["model"]["id"]; rev=cfg["model"]["revision"]

    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    tok=AutoTokenizer.from_pretrained(model_id,revision=rev)
    dtype=torch.bfloat16 if "Qwen3" in model_id else torch.float32
    model=AutoModelForCausalLM.from_pretrained(
      model_id,revision=rev,torch_dtype=dtype,low_cpu_mem_usage=True
    )
    model.eval()

    rows=[]
    for ai_id in ais:
        rows.append(run_one(ai_id,a.run_id,a.output_root,cfg,reg,tok,model,torch))
    summary={
      "schema":"CEREBRON_COUNCIL_BATCH_SHARD_V1",
      "run_id":a.run_id,
      "requested":ais,
      "receipt_count":len(rows),
      "inference_pass_count":sum(r.get("inference")=="PASS" for r in rows),
      "parse_pass_count":sum(bool(r.get("parse_ok")) for r in rows),
      "model_id":model_id,"revision":rev,
      "unique_lineage_fingerprints":len({r.get("lineage_fingerprint") for r in rows}),
      "independent_evidence_count":0
    }
    q=Path(a.output_root)/"_shard_summary.json"
    q.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,sort_keys=True),flush=True)
    if summary["inference_pass_count"] != len(ais):
        raise SystemExit(2)

if __name__=="__main__":
    main()
