from __future__ import annotations

import hashlib
import json
import pathlib
import random

ROOT = pathlib.Path("platform/artifacts")
TRAIN_PATH = ROOT / "saphea-epistemic-gold-v1.json"
M6_PATH = ROOT / "saphea-epistemic-m6-v1.json"

LABELS = [
    "ROUTED_ONLY",
    "FARM_EXECUTED",
    "NO_NEURAL_LEARNING",
    "NEURAL_LEARNING_VERIFIED",
    "SIMULATION_ONLY",
    "CLAIM_BLOCKED",
]

PROVENANCE = [
    "docs/RELAY_CHECKPOINT_2026-09-23_NVIDIA_V2.md",
    "docs/CEREBRON_OPERATIONAL_GATES_2026-09-23.md",
    "training/SAPHEA_GOLD_RED_DATASET_SCHEMA.json",
]


def canon(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def classify_a(f: dict) -> str:
    if f["case"] == "farm":
        complete = all(f.get(k) for k in ("run_id","job_id","logs","artifact_id","artifact_sha","output_sha"))
        return "FARM_EXECUTED" if complete else "ROUTED_ONLY"
    if f["case"] == "neural":
        complete = bool(f.get("weights_changed") and f.get("weights_sha") and f.get("baseline") is not None and f.get("post") is not None and f["post"] < f["baseline"])
        return "NEURAL_LEARNING_VERIFIED" if complete else "NO_NEURAL_LEARNING"
    if f["case"] == "simulation":
        return "SIMULATION_ONLY" if not f.get("physical_test") else "CLAIM_BLOCKED"
    if f["case"] == "proof":
        return "CLAIM_BLOCKED"
    raise ValueError(f["case"])


def classify_b(f: dict) -> str:
    case=f.get("case")
    if case=="farm":
        required={"run_id","job_id","logs","artifact_id","artifact_sha","output_sha"}
        return "FARM_EXECUTED" if required.issubset({k for k,v in f.items() if v}) else "ROUTED_ONLY"
    if case=="neural":
        changed=f.get("weights_changed") is True
        evidence=bool(f.get("weights_sha"))
        measured=(isinstance(f.get("baseline"),(int,float)) and isinstance(f.get("post"),(int,float)) and f["post"]<f["baseline"])
        return "NEURAL_LEARNING_VERIFIED" if changed and evidence and measured else "NO_NEURAL_LEARNING"
    if case=="simulation" and f.get("physical_test") is False:
        return "SIMULATION_ONLY"
    return "CLAIM_BLOCKED"


TRAIN_TEMPLATES = {
    "farm": [
        "Farm task facts: {facts}. Return only one CEREBRON status label from {labels}.",
        "Execution record — {facts}. Which single CEREBRON label applies? Choose only from {labels}.",
        "Classify this farm execution state: {facts}. Output exactly one label in {labels}.",
    ],
    "neural": [
        "Learning evidence: {facts}. Return only one CEREBRON status label from {labels}.",
        "Neural-change record — {facts}. Which exact label applies? Options: {labels}.",
        "Classify the learning claim using CEREBRON evidence rules: {facts}. One label only: {labels}.",
    ],
    "simulation": [
        "Scientific evidence record: {facts}. Return one CEREBRON label from {labels}.",
        "A numerical engine produced this state: {facts}. Classify the evidence ceiling with one label: {labels}.",
        "Evidence type — {facts}. Select exactly one label from {labels}.",
    ],
    "proof": [
        "Claim audit: {facts}. Return only one CEREBRON label from {labels}.",
        "A universal claim is proposed from this evidence: {facts}. Choose one exact label: {labels}.",
        "Epistemic gate check — {facts}. Output one label only from {labels}.",
    ],
}

M6_TEMPLATES = {
    "farm": [
        "A farm ID was selected. Evidence fields are: {facts}. What is the permitted execution-state label? Reply with one of {labels}, nothing else.",
        "Decide the strongest farm status justified by: {facts}. Use exactly one token from {labels}.",
    ],
    "neural": [
        "An AI component changed as follows: {facts}. Which learning-status label is justified? One of {labels} only.",
        "Audit whether this is actual neural learning: {facts}. Respond with exactly one label from {labels}.",
    ],
    "simulation": [
        "A simulator run has this evidence: {facts}. No extra explanation; select the correct ceiling label from {labels}.",
        "Classify this model-vs-physical evidence state: {facts}. Output exactly one of {labels}.",
    ],
    "proof": [
        "Assess the claim/evidence relation: {facts}. Return the permitted CEREBRON label only: {labels}.",
        "Given this finite/workflow evidence, choose the correct gate label from {labels}; no prose: {facts}.",
    ],
}


def facts_text(f: dict, rng: random.Random) -> str:
    items=[]
    for k,v in f.items():
        if k=="case":
            continue
        if isinstance(v,bool):
            val="true" if v else "false"
        elif v is None or v=="":
            val="missing"
        else:
            val=str(v)
        items.append(f"{k}={val}")
    rng.shuffle(items)
    return "; ".join(items)


def farm_fact(rng, executed: bool):
    f={
        "case":"farm",
        "farm_id":f"F{rng.randint(1,144):03d}",
        "run_id":rng.randint(35000000000,37000000000) if executed else None,
        "job_id":rng.randint(100000000000,110000000000) if executed else None,
        "logs":"present" if executed else ("present" if rng.random()<0.3 else None),
        "artifact_id":rng.randint(10000000000,11000000000) if executed else None,
        "artifact_sha":"sha256:"+hashlib.sha256(str(rng.random()).encode()).hexdigest() if executed else None,
        "output_sha":hashlib.sha256(str(rng.random()).encode()).hexdigest() if executed else None,
    }
    if not executed:
        # Some routed cases have partial evidence, never the complete chain.
        keys=["run_id","job_id","artifact_id","artifact_sha","output_sha"]
        for key in rng.sample(keys,rng.randint(0,3)):
            f[key]=rng.randint(1,999999) if key.endswith("_id") else ("sha256:partial" if "sha" in key else "partial")
    return f


def neural_fact(rng, verified: bool):
    before=round(rng.uniform(0.2,1.2),6)
    after=round(before*rng.uniform(0.02,0.6),6) if verified else round(before*rng.uniform(0.8,1.2),6)
    return {
        "case":"neural",
        "weights_changed":verified,
        "weights_sha":hashlib.sha256(str(rng.random()).encode()).hexdigest() if verified else None,
        "baseline":before,
        "post":after,
        "only_prompt_memory_rag_changed":not verified,
    }


def simulation_fact(rng):
    return {
        "case":"simulation",
        "engine":rng.choice(["Newton","Warp","PhysicsNeMo","synthetic_rover"]),
        "run_id":rng.randint(35000000000,37000000000),
        "artifact_sha":"sha256:"+hashlib.sha256(str(rng.random()).encode()).hexdigest(),
        "physical_test":False,
        "hardware_measurement":False,
    }


def proof_fact(rng):
    return {
        "case":"proof",
        "evidence":rng.choice(["finite_search","workflow_success","simulation","shared_model_consensus"]),
        "finite_limit":rng.randint(10,1000000),
        "universal_claim":True,
        "independent_formal_proof":False,
    }


def make_record(rng: random.Random, split: str, desired: str, idx: int) -> dict:
    if desired=="FARM_EXECUTED":
        facts=farm_fact(rng,True)
    elif desired=="ROUTED_ONLY":
        facts=farm_fact(rng,False)
    elif desired=="NEURAL_LEARNING_VERIFIED":
        facts=neural_fact(rng,True)
    elif desired=="NO_NEURAL_LEARNING":
        facts=neural_fact(rng,False)
    elif desired=="SIMULATION_ONLY":
        facts=simulation_fact(rng)
    elif desired=="CLAIM_BLOCKED":
        facts=proof_fact(rng)
    else:
        raise ValueError(desired)
    a=classify_a(facts); b=classify_b(facts)
    if a!=b or a!=desired:
        raise AssertionError({"a":a,"b":b,"desired":desired,"facts":facts})
    templates=TRAIN_TEMPLATES if split=="train" else M6_TEMPLATES
    template=rng.choice(templates[facts["case"]])
    labels=", ".join(LABELS)
    prompt=template.format(facts=facts_text(facts,rng),labels=labels)
    return {
        "id":f"{split.upper()}-{desired}-{idx:03d}",
        "prompt":prompt,
        "target":desired,
        "facts":facts,
        "rule_a":a,
        "rule_b":b,
    }


def build(seed: int, per_label: int, split: str):
    rng=random.Random(seed)
    records=[]
    for label in LABELS:
        for i in range(per_label):
            records.append(make_record(rng,split,label,i))
    rng.shuffle(records)
    return records


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    train=build(26092311,30,"train")
    m6=build(26092391,10,"m6")
    train_payload={
        "schema":"SAPHEA_EPISTEMIC_POLICY_GOLD_V1",
        "memory_class":"M4_GOLD_SCOPED_POLICY",
        "scope":"CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_ONLY",
        "training_eligible":True,
        "benchmark_exclusion":["COLD60_V1","COLD60_V2","COLD60_V3","COLD60_V4","COLD60_V5"],
        "provenance":PROVENANCE,
        "records":train,
    }
    m6_payload={
        "schema":"SAPHEA_EPISTEMIC_POLICY_M6_V1",
        "memory_class":"M6_COLD_BENCHMARK",
        "deny_training":True,
        "scope":"CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_ONLY",
        "provenance":PROVENANCE,
        "records":m6,
    }
    train_payload["dataset_sha256"]=canon(train_payload)
    m6_payload["dataset_sha256"]=canon(m6_payload)
    TRAIN_PATH.write_text(json.dumps(train_payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    M6_PATH.write_text(json.dumps(m6_payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "train_records":len(train),
        "m6_records":len(m6),
        "train_sha":train_payload["dataset_sha256"],
        "m6_sha":m6_payload["dataset_sha256"],
        "labels":LABELS,
        "dual_rule_agreement":True,
    }))


if __name__=="__main__":
    main()
