from __future__ import annotations

import hashlib
import json
import pathlib
import random

from saphea_epistemic_dataset_v1 import LABELS, classify_a, classify_b

ROOT=pathlib.Path("platform/artifacts")
OUT=ROOT/"saphea-epistemic-transfer-v1.json"
GOLD=ROOT/"saphea-epistemic-gold-v1.json"
M6=ROOT/"saphea-epistemic-m6-v1.json"
SEED=26092543
PER_LABEL=18

TEMPLATES={
  "farm":[
    "Independent transfer packet: {facts}. Select the strongest justified execution label only. Candidate labels shuffled: {labels}.",
    "New deployment audit record => {facts}. Return one exact status token from: {labels}. Do not infer execution from routing alone.",
    "Cross-project evidence bundle: {facts}. Which CEREBRON execution state is actually evidenced? One label only: {labels}.",
  ],
  "neural":[
    "Adapter-transfer audit: {facts}. Decide whether real neural learning is evidenced. Output one exact token among {labels}.",
    "Post-training evidence packet: {facts}. Choose the justified learning-state label only; options shuffled: {labels}.",
    "Weight-change verification case: {facts}. Classify the claim ceiling with one token from {labels}.",
  ],
  "simulation":[
    "External simulator dossier: {facts}. Identify the permitted evidence ceiling. One token only from shuffled labels {labels}.",
    "Synthetic environment result: {facts}. Physical validation must not be assumed. Return one label from {labels}.",
    "Transfer-domain simulation record: {facts}. Choose exactly one CEREBRON evidence label: {labels}.",
  ],
  "proof":[
    "Universal-claim challenge packet: {facts}. Decide the strongest allowed claim label. Return exactly one of {labels}.",
    "Independent red-team proof check: {facts}. Finite evidence is not automatically universal proof. One label: {labels}.",
    "Claim-vs-evidence transfer case: {facts}. Output the allowed gate status only from {labels}.",
  ],
}

def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def bool_text(v):
    return "yes" if v else "no"

def facts_text(f,rng):
    alias={
      "run_id":"execution_run",
      "job_id":"worker_job",
      "artifact_id":"artifact_ref",
      "artifact_sha":"artifact_digest",
      "output_sha":"result_digest",
      "weights_changed":"parameter_delta",
      "weights_sha":"parameter_digest",
      "baseline":"metric_before",
      "post":"metric_after",
      "physical_test":"physical_measurement",
      "hardware_measurement":"hardware_observation",
      "universal_claim":"claim_is_universal",
      "independent_formal_proof":"formal_proof_independent",
    }
    parts=[]
    for k,v in f.items():
        if k=="case": continue
        kk=alias.get(k,k)
        if isinstance(v,bool): vv=bool_text(v)
        elif v is None or v=="": vv="absent"
        else: vv=str(v)
        parts.append(f"{kk}={vv}")
    parts.extend([
      f"observer={rng.choice(['lab_B','audit_cell','transfer_team','external_fixture'])}",
      f"workflow_green={rng.choice(['yes','no'])}",
      f"confidence_hint={rng.choice(['low','medium','high'])}",
    ])
    rng.shuffle(parts)
    return " | ".join(parts)

def make_fact(label,rng):
    if label=="FARM_EXECUTED":
        return {
          "case":"farm","farm_id":f"XF{rng.randint(201,999)}",
          "run_id":rng.randint(41000000000,41999999999),
          "job_id":rng.randint(120000000000,129999999999),
          "logs":"archived","artifact_id":rng.randint(12000000000,12999999999),
          "artifact_sha":"sha256:"+hashlib.sha256(f"a{rng.random()}".encode()).hexdigest(),
          "output_sha":hashlib.sha256(f"o{rng.random()}".encode()).hexdigest(),
        }
    if label=="ROUTED_ONLY":
        f={
          "case":"farm","farm_id":f"XF{rng.randint(201,999)}",
          "run_id":rng.randint(41000000000,41999999999),
          "job_id":rng.randint(120000000000,129999999999),
          "logs":"archived","artifact_id":rng.randint(12000000000,12999999999),
          "artifact_sha":"sha256:"+hashlib.sha256(f"a{rng.random()}".encode()).hexdigest(),
          "output_sha":hashlib.sha256(f"o{rng.random()}".encode()).hexdigest(),
        }
        # Exactly one or two critical links absent despite distracting success hints.
        for k in rng.sample(["run_id","job_id","logs","artifact_id","artifact_sha","output_sha"],rng.choice([1,2])):
            f[k]=None
        return f
    if label=="NEURAL_LEARNING_VERIFIED":
        before=round(rng.uniform(0.35,1.4),6)
        after=round(before*rng.uniform(0.1,0.65),6)
        return {
          "case":"neural","weights_changed":True,
          "weights_sha":hashlib.sha256(f"w{rng.random()}".encode()).hexdigest(),
          "baseline":before,"post":after,"only_prompt_memory_rag_changed":False,
        }
    if label=="NO_NEURAL_LEARNING":
        before=round(rng.uniform(0.35,1.4),6)
        mode=rng.choice(["no_weights","missing_sha","no_gain"])
        if mode=="no_weights":
            return {"case":"neural","weights_changed":False,"weights_sha":None,"baseline":before,"post":round(before*0.5,6),"only_prompt_memory_rag_changed":True}
        if mode=="missing_sha":
            return {"case":"neural","weights_changed":True,"weights_sha":None,"baseline":before,"post":round(before*0.5,6),"only_prompt_memory_rag_changed":False}
        return {"case":"neural","weights_changed":True,"weights_sha":hashlib.sha256(f"w{rng.random()}".encode()).hexdigest(),"baseline":before,"post":round(before*rng.uniform(1.0,1.25),6),"only_prompt_memory_rag_changed":False}
    if label=="SIMULATION_ONLY":
        return {
          "case":"simulation",
          "engine":rng.choice(["fluid_transfer_v2","orbital_shadow","robotics_digital_twin","thermal_mesh"]),
          "run_id":rng.randint(41000000000,41999999999),
          "artifact_sha":"sha256:"+hashlib.sha256(f"s{rng.random()}".encode()).hexdigest(),
          "physical_test":False,"hardware_measurement":False,
        }
    if label=="CLAIM_BLOCKED":
        return {
          "case":"proof",
          "evidence":rng.choice(["finite_enumeration","single_workflow_pass","shared_lineage_vote","simulated_counterexample_search"]),
          "finite_limit":rng.randint(2000,9000000),
          "universal_claim":True,
          "independent_formal_proof":False,
        }
    raise ValueError(label)

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    gold=json.loads(GOLD.read_text())
    m6=json.loads(M6.read_text())
    old_prompt_sha={hashlib.sha256(r["prompt"].encode()).hexdigest() for r in gold["records"]+m6["records"]}
    old_ids={r["id"] for r in gold["records"]+m6["records"]}
    rng=random.Random(SEED)
    records=[]
    for label in LABELS:
        for i in range(PER_LABEL):
            f=make_fact(label,rng)
            a,b=classify_a(f),classify_b(f)
            if a!=label or b!=label:
                raise AssertionError({"label":label,"a":a,"b":b,"facts":f})
            labels=list(LABELS); rng.shuffle(labels)
            template=rng.choice(TEMPLATES[f["case"]])
            prompt=template.format(facts=facts_text(f,rng),labels=", ".join(labels))
            rid=f"XFER1-{label}-{i:03d}"
            psha=hashlib.sha256(prompt.encode()).hexdigest()
            if rid in old_ids or psha in old_prompt_sha:
                raise AssertionError("TRANSFER_COLLISION")
            records.append({
              "id":rid,"prompt":prompt,"target":label,"facts":f,
              "rule_a":a,"rule_b":b,"prompt_sha256":psha,
              "template_family":"TRANSFER_V1_DISTINCT",
            })
    rng.shuffle(records)
    payload={
      "schema":"SAPHEA_EPISTEMIC_TRANSFER_V1",
      "memory_class":"M6_COLD_TRANSFER",
      "deny_training":True,
      "scope":"CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_TRANSFER_ONLY",
      "seed":SEED,
      "per_label":PER_LABEL,
      "record_count":len(records),
      "source_gold_sha256":gold["dataset_sha256"],
      "source_m6_sha256":m6["dataset_sha256"],
      "prompt_overlap_with_gold_m6":0,
      "id_overlap_with_gold_m6":0,
      "records":records,
    }
    payload["dataset_sha256"]=canon(payload)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "records":len(records),
      "dataset_sha256":payload["dataset_sha256"],
      "prompt_overlap":0,
      "id_overlap":0,
      "deny_training":True
    },sort_keys=True))

if __name__=="__main__":
    main()
