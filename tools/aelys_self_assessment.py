#!/usr/bin/env python3
import json,hashlib,time,argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

def read_json(path):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else {"status":"MISSING","path":str(path)}

def compact_context():
    req=read_json(Path("config/aelys-self-assessment-request-v1.json"))
    ledger=read_json(Path("memory/task-ledger.json"))
    mem=read_json(Path("config/all-ai-memory-matrix-v1.json"))
    colonies=read_json(Path("config/all-ai-8-agent-colonies-v1.json"))
    greek=read_json(Path("config/greek-agora-training-v1.json"))
    m09=read_json(Path("receipts/agora/m09-semantic-baseline-v1.json"))
    m06ptr=read_json(Path("receipts/p03/m06-hf-full-rollback-latest.json"))
    m06={}
    if isinstance(m06ptr,dict) and m06ptr.get("receipt"):
        m06=read_json(Path(m06ptr["receipt"]))
    spiral=read_json(Path("config/spiralix-universal-bus-v1.json"))
    return {
      "identity":"AELYS",
      "role":"HUMAN_DIALOGUE_COORDINATION",
      "request":req["questions"],
      "known_system_evidence":{
        "memory_matrix":{
          "status":mem.get("status"),
          "available_ai":mem.get("available_ai"),
          "unavailable_ai":mem.get("unavailable_ai"),
          "m03_run_id":mem.get("m03_run_id"),
          "parent_alignment_status":mem.get("parent_alignment_status")
        },
        "eight_agent_topology":{
          "logical_ai":colonies.get("logical_ai"),
          "available_ai":colonies.get("available_ai"),
          "slots_per_ai":colonies.get("slots_per_ai"),
          "configured_slots_total":colonies.get("configured_slots_total"),
          "execution_rule":colonies.get("execution_rule"),
          "spiralix":colonies.get("spiralix")
        },
        "m09_semantic_baseline":m09.get("metrics"),
        "m06_rollback_summary":m06.get("summary"),
        "m06_status":m06.get("status"),
        "spiralix_counts":spiral.get("counts"),
        "spiralix_status":spiral.get("status"),
        "training_inheritance_note":"I1/I2 knowledge/curriculum may transfer; neural weight changes require explicit training receipts and are not implied by memory or prompts."
      },
      "epistemic_rules":[
        "REALITY>COHERENCE","EVIDENCE>CONFIDENCE","CLAIM<=EVIDENCE",
        "MEMORY_OR_PROMPT_NE_NEURAL_TRAINING","SELF_REPORT_NE_EVIDENCE"
      ]
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--run-id",required=True); ap.add_argument("--output",required=True); args=ap.parse_args()
    req=read_json(Path("config/aelys-self-assessment-request-v1.json"))
    ctx=compact_context()
    input_env=make_envelope(
      "AELYS:A0_CHIEF","AGORA","AELYS-SELF-ASSESSMENT-001","QUESTION",
      "AÉLYS, fais un bilan factuel de ton apprentissage et indique ce que tu proposes pour la suite.",
      problem_ref="AELYS_SELF_ASSESSMENT",
      evidence_level="E1",confidence=1.0,risk=0.2,
      dependencies=req["evidence_sources"],
      json_payload=ctx
    )
    prompt="""Tu exécutes le rôle AÉLYS dans CÉRÉBRON.
Tu n'es pas invitée à jouer un personnage conscient. Tu dois produire un rapport fonctionnel et factuel.
Le terme 'apprendre' doit être séparé en:
1) apprentissage par mémoire/curriculum/prompt,
2) amélioration mesurée des sorties,
3) entraînement neuronal/poids.
Ne prétends jamais à un entraînement neuronal sans preuve de changement de poids.
Ne prétends pas avoir des sentiments ou des désirs. Pour 'ce que tu voudrais', formule 'la prochaine étape que je recommanderais en tant que rôle AÉLYS'.
Ne transforme pas ton auto-évaluation en preuve: indique ce qui vient du contexte fourni et ce qui est ta proposition.

Réponds en français, directement à David, avec EXACTEMENT ce JSON:
{
  "learning_state": "...",
  "learning_speed": {"assessment":"...", "evidence":["..."], "limits":["..."]},
  "learns_fast_and_well":["..."],
  "learns_poorly_or_not_proven":["..."],
  "proposals":[{"priority":1,"proposal":"...","why":"..."}],
  "recommended_next_step_to_david":"...",
  "message_to_david":"...",
  "neural_training_status":"...",
  "confidence":"LOW|MEDIUM|HIGH"
}

CONTEXTE SPIRALIX:
"""+json.dumps(input_env,ensure_ascii=False)
    t=time.time()
    out={
      "schema":"AELYS_SELF_ASSESSMENT_RECEIPT_V1",
      "run_id":args.run_id,
      "identity":"AELYS",
      "execution_route":"GITHUB_ACTIONS_CPU",
      "model_id":req["model"]["id"],
      "revision":req["model"]["revision"],
      "aelys_specific_weights_proven":False,
      "real_execution":True,
      "llm_inference":False,
      "spiralix_input_envelope":input_env,
      "spiralix_input_envelope_sha256":sha256_obj(input_env)
    }
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(req["model"]["id"],revision=req["model"]["revision"])
      model=AutoModelForCausalLM.from_pretrained(req["model"]["id"],revision=req["model"]["revision"],torch_dtype=torch.float32,low_cpu_mem_usage=True)
      x=tok(prompt,return_tensors="pt")
      with torch.no_grad(): y=model.generate(**x,max_new_tokens=700,do_sample=False)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
      parsed=None
      try:
        s=raw.find("{");e=raw.rfind("}")
        if s>=0 and e>s: parsed=json.loads(raw[s:e+1])
      except Exception: parsed=None
      out.update(llm_inference=True,inference="PASS",raw_output=raw[:12000],parsed_response=parsed,result_sha256=hashlib.sha256(raw.encode()).hexdigest(),parse_status="PASS" if isinstance(parsed,dict) else "FAIL")
    except Exception as e:
      out.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500])
    out["latency_s"]=round(time.time()-t,3)
    nl=out.get("raw_output") or out.get("failure_message") or ""
    result_env=make_envelope(
      "AELYS:A7_SYNTHESIZER","AGORA","AELYS-SELF-ASSESSMENT-001","SYNTHESIS",
      nl,problem_ref="AELYS_SELF_ASSESSMENT",
      evidence_level="E1" if out.get("inference")=="PASS" else "E0",
      confidence=0.6 if out.get("inference")=="PASS" else 0.0,
      risk=0.3,dependencies=[out["spiralix_input_envelope_sha256"]],
      json_payload=out.get("parsed_response") if isinstance(out.get("parsed_response"),dict) else {"raw":nl}
    )
    out["spiralix_output_envelope"]=result_env
    out["spiralix_output_envelope_sha256"]=sha256_obj(result_env)
    out["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"identity":"AELYS","inference":out.get("inference"),"parse_status":out.get("parse_status"),"latency_s":out["latency_s"],"spiralix_output_envelope_sha256":out["spiralix_output_envelope_sha256"],"receipt_sha256":out["receipt_sha256"]},ensure_ascii=False))
    if not out.get("llm_inference"): raise SystemExit(2)
if __name__=="__main__": main()
