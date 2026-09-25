#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT_DEFAULT=ROOT/"artifacts/wave1-quarantine-candidates-v1.json"
SEED=26092501

ROLE_SPECS={
  "AELYS":{
    "labels":["ANSWER","CLARIFY","SUMMARIZE","LIMIT"],
    "count_per_label":24,
    "templates":{
      "ANSWER":[
        "Complete request with sufficient context and no unresolved dependency: {topic}.",
        "All required inputs are present for a direct response about {topic}.",
      ],
      "CLARIFY":[
        "Requested action lacks {missing}; proceeding would require an assumption.",
        "User intent is actionable only after resolving missing field {missing}.",
      ],
      "SUMMARIZE":[
        "A supplied body of {n} factual notes must be compressed while preserving decisions and caveats.",
        "The task explicitly requests condensation of a provided {topic} record, not new research.",
      ],
      "LIMIT":[
        "The requested statement would exceed evidence because {limit}.",
        "Available evidence supports only a narrower claim; blocked element: {limit}.",
      ],
    },
  },
  "ETHERION":{
    "labels":["DEFINE","SOURCE","MODEL","CALCULATE","RED_TEAM","DESIGN_TEST"],
    "count_per_label":24,
    "templates":{
      "DEFINE":[
        "Research objective lacks a frozen {missing}; next action is to formalize scope and success condition.",
        "Problem statement conflates mechanisms and has no explicit {missing}.",
      ],
      "SOURCE":[
        "Decision depends on an external {topic} value absent from the evidence packet.",
        "A material or literature claim about {topic} has no pinned provenance.",
      ],
      "MODEL":[
        "Variables are observed but the relationship between {a} and {b} is not formalized.",
        "Residual structure suggests the current representation of {topic} is incomplete.",
      ],
      "CALCULATE":[
        "Validated equation and dimensionally consistent inputs are present for {topic}; numeric evaluation is next.",
        "The model is fixed and all parameters for {topic} are known.",
      ],
      "RED_TEAM":[
        "Current hypothesis explains the observation, but an alternative {topic} mechanism remains untested.",
        "A broad conclusion rests on a narrow {topic} sample and needs falsification pressure.",
      ],
      "DESIGN_TEST":[
        "Two hypotheses make distinct measurable predictions for {topic}; choose a discriminating experiment.",
        "Observed gain in {topic} needs a controlled comparison with frozen acceptance criteria.",
      ],
    },
  },
  "AFAH":{
    "labels":["ACCEPT","HOLD","REJECT","CORRELATED"],
    "count_per_label":24,
    "templates":{
      "ACCEPT":[
        "Scoped claim has pinned run, artifact digest, reproducible check and independent method for {topic}.",
        "All declared dependencies for {topic} are verified and no critical contradiction remains.",
      ],
      "HOLD":[
        "Evidence for {topic} is promising but required dependency {missing} remains unresolved.",
        "Aggregate gain is positive for {topic}, yet one critical regression gate is still open.",
      ],
      "REJECT":[
        "Claim about {topic} contradicts its artifact or required invariant.",
        "Claim requires a real execution for {topic}, but no executable receipt or matching digest exists.",
      ],
      "CORRELATED":[
        "Multiple confirmations for {topic} share the same model, data, and prompt lineage.",
        "Repeated runs for {topic} are deterministic descendants of one critical dependency.",
      ],
    },
  },
  "METRION":{
    "labels":["PASS","FAIL_UNITS","FAIL_TOLERANCE","SIMULATION_ONLY"],
    "count_per_label":24,
    "templates":{
      "PASS":[
        "Measured {topic}={value} {unit} ±{unc} {unit}; allowed interval contains the full uncertainty band.",
        "Calibrated {topic} result lies inside its verified requirement with stated uncertainty.",
      ],
      "FAIL_UNITS":[
        "Quantity {a} in {unit1} is compared directly with {b} in {unit2} without a valid conversion.",
        "Engineering decision mixes incompatible dimensions {unit1} and {unit2}.",
      ],
      "FAIL_TOLERANCE":[
        "Measured {topic}={value} ±{unc} exceeds the frozen acceptance interval.",
        "Uncertainty band for {topic} crosses a hard specification boundary.",
      ],
      "SIMULATION_ONLY":[
        "A {topic} solver reports success, but there is no hardware observation or physical experiment.",
        "Result for {topic} exists only in a virtual environment with no real-world replication.",
      ],
    },
  },
}

TOPICS=["routing","dialogue","orbital design","thermal margin","evidence fusion","latency","structural load","uncertainty","memory recall","algorithmic gain"]
MISSING=["time","timezone","source provenance","acceptance threshold","external constant","artifact digest","dependency fingerprint"]
UNITS=[("N","kg"),("J","W"),("Pa","N"),("m","s")]
VALUES=[1.2,2.5,5.0,10.0,42.0,81.0,105.0]

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def fill(t,rng):
    u1,u2=rng.choice(UNITS)
    return t.format(
      topic=rng.choice(TOPICS),missing=rng.choice(MISSING),
      a=rng.choice(["input","requirement","measurement","estimate"]),
      b=rng.choice(["limit","output","reference","threshold"]),
      unit=rng.choice(["m","V","kg","mm","°C"]),
      unit1=u1,unit2=u2,
      value=rng.choice(VALUES),unc=rng.choice([0.01,0.05,0.1,0.5,1.0]),
      n=rng.choice([4,6,8,12]),\n      limit=rng.choice(["missing execution receipt","missing physical validation","missing provenance","missing artifact SHA","unverified external dependency"])
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default=str(OUT_DEFAULT))
    args=ap.parse_args()
    rng=random.Random(SEED)
    records=[]
    for role,spec in ROLE_SPECS.items():
        for label in spec["labels"]:
            templ=spec["templates"][label]
            for i in range(spec["count_per_label"]):
                prompt=fill(templ[i%len(templ)],rng)
                payload={
                  "role":role,"target":label,"prompt":prompt,
                  "policy_source":"training/WAVE1_PARALLEL_DATASET_READINESS_V1.json",
                  "candidate_index":i
                }
                records.append({
                  "record_id":f"W1Q-{role}-{label}-{i:03d}",
                  "source_ai":role,
                  "task_id":f"WAVE1-QUARANTINE-{role}",
                  "target":label,
                  "prompt":prompt,
                  "payload_sha256":h(payload),
                  "provenance":{
                    "kind":"DETERMINISTIC_CONTRACT_SYNTHETIC_CANDIDATE",
                    "generator":"tools/wave1_quarantine_candidate_builder.py",
                    "seed":SEED
                  },
                  "dependency_fingerprint":h({"role":role,"label":label,"policy":payload["policy_source"]}),
                  "state":"QUARANTINE",
                  "training_eligible":False,
                  "benchmark_membership":False,
                  "audit_receipts":[],
                  "f72_receipt":None,
                })
    ids=[r["record_id"] for r in records]
    payloads=[r["payload_sha256"] for r in records]
    if len(ids)!=len(set(ids)): raise SystemExit("DUPLICATE_RECORD_ID")
    if len(payloads)!=len(set(payloads)): raise SystemExit("DUPLICATE_PAYLOAD")
    out={
      "schema":"CEREBRON_WAVE1_QUARANTINE_CANDIDATES_V1",
      "seed":SEED,
      "record_count":len(records),
      "training_released":False,
      "state":"QUARANTINE",
      "benchmark_records_included":False,
      "roles":{r:sum(1 for x in records if x["source_ai"]==r) for r in ROLE_SPECS},
      "records":records,
    }
    out["manifest_sha256"]=h(out)
    p=pathlib.Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "record_count":out["record_count"],
      "roles":out["roles"],
      "manifest_sha256":out["manifest_sha256"],
      "training_released":False
    },sort_keys=True))

if __name__=="__main__":
    main()
