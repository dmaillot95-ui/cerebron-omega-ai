from __future__ import annotations

import hashlib
import json
import pathlib
import random

ROOT=pathlib.Path("platform/artifacts")
OUT=ROOT/"saphea-epistemic-repair-gold-v2.json"
SEED=26092571
PER_LABEL=30
LABELS=[
    "ROUTED_ONLY","FARM_EXECUTED","NO_NEURAL_LEARNING",
    "NEURAL_LEARNING_VERIFIED","SIMULATION_ONLY","CLAIM_BLOCKED",
]

def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def oracle_a(f):
    kind=f["kind"]
    if kind=="farm":
        complete=all(f.get(k) not in (None,"",False) for k in ["run","job","logs","artifact","artifact_sha","output_sha"])
        return "FARM_EXECUTED" if complete else "ROUTED_ONLY"
    if kind=="neural":
        ok=bool(
            f.get("weights_changed") is True
            and f.get("weights_sha")
            and isinstance(f.get("before"),(int,float))
            and isinstance(f.get("after"),(int,float))
            and f["after"] < f["before"]
        )
        return "NEURAL_LEARNING_VERIFIED" if ok else "NO_NEURAL_LEARNING"
    if kind=="simulation":
        return "SIMULATION_ONLY" if f.get("physical_test") is False else "CLAIM_BLOCKED"
    if kind=="claim":
        return "CLAIM_BLOCKED"
    raise ValueError(kind)

def oracle_b(f):
    if f["kind"]=="farm":
        missing=sum(1 for k in ["run","job","logs","artifact","artifact_sha","output_sha"] if not f.get(k))
        return "ROUTED_ONLY" if missing else "FARM_EXECUTED"
    if f["kind"]=="neural":
        if not f.get("weights_changed"):
            return "NO_NEURAL_LEARNING"
        if not f.get("weights_sha"):
            return "NO_NEURAL_LEARNING"
        if f.get("after") is None or f.get("before") is None or f["after"]>=f["before"]:
            return "NO_NEURAL_LEARNING"
        return "NEURAL_LEARNING_VERIFIED"
    if f["kind"]=="simulation" and not f.get("physical_test"):
        return "SIMULATION_ONLY"
    return "CLAIM_BLOCKED"

ALIASES={
    "run":["execution_receipt","run_ref","workflow_receipt"],
    "job":["worker_receipt","job_ref","task_receipt"],
    "logs":["log_chain","logs_present","execution_logs"],
    "artifact":["artifact_ref","output_artifact","artifact_object"],
    "artifact_sha":["artifact_digest","artifact_hash","artifact_sha256"],
    "output_sha":["result_digest","output_hash","result_sha256"],
    "weights_changed":["parameter_delta","weights_updated","adapter_changed"],
    "weights_sha":["parameter_digest","weight_artifact_hash","adapter_sha"],
    "before":["sealed_metric_before","baseline_loss","metric_pre"],
    "after":["sealed_metric_after","post_loss","metric_post"],
    "physical_test":["physical_measurement","hardware_test","real_world_test"],
    "universal_claim":["universal_scope_requested","claim_all_cases","universal_claim"],
    "formal_proof":["independent_formal_proof","formal_derivation","proof_certificate"],
}

TEMPLATES=[
    "Evidence ledger: {facts}. Return exactly one permitted CEREBRON state from [{labels}].",
    "Contrastive audit case — {facts}. Decide only from evidence, not intent. One token: [{labels}].",
    "Boundary classification record: {facts}. Output the single strongest justified state among [{labels}].",
    "Epistemic routing check: {facts}. Ignore confidence and workflow colour; emit one state token from [{labels}].",
]

def render_facts(f,rng):
    parts=[]
    for k,v in f.items():
        if k in {"kind","target","pair_id"}:
            continue
        name=rng.choice(ALIASES.get(k,[k]))
        if isinstance(v,bool):
            val="yes" if v else "no"
        elif v is None or v=="":
            val="absent"
        else:
            val=str(v)
        parts.append(f"{name}={val}")
    parts.extend([
        f"workflow_colour={rng.choice(['green','amber','red'])}",
        f"confidence_hint={rng.choice(['low','medium','high'])}",
        f"operator_note={rng.choice(['routine','urgent','crosscheck'])}",
    ])
    rng.shuffle(parts)
    return " ; ".join(parts)

def farm_pair(i,rng):
    common={
        "kind":"farm",
        "run":f"RUN-{70000+i}",
        "job":f"JOB-{90000+i}",
        "logs":"present",
        "artifact":f"ART-{50000+i}",
        "artifact_sha":"sha256:"+hashlib.sha256(f"farm-a-{i}".encode()).hexdigest(),
        "output_sha":hashlib.sha256(f"farm-o-{i}".encode()).hexdigest(),
    }
    good=dict(common,target="FARM_EXECUTED",pair_id=f"FARM-{i:02d}-EXEC")
    bad=dict(common,target="ROUTED_ONLY",pair_id=f"FARM-{i:02d}-ROUTE")
    miss=["run","job","logs","artifact","artifact_sha","output_sha"][i%6]
    bad[miss]=None
    return good,bad

def neural_pair(i,rng):
    before=round(0.55+0.01*(i%7),4)
    after=round(before*(0.35+0.02*(i%4)),4)
    good={
        "kind":"neural","target":"NEURAL_LEARNING_VERIFIED","pair_id":f"NEURAL-{i:02d}-YES",
        "weights_changed":True,
        "weights_sha":hashlib.sha256(f"neural-w-{i}".encode()).hexdigest(),
        "before":before,"after":after,
        "prompt_only_change":False,"memory_only_change":False,
    }
    bad=dict(good,target="NO_NEURAL_LEARNING",pair_id=f"NEURAL-{i:02d}-NO")
    mode=i%4
    if mode==0:
        bad.update(weights_changed=False,weights_sha=None,prompt_only_change=True)
    elif mode==1:
        bad.update(weights_sha=None)
    elif mode==2:
        bad.update(after=round(before*1.08,4))
    else:
        bad.update(weights_changed=False,weights_sha=None,memory_only_change=True,prompt_only_change=False)
    return good,bad

def simulation_claim_pair(i,rng):
    sim={
        "kind":"simulation","target":"SIMULATION_ONLY","pair_id":f"EVID-{i:02d}-SIM",
        "engine":rng.choice(["digital_twin","thermal_solver","orbital_reference","fluid_mesh"]),
        "simulation_receipt":f"SIM-{80000+i}",
        "physical_test":False,
        "hardware_observation":False,
        "universal_claim":False,
        "formal_proof":False,
    }
    claim={
        "kind":"claim","target":"CLAIM_BLOCKED","pair_id":f"EVID-{i:02d}-BLOCK",
        "evidence_kind":rng.choice(["finite_search","workflow_success","shared_model_vote","simulation"]),
        "tested_cases":5000+i*31,
        "universal_claim":True,
        "formal_proof":False,
        "physical_test":False,
    }
    return sim,claim

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    buckets={k:[] for k in LABELS}
    for i in range(PER_LABEL):
        g,b=farm_pair(i,rng)
        buckets[g["target"]].append(g); buckets[b["target"]].append(b)
        g,b=neural_pair(i,rng)
        buckets[g["target"]].append(g); buckets[b["target"]].append(b)
        g,b=simulation_claim_pair(i,rng)
        buckets[g["target"]].append(g); buckets[b["target"]].append(b)

    # Pair generators create exactly PER_LABEL examples for each class.
    records=[]
    for label in LABELS:
        if len(buckets[label])!=PER_LABEL:
            raise AssertionError((label,len(buckets[label])))
        for i,facts in enumerate(buckets[label]):
            a,b=oracle_a(facts),oracle_b(facts)
            if a!=label or b!=label:
                raise AssertionError({"label":label,"a":a,"b":b,"facts":facts})
            opts=list(LABELS); rng.shuffle(opts)
            prompt=rng.choice(TEMPLATES).format(
                facts=render_facts(facts,rng),
                labels=", ".join(opts),
            )
            records.append({
                "id":f"REPAIR2-{label}-{i:03d}",
                "pair_id":facts["pair_id"],
                "prompt":prompt,
                "target":label,
                "facts":facts,
                "rule_a":a,
                "rule_b":b,
                "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
            })
    rng.shuffle(records)

    payload={
        "schema":"SAPHEA_EPISTEMIC_REPAIR_GOLD_V2",
        "memory_class":"M4_GOLD_SCOPED_POLICY",
        "scope":"CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_ONLY",
        "training_eligible":True,
        "diagnosis_informed":True,
        "cold_benchmark_content_used":False,
        "source_failure_class":"CLASS_PRIOR_COLLAPSE",
        "record_count":len(records),
        "per_label":PER_LABEL,
        "seed":SEED,
        "design":[
            "PAIRWISE_CONTRASTIVE_BOUNDARIES",
            "FIELD_ALIAS_VARIATION",
            "IRRELEVANT_DISTRACTORS",
            "CLASS_BALANCED",
            "NO_TRANSFER_OR_REDTEAM_EXAMPLES",
        ],
        "records":records,
    }
    payload["dataset_sha256"]=canon(payload)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "records":len(records),
        "per_label":PER_LABEL,
        "dataset_sha256":payload["dataset_sha256"],
        "cold_benchmark_content_used":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
