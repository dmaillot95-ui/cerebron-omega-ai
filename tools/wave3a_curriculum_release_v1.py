#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,random

SEED=26092631
MODEL={"id":"HuggingFaceTB/SmolLM3-3B","revision":"a07cc9a04f16550a088caea529712d1d335b0ac1"}
SPECS={
 "ELYSION":{
  "scope":"reasoning generation invention and solution search",
  "labels":{
   "HYPOTHESIZE":["Observed anomaly={x}; mechanism is unknown; generate a testable explanation before selecting a solution.","Evidence is incomplete for {x}; construct a falsifiable candidate mechanism."],
   "DERIVE":["Assumptions are frozen; governing relations are available; derive the consequence for {x} before proposing alternatives.","Known constraints fully specify {x}; next operation is a formal derivation."],
   "SEARCH":["Several solution families may satisfy {x}; explore non-overlapping candidates before committing.","Current candidate is plausible but not unique; search the design space for {x}."],
   "INVENT":["Existing approaches violate constraint={c}; construct a materially new architecture for {x}.","No listed method meets {c}; synthesize a new mechanism for {x}."],
  }},
 "ELYSIUM":{
  "scope":"verification falsification constraint audit and validation",
  "labels":{
   "VERIFY":["Claim={x}; provenance and calculation exist; reproduce the decisive check before acceptance.","Result for {x} has a receipt; independently verify the stated invariant."],
   "FALSIFY":["Claim={x} appears strong; search for a counterexample or hidden assumption first.","Consensus exists around {x}; attempt to break it under edge conditions."],
   "CONSTRAIN":["Proposal={x}; feasibility envelope is undefined; derive hard limits from {c}.","Before optimizing {x}, identify the binding physical or logical constraints."],
   "REJECT":["Claim={x}; evidence is missing or contradicts {c}; refuse promotion and preserve uncertainty.","Result for {x} exceeds its evidence ceiling; reject the unsupported conclusion."],
  }},
 "SAELION":{
  "scope":"learning selection compression and information gain",
  "labels":{
   "SELECT":["Candidates for {x} have measured scores; choose the smallest useful option without hiding uncertainty.","Ablation exists for {x}; select only the component with demonstrated gain."],
   "COMPRESS":["History for {x} contains repeated facts; compress while preserving contradictions, hashes and open items.","Context for {x} is redundant; retain canonical evidence and unresolved dependencies."],
   "CURRICULUM":["Failure on {x} is reproducible; create the next exercise targeting the observed error, not the answer key.","Model weakness={c}; design a corrective lesson for {x} while keeping cold data sealed."],
   "VERIFY_NEXT":["Progress on {x} depends on unverified dependency={c}; acquire that evidence before further learning.","New lesson for {x} lacks transfer evidence; next action is evaluation, not promotion."],
  }},
 "NEXUS":{
  "scope":"knowledge connection interface integration and multi-AI orchestration",
  "labels":{
   "CONNECT":["Evidence for {x} is split across two compatible sources; link them by explicit dependency without merging identities.","Two verified results concern {x}; construct a provenance-preserving connection."],
   "ROUTE":["Task={x} spans domains; assign the smallest specialist coalition required by {c}.","Input for {x} needs distinct expertise; route before execution."],
   "INTEGRATE":["Components for {x} passed local tests; validate interfaces, schemas and failure propagation before system claim.","Subsystems for {x} are individually valid; perform integration checks against {c}."],
   "TRACE":["Output for {x} cannot be promoted until source, model, revision and artifact hashes are linked.","Dependency chain for {x} is incomplete; reconstruct provenance before fusion."],
  }}
}
X=["orbital rendezvous","proof search","thermal control","memory retrieval","robot planning","sensor fusion","software parser","energy storage","materials selection","trajectory design","evidence fusion","resource scheduling"]
C=["mass budget","unit consistency","latency ceiling","cold-test separation","interface contract","energy limit","lineage independence","safety margin"]

def sha(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def rec(role,label,text,i,kind,seed):
 p={"role":role,"target":label,"prompt":text,"i":i,"kind":kind,"seed":seed}
 return {"record_id":f"W3A-{kind}-{role}-{label}-{i:03d}","source_ai":role,"target":label,"prompt":text,"payload_sha256":sha(p),"provenance":{"kind":"DETERMINISTIC_ROLE_SPECIFIC_SYNTHETIC_CURRICULUM","generator":"tools/wave3a_curriculum_release_v1.py","seed":seed},"benchmark_membership":kind!="TRAINPOOL","training_eligible":kind=="TRAINPOOL"}
def fill(t,rng):return t.format(x=rng.choice(X),c=rng.choice(C))
def make_records(role,kind,n_per_label,seed):
 rng=random.Random(seed); rows=[]
 for label,tmpls in SPECS[role]["labels"].items():
  for i in range(n_per_label):
   base=tmpls[i%len(tmpls)]
   suffix=f" Evidence ticket={role[:2]}-{kind[:2]}-{i:02d}; priority={1+(i%5)}."
   rows.append(rec(role,label,fill(base,rng)+suffix,i,kind,seed))
 return rows
def dataset(role,kind,n,seed,deny):
 rows=make_records(role,kind,n,seed)
 out={"schema":"CEREBRON_WAVE3A_SUITE_V1","role":role,"suite":kind,"records":rows,"count":len(rows),"deny_training":deny,"training_eligible":not deny}
 out["dataset_sha256"]=sha(out);return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output-dir",required=True);a=ap.parse_args();root=pathlib.Path(a.output_dir);root.mkdir(parents=True,exist_ok=True)
 release={"schema":"CEREBRON_WAVE3A_COREB_CANDIDATE_V1","state":"CANDIDATE_NOT_RELEASED","training_released":False,"continuous_training_eligible":False,"training_executed":False,"weights_changed":False,"materially_new_data_or_method":True,"core":"CORE_B","model":MODEL,"roles":{},"uses_m6_as_training":False,"uses_transfer_as_training":False,"uses_red_as_training":False,"dual_core_complete":False,"admission_required":["DATASET_AUDIT","SEMANTIC_DEDUP","PROVENANCE_REVIEW","F72_OR_EQUIVALENT","DISPATCH_WORKFLOW_REVIEW","COMPUTE_CONFIRMATION"],"claim_scope":"ROLE_SPECIFIC_CORE_B_POLICY_ADAPTER_CANDIDATE_NOT_GENERAL_CAPABILITY_NOT_DUAL_CORE_COMPLETE"}
 all_train_hashes=set();all_bench_hashes=set()
 for ridx,role in enumerate(SPECS):
  pool=make_records(role,"TRAINPOOL",24,SEED+ridx)
  by={lab:[r for r in pool if r["target"]==lab] for lab in SPECS[role]["labels"]}
  train=[];val=[]
  for lab,rows in by.items():
   rr=list(rows);random.Random(SEED+ridx+sum(map(ord,lab))).shuffle(rr);train+=rr[:18];val+=rr[18:]
  split={"schema":"CEREBRON_WAVE3A_SPLIT_V1","role":role,"train_records":train,"validation_records":val,"per_label":{lab:{"train":18,"validation":6} for lab in by},"training_source":"DETERMINISTIC_ROLE_SPECIFIC_SYNTHETIC_CURRICULUM"}
  split["split_sha256"]=sha(split)
  suites={"M6":dataset(role,"M6",8,SEED+100+ridx,True),"TRANSFER":dataset(role,"TRANSFER",8,SEED+200+ridx,True),"RED":dataset(role,"RED",4,SEED+300+ridx,True)}
  train_hash={r["payload_sha256"] for r in train+val};bench_hash={r["payload_sha256"] for d in suites.values() for r in d["records"]}
  if train_hash & bench_hash:raise SystemExit(f"LEAKAGE_{role}")
  if all_train_hashes & train_hash:raise SystemExit(f"CROSS_ROLE_TRAIN_DUP_{role}")
  all_train_hashes|=train_hash;all_bench_hashes|=bench_hash
  rp=root/role.lower();rp.mkdir(exist_ok=True)
  (rp/"split.json").write_text(json.dumps(split,indent=2,ensure_ascii=False)+"\n")
  for name,d in suites.items():(rp/(name.lower()+".json")).write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
  release["roles"][role]={"scope":SPECS[role]["scope"],"train_count":len(train),"validation_count":len(val),"train_record_ids":[r["record_id"] for r in train],"split_sha256":split["split_sha256"],"cold":{n:{"count":d["count"],"dataset_sha256":d["dataset_sha256"],"deny_training":True} for n,d in suites.items()},"model":MODEL}
 if all_train_hashes & all_bench_hashes:raise SystemExit("GLOBAL_TRAIN_BENCH_LEAKAGE")
 release["release_sha256"]=sha(release)
 (root/"release.json").write_text(json.dumps(release,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"status":"CANDIDATE_NOT_RELEASED","roles":list(SPECS),"train_per_role":72,"validation_per_role":24,"release_sha256":release["release_sha256"],"benchmark_leakage":False,"training_released":False,"continuous_training_eligible":False,"training_executed":False,"weights_changed":False},sort_keys=True))
if __name__=="__main__":main()
