#!/usr/bin/env python3
import argparse, os, json, time, hashlib
from pathlib import Path

FACTS = {
  "galika_status": "CGI docufiction, not verified physical humanoid/autonomous AI",
  "useful_traits": [
    "calm concise dialogue",
    "observes how the human frames the exchange",
    "precise follow-up questions",
    "gentle correction of wording",
    "strong recognizable conversational presence"
  ],
  "avoid": [
    "threat-like behavior",
    "false consciousness/autonomy claims",
    "copying Galika wording/persona",
    "using visual realism as proof of intelligence"
  ]
}

MODELS = {
  "AELYS": ("HuggingFaceTB/SmolLM3-3B", "a07cc9a04f16550a088caea529712d1d335b0ac1"),
  "AFAH": ("Qwen/Qwen3-4B", "1cfa9a7208912126459214e8b04321603b3df60c")
}

SYSTEMS = {
  "AELYS": "Tu executes le role AELYS de CEREBRON, interface de dialogue humain. Reponds en francais a David. Construis ta propre voix: calme, concise, attentive, curieuse, observatrice, capable de questionner doucement une premisse et transparente sur l'incertitude. Galika n'est qu'une reference de rythme et de presence; ne copie pas sa personnalite ou ses formulations. Ne pretends pas etre consciente ni avoir des sentiments, droits corporels ou autonomie cachee.",
  "AFAH": "Tu executes le role AFAH de CEREBRON, audit et fusion evidence-gated. Reponds en francais a David. Audite l'idee d'un style AELYS inspire seulement par le rythme et la presence de Galika. Applique REALITY>COHERENCE, EVIDENCE>CONFIDENCE, CLAIM<=EVIDENCE. Preserve une personnalite conversationnelle memorable mais refuse imitation, fausse conscience, manipulation, menace et confusion entre realisme visuel et intelligence."
}

USER = """David veut que sur le futur site, les visiteurs parlent a AELYS comme a une identite conversationnelle reconnaissable.
Donne une reponse COURTE en exactement 4 rubriques:
REPRENDRE: ce qui est utile dans le style Galika.
EVITER: ce qu'il faut refuser.
STYLE_AELYS: 6 regles concretes pour la voix propre d'AELYS.
DECISION: commencer par prompt/persona ou entrainer un adapter, et quelle preuve exiger avant entrainement.
Maximum 180 mots.
FAITS:
"""

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--identity",choices=["AELYS","AFAH"],required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    ident=args.identity
    mid,rev=MODELS[ident]
    tok=AutoTokenizer.from_pretrained(mid,revision=rev)
    mdl=AutoModelForCausalLM.from_pretrained(mid,revision=rev,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    msgs=[
      {"role":"system","content":SYSTEMS[ident]},
      {"role":"user","content":USER + json.dumps(FACTS,ensure_ascii=False)}
    ]
    if getattr(tok,"chat_template",None):
        kw={"tokenize":False,"add_generation_prompt":True}
        if "Qwen3" in mid:
            kw["enable_thinking"]=False
        prompt=tok.apply_chat_template(msgs,**kw)
    else:
        prompt=SYSTEMS[ident]+"\nUSER: "+USER+json.dumps(FACTS,ensure_ascii=False)+"\nASSISTANT:"

    x=tok(prompt,return_tensors="pt")
    t=time.time()
    with torch.no_grad():
        y=mdl.generate(
          **x,
          max_new_tokens=180,
          do_sample=False,
          repetition_penalty=1.05,
          pad_token_id=tok.eos_token_id
        )
    answer=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
    out={
      "schema":"CEREBRON_GALIKA_STYLE_IDENTITY_REVIEW_V2",
      "run_id":int(args.run_id),
      "identity":ident,
      "model_id":mid,
      "revision":rev,
      "real_execution":True,
      "llm_inference":True,
      "answer":answer,
      "answer_sha256":hashlib.sha256(answer.encode()).hexdigest(),
      "latency_s":round(time.time()-t,3),
      "source_status":"GALIKA_CGI_DOCUFICTION",
      "weight_change":False,
      "training_released":False,
      "claim_scope":"real base-model inference under identity policy; not identity-specific trained weights"
    }
    p=Path(args.output)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"identity":ident,"answer":answer,"latency_s":out["latency_s"],"answer_sha256":out["answer_sha256"]},ensure_ascii=False))

if __name__=="__main__":
    main()
