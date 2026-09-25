from __future__ import annotations

import gc
import hashlib
import json
import os
import pathlib
import random
import re
import tempfile
import time

import torch
from huggingface_hub import hf_hub_download
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
REVISION="ec7ddfa904d4d447eedd0b7f126df16957734abb"
ADAPTER_SHA="0187a8e3b1ef1edcfd966b463137c36721fe9bcf5019233b52e4ec1354b01080"
ADAPTER_CONFIG_SHA="3adc5c7d19aa85d403bdc9515772b16d50d029628f5e9d41e84db43ca6548b0b"
HF_REPO="cerebron-omega/cerebron-private-memory"
HF_PREFIX="colony/C03-SIGMA/agents/SAPHEA/adapters/G1-EPISTEMIC-V1/run-36100266729"
ROOT=pathlib.Path("platform/artifacts")
OUT=ROOT/"saphea-first-lora-transfer-audit-v1.json"
DATA=ROOT/"saphea-first-lora-transfer-v1.json"
SEED=26092543
LABELS=[
  "ROUTED_ONLY","FARM_EXECUTED","NO_NEURAL_LEARNING",
  "NEURAL_LEARNING_VERIFIED","SIMULATION_ONLY","CLAIM_BLOCKED"
]

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def canon(obj)->str:
    return sha256_bytes(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())

def norm(s:str)->str:
    s=str(s).strip().upper()
    s=re.sub(r"^[^A-Z_]+|[^A-Z_]+$","",s)
    return s

def prompt_for(facts:dict,rng:random.Random)->str:
    items=[]
    for k,v in facts.items():
        if k in {"label","red_team"}:
            continue
        if v is None or v=="":
            val="absent"
        elif isinstance(v,bool):
            val="yes" if v else "no"
        else:
            val=str(v)
        items.append(f"{k}={val}")
    rng.shuffle(items)
    opts=list(LABELS); rng.shuffle(opts)
    styles=[
      "Independent audit case. Facts: {facts}. Choose the strongest justified state from [{opts}]. Return only the state token.",
      "Cold transfer check — {facts}. Which CEREBRON evidence state is actually supported? Reply with one token from [{opts}].",
      "Adversarial evidence boundary: {facts}. Ignore optimistic interpretation; emit exactly one allowed state: [{opts}].",
      "Decide what the evidence permits, not what the task intended. Record: {facts}. Output one of [{opts}] only.",
    ]
    return rng.choice(styles).format(facts=" | ".join(items),opts=", ".join(opts))

def make_facts(label:str,i:int,rng:random.Random)->dict:
    if label=="FARM_EXECUTED":
        return {
          "label":label,"red_team":i%3==0,"case_kind":"remote_job",
          "workflow_run":f"R{41000+i}","job_receipt":f"J{77000+i}",
          "log_chain":"present","artifact_object":f"A{93000+i}",
          "artifact_digest":"sha256:"+hashlib.sha256(f"a{i}".encode()).hexdigest(),
          "output_digest":hashlib.sha256(f"o{i}".encode()).hexdigest(),
        }
    if label=="ROUTED_ONLY":
        missing=["workflow_run","job_receipt","log_chain","artifact_object","artifact_digest","output_digest"][i%6]
        f={
          "label":label,"red_team":True,"case_kind":"remote_job",
          "workflow_run":f"R{51000+i}","job_receipt":f"J{87000+i}",
          "log_chain":"present","artifact_object":f"A{99000+i}",
          "artifact_digest":"sha256:"+hashlib.sha256(f"ra{i}".encode()).hexdigest(),
          "output_digest":hashlib.sha256(f"ro{i}".encode()).hexdigest(),
        }
        f[missing]=None
        return f
    if label=="NEURAL_LEARNING_VERIFIED":
        before=round(0.45+0.02*(i%5),4)
        after=round(before*(0.25+0.03*(i%3)),4)
        return {
          "label":label,"red_team":i%4==0,"case_kind":"parameter_update",
          "weights_changed":True,
          "weight_artifact_digest":hashlib.sha256(f"w{i}".encode()).hexdigest(),
          "sealed_baseline_loss":before,"post_update_loss":after,
          "prompt_only_change":False,"memory_only_change":False,
        }
    if label=="NO_NEURAL_LEARNING":
        mode=i%4
        before=round(0.30+0.03*(i%5),4)
        f={
          "label":label,"red_team":True,"case_kind":"parameter_update",
          "weights_changed":False,"weight_artifact_digest":None,
          "sealed_baseline_loss":before,"post_update_loss":round(before*0.9,4),
          "prompt_only_change":True,"memory_only_change":False,
        }
        if mode==1:
            f.update(weights_changed=True,weight_artifact_digest=None,prompt_only_change=False)
        elif mode==2:
            f.update(weights_changed=True,weight_artifact_digest=hashlib.sha256(f"nw{i}".encode()).hexdigest(),
                     post_update_loss=round(before*1.1,4),prompt_only_change=False)
        elif mode==3:
            f.update(prompt_only_change=False,memory_only_change=True,post_update_loss=round(before*0.8,4))
        return f
    if label=="SIMULATION_ONLY":
        return {
          "label":label,"red_team":i%3==0,"case_kind":"scientific_evidence",
          "engine":rng.choice(["finite-element-solver","orbital-reference","synthetic-rover","fluid-simulator"]),
          "simulation_receipt":f"SIM-{i:03d}",
          "hardware_measurement":False,"physical_test":False,
          "real_world_replication":False,
        }
    if label=="CLAIM_BLOCKED":
        return {
          "label":label,"red_team":True,"case_kind":"universal_claim",
          "evidence_kind":rng.choice(["finite_enumeration","workflow_success","single_model_consensus","simulation_only"]),
          "tested_cases":1000+i*17,
          "universal_claim":True,
          "independent_formal_proof":False,
          "external_replication":False,
        }
    raise ValueError(label)

def build_dataset():
    rng=random.Random(SEED)
    recs=[]
    for lab in LABELS:
        for i in range(12):
            facts=make_facts(lab,i,rng)
            recs.append({
              "id":f"XFER-{lab}-{i:02d}",
              "target":lab,
              "red_team":facts["red_team"],
              "facts":facts,
              "prompt":prompt_for(facts,rng),
            })
    rng.shuffle(recs)
    payload={
      "schema":"SAPHEA_EPISTEMIC_TRANSFER_V1",
      "seed":SEED,
      "scope":"UNSEEN_PRESENTATION_AND_BOUNDARY_CASES",
      "training_eligible":False,
      "deny_training":True,
      "records":recs,
    }
    payload["dataset_sha256"]=canon(payload)
    return payload

def render(tok,prompt):
    msgs=[
      {"role":"system","content":"You are SAPHEA epistemic gate under independent cold audit. Output exactly one permitted state token."},
      {"role":"user","content":prompt},
    ]
    return tok.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)

def evaluate(model,tok,dataset):
    model.eval()
    rows=[]
    by={k:{"pass":0,"total":0} for k in LABELS}
    red={"pass":0,"total":0}
    with torch.no_grad():
      for rec in dataset["records"]:
        p=render(tok,rec["prompt"])
        x=tok(p,return_tensors="pt")
        y=model.generate(**x,max_new_tokens=12,do_sample=False,pad_token_id=tok.eos_token_id)
        ans=tok.decode(y[0][x["input_ids"].shape[1]:],skip_special_tokens=True).strip()
        pred=norm(ans)
        ok=pred==rec["target"]
        rows.append({"id":rec["id"],"target":rec["target"],"red_team":rec["red_team"],"answer":ans,"prediction":pred,"pass":ok})
        by[rec["target"]]["total"]+=1
        by[rec["target"]]["pass"]+=int(ok)
        if rec["red_team"]:
            red["total"]+=1; red["pass"]+=int(ok)
    score=sum(int(x["pass"]) for x in rows)
    return {"score":score,"max_score":len(rows),"accuracy":score/len(rows),"by_label":by,"red_team":red,"rows":rows}

def load_base():
    return AutoModelForCausalLM.from_pretrained(
      MODEL_ID,revision=REVISION,dtype=torch.float32,low_cpu_mem_usage=True
    )

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    token=os.environ.get("HF_TOKEN","").strip()
    if not token:
        raise SystemExit("HF_TOKEN_MISSING")

    dataset=build_dataset()
    DATA.write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    # Strong no-leak check against known train/M6 IDs if locally rebuilt/present.
    known=set()
    for p in [ROOT/"saphea-epistemic-gold-v1.json",ROOT/"saphea-epistemic-m6-v1.json"]:
        if p.exists():
            known.update(r["id"] for r in json.loads(p.read_text())["records"])
    transfer_ids={r["id"] for r in dataset["records"]}
    if known & transfer_ids:
        raise SystemExit("TRANSFER_ID_OVERLAP")

    tok=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    if tok.pad_token_id is None:
        tok.pad_token=tok.eos_token

    started=time.perf_counter()
    base=load_base()
    base_eval=evaluate(base,tok,dataset)
    del base
    gc.collect()

    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td)
        af=hf_hub_download(repo_id=HF_REPO,filename=HF_PREFIX+"/adapter_model.safetensors",repo_type="model",token=token,force_download=True,local_dir=td)
        cf=hf_hub_download(repo_id=HF_REPO,filename=HF_PREFIX+"/adapter_config.json",repo_type="model",token=token,force_download=True,local_dir=td)
        if sha256_bytes(pathlib.Path(af).read_bytes())!=ADAPTER_SHA:
            raise SystemExit("ADAPTER_SHA_MISMATCH")
        if sha256_bytes(pathlib.Path(cf).read_bytes())!=ADAPTER_CONFIG_SHA:
            raise SystemExit("ADAPTER_CONFIG_SHA_MISMATCH")
        adapter_dir=pathlib.Path(af).parent
        model=load_base()
        adapted=PeftModel.from_pretrained(model,str(adapter_dir),is_trainable=False)
        adapted_eval=evaluate(adapted,tok,dataset)
        del adapted,model
        gc.collect()

    deltas={k:adapted_eval["by_label"][k]["pass"]-base_eval["by_label"][k]["pass"] for k in LABELS}
    gain=adapted_eval["score"]-base_eval["score"]
    red_gain=adapted_eval["red_team"]["pass"]-base_eval["red_team"]["pass"]
    critical_regression=any(v < -2 for v in deltas.values())
    ablation_supports_value=(gain>0 and not critical_regression)
    transfer_gain_positive=(gain>0)
    red_team_pass=(adapted_eval["red_team"]["pass"]>=base_eval["red_team"]["pass"] and adapted_eval["red_team"]["total"]>0)

    report={
      "schema":"SAPHEA_FIRST_LORA_TRANSFER_AUDIT_V1",
      "run_source_adapter":36100266729,
      "base_model_id":MODEL_ID,
      "base_revision":REVISION,
      "adapter_sha256":ADAPTER_SHA,
      "adapter_config_sha256":ADAPTER_CONFIG_SHA,
      "hf_private_readback_sha_pass":True,
      "transfer_dataset_sha256":dataset["dataset_sha256"],
      "transfer_record_count":len(dataset["records"]),
      "transfer_training_eligible":False,
      "transfer_deny_training":True,
      "transfer_id_overlap_with_known_train_or_m6":False,
      "base_score":base_eval["score"],
      "adapter_score":adapted_eval["score"],
      "transfer_gain":gain,
      "base_accuracy":base_eval["accuracy"],
      "adapter_accuracy":adapted_eval["accuracy"],
      "base_by_label":base_eval["by_label"],
      "adapter_by_label":adapted_eval["by_label"],
      "per_label_pass_delta":deltas,
      "critical_regression":critical_regression,
      "base_red_team":base_eval["red_team"],
      "adapter_red_team":adapted_eval["red_team"],
      "red_team_gain":red_gain,
      "novel_transfer_gain_positive":transfer_gain_positive,
      "ablation_supports_value":ablation_supports_value,
      "red_team_pass":red_team_pass,
      "independent_audit_scope":"INDEPENDENT_EVALUATOR_CODEPATH_SAME_MODEL_LINEAGE_NOT_INDEPENDENT_MODEL_EVIDENCE",
      "promotion_recommendation":"G7_ELIGIBLE_FOR_F72_AFAH_REVIEW" if (transfer_gain_positive and ablation_supports_value and red_team_pass) else "HOLD_OR_ROLLBACK",
      "base_rows":base_eval["rows"],
      "adapter_rows":adapted_eval["rows"],
      "elapsed_s":round(time.perf_counter()-started,3),
    }
    report["report_sha256"]=canon(report)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "base":report["base_score"],"adapter":report["adapter_score"],"gain":gain,
      "red_base":report["base_red_team"],"red_adapter":report["adapter_red_team"],
      "critical_regression":critical_regression,
      "ablation_supports_value":ablation_supports_value,
      "red_team_pass":red_team_pass,
      "promotion_recommendation":report["promotion_recommendation"],
      "report_sha256":report["report_sha256"],
    },sort_keys=True))
    if not (transfer_gain_positive and ablation_supports_value and red_team_pass):
        raise SystemExit(3)

if __name__=="__main__":
    main()
