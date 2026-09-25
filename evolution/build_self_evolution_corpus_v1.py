#!/usr/bin/env python3
"""Build a provenance-rich self-evolution corpus from CEREBRON memory banks.

The output is NOT automatically a training dataset. Admission is explicit.
"""
import json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evolution.cerebron_self_evolution import normalize_text, sha256_text, stable_split

def load(p):
    return json.loads((ROOT/p).read_text())

failure=load("memory/failure-bank-v1.json")
lesson=load("memory/lesson-bank-v1.json")
contra=load("memory/contradiction-bank-v1.json")
gvl=load("memory/gvl-lesson-index.json")

records=[]

def add(record):
    text=record["text"].strip()
    record["normalized_sha256"]=sha256_text(normalize_text(text))
    record["split"]=stable_split(record["record_id"])
    records.append(record)

for e in failure.get("entries",[]):
    fid=e["FAILURE_ID"]
    text="\n".join([
      "FAILURE_SIGNATURE: "+str(e.get("FAILURE_SIGNATURE","")),
      "ROOT_CAUSE: "+str(e.get("ROOT_CAUSE","")),
      "IMPACT: "+str(e.get("IMPACT","")),
      "SCOPE: "+str(e.get("SCOPE","")),
      "REPAIR_STATUS: "+str(e.get("REPAIR_STATUS","")),
      "TRANSFER_RISK: "+str(e.get("TRANSFER_RISK","")),
      "REPAIR_ATTEMPTS: "+" | ".join(map(str,e.get("REPAIR_ATTEMPTS",[]))),
    ])
    add({
      "record_id":fid,
      "source_bank":"FAILURE_BANK",
      "source_class":e.get("FAILURE_CLASS"),
      "ai_id":e.get("AI_ID"),
      "mission_id":e.get("MISSION_ID"),
      "text":text,
      "evidence_refs":e.get("EVIDENCE_REFS",[]),
      "reproducible":bool(e.get("REPRODUCIBLE")),
      "admission_class":"RED_CANDIDATE",
      "training_eligible":False,
      "use_for":["CURRICULUM","EVALUATION","COUNTEREXAMPLE_GENERATION"],
      "reason":"Failure Bank entries require explicit RED admission before weight training."
    })

auto_allowed=set(lesson.get("auto_propagation_allowed",[]))
for e in lesson.get("entries",[]):
    lid=e["LESSON_ID"]
    klass=e.get("CLASS")
    eligible=klass in auto_allowed
    text="\n".join([
      "TITLE: "+str(e.get("TITLE","")),
      "DESCRIPTION: "+str(e.get("DESCRIPTION","")),
      "LIMITS: "+str(e.get("LIMITS","")),
      "PROMOTION_STATUS: "+str(e.get("PROMOTION_STATUS","")),
    ])
    add({
      "record_id":lid,
      "source_bank":"LESSON_BANK",
      "source_class":klass,
      "ai_id":None,
      "mission_id":e.get("MISSION_ID"),
      "text":text,
      "evidence_refs":e.get("EVIDENCE_REFS",[]),
      "reproducible":None,
      "admission_class":"GOLD" if eligible else "LESSON_WORKING",
      "training_eligible":eligible,
      "use_for":["TRAINING","CURRICULUM"] if eligible else ["CURRICULUM","EVALUATION"],
      "reason":"Auto-propagation only for L5_VALIDATED/L6_PROMOTED."
    })

for e in contra.get("entries",[]):
    cid=e["CONTRADICTION_ID"]
    text="\n".join([
      "CLAIM_A: "+str(e.get("CLAIM_A","")),
      "CLAIM_B: "+str(e.get("CLAIM_B","")),
      "CONTEXT: "+str(e.get("CONTEXT","")),
      "RESOLUTION_STATUS: "+str(e.get("RESOLUTION_STATUS","")),
      "RESOLUTION_TEST: "+str(e.get("RESOLUTION_TEST","")),
    ])
    add({
      "record_id":cid,
      "source_bank":"CONTRADICTION_BANK",
      "source_class":"CONTRADICTION",
      "ai_id":None,
      "mission_id":None,
      "text":text,
      "evidence_refs":[x for x in [e.get("SOURCE_A"),e.get("SOURCE_B"),e.get("EVIDENCE_A"),e.get("EVIDENCE_B")] if x],
      "reproducible":None,
      "admission_class":"CONTRADICTION_REFERENCE",
      "training_eligible":False,
      "use_for":["REDTEAM","EVALUATION","CALIBRATION"],
      "reason":"Contradictions remain visible and are not silently converted to targets."
    })

for e in gvl.get("lessons",[]):
    gid=e["lesson_id"]
    status=e.get("promotion_status")
    eligible=status in {"L5_VALIDATED","L6_PROMOTED","PROMOTED"}
    text="\n".join([
      "PROBLEM_CLASS: "+str(e.get("problem_class","")),
      "INVARIANT: "+str(e.get("invariant","")),
      "SCOPE: "+str(e.get("scope","")),
      "FAILURE_MODES: "+" | ".join(map(str,e.get("failure_modes",[]))),
      "PROMOTION_STATUS: "+str(status),
      "NOTE: "+str(e.get("note","")),
    ])
    add({
      "record_id":gid,
      "source_bank":"GVL_LESSON_INDEX",
      "source_class":status,
      "ai_id":e.get("source_ai"),
      "mission_id":None,
      "text":text,
      "evidence_refs":e.get("evidence_refs",[]),
      "reproducible":None,
      "admission_class":"GOLD" if eligible else "GVL_REFERENCE",
      "training_eligible":eligible,
      "use_for":["TRAINING","CURRICULUM"] if eligible else ["CURRICULUM","EVALUATION"],
      "reason":"GVL promotion must be explicit."
    })

# Exact normalized dedup, preserving all lineage references but only one canonical record.
by_hash={}
duplicates=[]
canonical=[]
authority={"LESSON_BANK":4,"GVL_LESSON_INDEX":3,"FAILURE_BANK":2,"CONTRADICTION_BANK":1}
for r in records:
    h=r["normalized_sha256"]
    if h not in by_hash:
        by_hash[h]=r
        canonical.append(r)
    else:
        prior=by_hash[h]
        # Prefer higher authority, but preserve duplicate relation.
        if authority.get(r["source_bank"],0)>authority.get(prior["source_bank"],0):
            canonical.remove(prior)
            canonical.append(r)
            by_hash[h]=r
            prior,r=r,prior
        duplicates.append({
          "duplicate_id":r["record_id"],
          "canonical_id":prior["record_id"],
          "normalized_sha256":h
        })

eligible=[r for r in canonical if r["training_eligible"]]
splits={k:sum(r["split"]==k for r in canonical) for k in ("train","validation","holdout")}
eligible_splits={k:sum(r["split"]==k and r["training_eligible"] for r in canonical) for k in ("train","validation","holdout")}

report={
  "schema":"CEREBRON_SELF_EVOLUTION_CORPUS_V1",
  "status":"BUILT_NOT_RELEASED",
  "source_counts":{
    "failure_bank":len(failure.get("entries",[])),
    "lesson_bank":len(lesson.get("entries",[])),
    "contradiction_bank":len(contra.get("entries",[])),
    "gvl_lesson_index":len(gvl.get("lessons",[]))
  },
  "raw_record_count":len(records),
  "canonical_record_count":len(canonical),
  "duplicate_count":len(duplicates),
  "split_counts":splits,
  "training_eligible_count":len(eligible),
  "training_eligible_split_counts":eligible_splits,
  "weight_training_released":False,
  "release_reason":"Requires explicit dataset seal plus minimum target coverage; corpus build alone never releases training.",
  "records":canonical,
  "duplicates":duplicates
}
out=ROOT/"artifacts/cerebron-self-evolution-corpus.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:report[k] for k in [
  "status","source_counts","raw_record_count","canonical_record_count",
  "duplicate_count","split_counts","training_eligible_count",
  "training_eligible_split_counts","weight_training_released"
]},sort_keys=True))
