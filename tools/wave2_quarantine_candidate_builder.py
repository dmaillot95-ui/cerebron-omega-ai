#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, pathlib, random

SEED=26092520
ROLE_SPECS={
  "SPIRALION":{
    "labels":["CONTINUE","ISOLATE_CONTRADICTION","COMPRESS","VERIFY_NEXT"],
    "templates":{
      "CONTINUE":[
        "Verified checkpoint={cp}; residual={residual}; no contradiction=true; next dependency verified=true.",
        "Prior state hash is stable; open residual={residual}; requested action is direct continuation."
      ],
      "ISOLATE_CONTRADICTION":[
        "Receipt A={a}; receipt B={b}; same pinned input=true; conclusions conflict=true.",
        "New result violates verified invariant={inv}; prior checkpoint otherwise remains valid."
      ],
      "COMPRESS":[
        "Verified notes={n}; repeated facts=true; preserve proofs=true; preserve unknowns=true; preserve dependencies=true.",
        "Context budget exceeded; duplicate summaries={n}; checkpoint must retain only nonredundant verified state."
      ],
      "VERIFY_NEXT":[
        "Continuation depends on unverified item={dep}; next deduction blocked=true.",
        "Claimed improvement exists; cold receipt missing=true; immediate action must be evidence acquisition."
      ]
    }
  },
  "HYPERION":{
    "labels":["ALTERNATIVE","COUNTERFACTUAL","MECHANISM","DIVERSIFY"],
    "templates":{
      "ALTERNATIVE":[
        "Current explanation={topic}; request distinct plausible explanation with different tradeoffs.",
        "Primary architecture exists; task asks for a materially different route."
      ],
      "COUNTERFACTUAL":[
        "Evaluate conclusion if assumption={assumption} is reversed while other variables stay fixed.",
        "Observed result exists; assess hypothetical world where control condition changes."
      ],
      "MECHANISM":[
        "Correlation pattern={topic}; causal process not specified; task asks how it could arise.",
        "Failure repeats under condition={condition}; goal is a causal chain, not another fit."
      ],
      "DIVERSIFY":[
        "Candidate set size={n}; all variants share same representation; orthogonal families required.",
        "Agents converged on one method; next action is non-overlapping candidate generation."
      ]
    }
  },
  "ASTRION":{
    "labels":["REQUIREMENTS","PHYSICS_MODEL","CALCULATE","TEST"],
    "templates":{
      "REQUIREMENTS":[
        "Vehicle concept={topic}; payload target missing=true; delta-v target missing={flag}; acceptance criteria incomplete=true.",
        "Mission concept lacks frozen duty cycle, throughput or lifetime requirement."
      ],
      "PHYSICS_MODEL":[
        "Requirements fixed=true; governing relation for {topic} absent=true; coupling not formalized=true.",
        "Geometry and boundary conditions exist; physical model for {topic} is still missing."
      ],
      "CALCULATE":[
        "Validated equation=true; all numeric inputs present=true; units consistent=true; target metric={topic}.",
        "Model frozen=true; parameters complete=true; next step is numerical evaluation."
      ],
      "TEST":[
        "Simulation promising=true; hardware evidence missing=true; acceptance test for {topic} required.",
        "Analytical result exists; operational claim blocked until controlled validation."
      ]
    }
  },
  "SAPHEA_MICRO":{
    "labels":["ROUTE","MATH","CODE","RESEARCH","INVENT","RED_TEAM","FUSION"],
    "templates":{
      "ROUTE":[
        "Task mixes domains={mix}; select smallest useful specialist coalition before execution.",
        "Incoming request not yet decomposed; first operation is specialist routing."
      ],
      "MATH":[
        "Task type=formal symbolic proof; web dependency=false; implementation dependency=false.",
        "Need derivation of identity={topic}; execution tools unnecessary."
      ],
      "CODE":[
        "Traceback present=true; failing test reproducible=true; next operation is implementation debug.",
        "Task requests deterministic parser implementation plus unit tests."
      ],
      "RESEARCH":[
        "Claim depends on current external source={topic}; provenance missing=true.",
        "Specification may have changed; current authoritative retrieval required."
      ],
      "INVENT":[
        "Goal requests novel architecture under constraints={topic}; multiple concepts desired before scoring.",
        "Task is generative design, not verification of an existing candidate."
      ],
      "RED_TEAM":[
        "Result appears plausible; hidden assumption risk=true; counterexample search required.",
        "Benchmark gain may be leakage; next mission is falsification."
      ],
      "FUSION":[
        "Specialist outputs={n}; some lineage shared=true; synthesize without double-counting evidence.",
        "Multiple partial results exist; merge into one dependency-preserving decision."
      ]
    }
  }
}

TOPICS=["orbital transfer","thermal margin","evidence fusion","checkpoint chain","propulsion","routing","proof search","structural load","memory continuity","parser behavior"]
RESIDUALS=["unresolved lemma","missing transfer test","unverified constant","open dependency","unexplained residual"]
ASSUMPTIONS=["gravity present","constant density","perfect sensor","single failure mode","closed boundary"]
CONDITIONS=["high load","low temperature","long duty cycle","delayed feedback","shared lineage"]

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def fill(t,rng,i):
    return t.format(
      cp=f"CP-{1000+i}",residual=rng.choice(RESIDUALS),
      a=f"A-{2000+i}",b=f"B-{3000+i}",inv=rng.choice(["energy_budget","hash_chain","claim_ceiling","unit_consistency"]),
      dep=rng.choice(["external constant","cold benchmark","artifact digest","independent receipt"]),
      n=rng.choice([5,12,24,40]),topic=rng.choice(TOPICS),
      assumption=rng.choice(ASSUMPTIONS),condition=rng.choice(CONDITIONS),
      flag=rng.choice(["true","false"]),mix=rng.choice(["math+code","research+audit","code+research","invention+redteam"])
    )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    rng=random.Random(SEED)
    rows=[]
    for role,spec in ROLE_SPECS.items():
        for label in spec["labels"]:
            tmpls=spec["templates"][label]
            for i in range(24):
                prompt=fill(tmpls[i%len(tmpls)],rng,i)
                payload={"role":role,"target":label,"prompt":prompt,"i":i,"seed":SEED}
                rows.append({
                  "record_id":f"W2Q-{role}-{label}-{i:03d}",
                  "source_ai":role,
                  "target":label,
                  "prompt":prompt,
                  "payload_sha256":sha(payload),
                  "provenance":{"kind":"DETERMINISTIC_CONTRACT_SYNTHETIC_CANDIDATE","generator":"tools/wave2_quarantine_candidate_builder.py","seed":SEED},
                  "dependency_fingerprint":sha({"role":role,"label":label}),
                  "state":"QUARANTINE",
                  "training_eligible":False,
                  "benchmark_membership":False
                })
    ids=[r["record_id"] for r in rows]
    pshas=[r["payload_sha256"] for r in rows]
    if len(ids)!=len(set(ids)): raise SystemExit("DUPLICATE_ID")
    if len(pshas)!=len(set(pshas)): raise SystemExit("DUPLICATE_PAYLOAD")
    out={
      "schema":"CEREBRON_WAVE2_QUARANTINE_CANDIDATES_V1",
      "seed":SEED,
      "record_count":len(rows),
      "roles":{r:sum(1 for x in rows if x["source_ai"]==r) for r in ROLE_SPECS},
      "state":"QUARANTINE",
      "training_released":False,
      "benchmark_records_included":False,
      "records":rows
    }
    out["manifest_sha256"]=sha(out)
    p=pathlib.Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"record_count":out["record_count"],"roles":out["roles"],"manifest_sha256":out["manifest_sha256"]},sort_keys=True))

if __name__=="__main__":
    main()
