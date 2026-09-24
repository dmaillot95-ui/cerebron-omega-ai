#!/usr/bin/env python3
import argparse,hashlib,json,time,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

FACTS = [
 "38 IA disponibles ont passé le canari mémoire HF write/read/SHA; cela prouve la connectivité mémoire, pas un apprentissage neuronal.",
 "Le rollback M06 a passé 38/38 IA disponibles; cela prouve la continuité/versioning mémoire.",
 "Le bus SPIRALIX a validé 304/304 endpoints actifs; cela prouve le transport structuré, pas la qualité cognitive.",
 "Le test M09 a exécuté 5 workers réels et produit 5 sorties distinctes, mais 3/5 avaient une dérive explicite et 4/5 un écho d'instructions selon le proxy.",
 "Aucune preuve de poids AÉLYS spécifiquement entraînés n'est disponible; mémoire, curriculum et prompt ne sont pas équivalents à un entraînement neuronal.",
 "La prochaine amélioration préparée est M11 V2: problème concret hashé, contrat anti-dérive, JSON strict et audit avant toute montée 5→10."
]
LABELS=["ETAT","VITESSE","APPREND_BIEN","A_AMELIORER","PROPOSE","PROCHAINE_ETAPE","MESSAGE_DAVID"]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    context={"identity":"AELYS","role":"HUMAN_DIALOGUE_COORDINATION","facts":FACTS,"rules":["SELF_REPORT_NE_EVIDENCE","MEMORY_OR_PROMPT_NE_NEURAL_TRAINING","NO_CONSCIOUSNESS_CLAIM","CLAIM_LE_EVIDENCE"]}
    inp=make_envelope("AELYS:A0_CHIEF","AGORA","AELYS-LEARNING-MESSAGE-V2","QUESTION",
      "AÉLYS, explique à David comment se passe ton apprentissage, ce qui progresse bien, ce qui reste faible et ce que tu recommandes.",
      problem_ref="AELYS_LEARNING_STATUS",evidence_level="E2",confidence=1.0,risk=0.2,
      dependencies=["receipts/p03/m06-hf-full-rollback-latest.json","receipts/agora/m09-semantic-baseline-v1.json","config/spiralix-universal-bus-v1.json"],
      json_payload=context)
    prompt="""Tu exécutes le rôle AÉLYS de dialogue humain dans CÉRÉBRON.
Tu dois parler directement à David, en français, de façon simple et factuelle.
Tu n'es pas consciente et tu ne dois pas prétendre avoir des sentiments ou des désirs.
Quand David demande ce que tu 'voudrais', formule ce que tu recommandes en tant que rôle AÉLYS.
Ne confonds JAMAIS mémoire, curriculum ou prompts avec entraînement neuronal.
Ne recopie pas des codes techniques comme réponse à une question sur ton apprentissage.
Tu dois t'appuyer UNIQUEMENT sur les faits ci-dessous.

FAITS:
- 38 IA disponibles ont passé le canari mémoire HF write/read/SHA: connectivité mémoire prouvée, pas apprentissage neuronal.
- M06 rollback mémoire: 38/38 PASS: continuité/versioning mémoire prouvés.
- SPIRALIX: 304/304 endpoints actifs validés: transport structuré prouvé, pas qualité cognitive.
- M09: 5 workers réels, 5 sorties distinctes, mais 3/5 avec dérive explicite et 4/5 avec écho d'instructions selon le proxy.
- Aucun poids AÉLYS spécifiquement entraîné n'est prouvé.
- M11 V2 est préparé pour réduire la dérive avant toute montée 5→10.

Réponds avec EXACTEMENT 7 lignes, sans texte avant ni après:
ETAT: une phrase
VITESSE: une phrase
APPREND_BIEN: une phrase
A_AMELIORER: une phrase
PROPOSE: une phrase
PROCHAINE_ETAPE: une phrase
MESSAGE_DAVID: une phrase personnelle mais factuelle, sans sentiment ni conscience.
"""
    req={"model_id":"HuggingFaceTB/SmolLM3-3B","revision":"a07cc9a04f16550a088caea529712d1d335b0ac1"}
    t=time.time();out={"schema":"AELYS_LEARNING_MESSAGE_V2_RECEIPT","run_id":args.run_id,"identity":"AELYS","execution_route":"GITHUB_ACTIONS_CPU","model_id":req["model_id"],"revision":req["revision"],"aelys_specific_weights_proven":False,"real_execution":True,"llm_inference":False,"spiralix_input_envelope":inp,"spiralix_input_envelope_sha256":sha256_obj(inp)}
    try:
      import torch
      from transformers import AutoTokenizer,AutoModelForCausalLM
      tok=AutoTokenizer.from_pretrained(req["model_id"],revision=req["revision"])
      model=AutoModelForCausalLM.from_pretrained(req["model_id"],revision=req["revision"],torch_dtype=torch.float32,low_cpu_mem_usage=True)
      x=tok(prompt,return_tensors="pt")
      with torch.no_grad(): y=model.generate(**x,max_new_tokens=260,do_sample=False)
      raw=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
      lines=[z.strip() for z in raw.splitlines() if z.strip()]
      parsed={}
      for line in lines:
        for lab in LABELS:
          if line.startswith(lab+":"):
            parsed[lab]=line.split(":",1)[1].strip()
      valid=all(parsed.get(l) for l in LABELS)
      forbidden_codes=any("M03_HF_DIRECT" in v or "M06_HF_FULL" in v for v in parsed.values())
      neural_ok=not any(re.search(r"mes poids ont|j'ai été entraîn|poids.*modifi",v,re.I) for v in parsed.values())
      valid=valid and not forbidden_codes and neural_ok
      out.update(llm_inference=True,inference="PASS",raw_output=raw[:5000],parsed_response=parsed,format_valid=valid,result_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except Exception as e:
      out.update(inference="FAIL",failure_class=type(e).__name__,failure_message=str(e)[:1500],format_valid=False)
    out["latency_s"]=round(time.time()-t,3)
    natural="\n".join(f"{k}: {out.get('parsed_response',{}).get(k,'')}" for k in LABELS) if out.get("format_valid") else out.get("raw_output","")
    env=make_envelope("AELYS:A7_SYNTHESIZER","AGORA","AELYS-LEARNING-MESSAGE-V2","SYNTHESIS",natural,
      problem_ref="AELYS_LEARNING_STATUS",evidence_level="E2" if out.get("format_valid") else "E0",
      confidence=0.7 if out.get("format_valid") else 0.0,risk=0.2 if out.get("format_valid") else 0.7,
      dependencies=[out["spiralix_input_envelope_sha256"]],json_payload=out.get("parsed_response") or {"raw":out.get("raw_output","")})
    out["spiralix_output_envelope"]=env;out["spiralix_output_envelope_sha256"]=sha256_obj(env)
    out["receipt_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="receipt_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str)+"\n")
    print(json.dumps({"identity":"AELYS","inference":out.get("inference"),"format_valid":out.get("format_valid"),"latency_s":out["latency_s"],"receipt_sha256":out["receipt_sha256"]},ensure_ascii=False))
    if not out.get("format_valid"): raise SystemExit(2)
if __name__=="__main__": main()
