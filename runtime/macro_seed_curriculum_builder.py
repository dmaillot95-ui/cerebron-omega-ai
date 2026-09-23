#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
TYPES=["APPLY","DO_NOT_APPLY","COUNTEREXAMPLE","TRANSFER","ADVERSARIAL","ABLATION_CONTROL"]
REQ=["macro_seed_id","title","invariant","procedure","scope","provenance","dependency_fingerprint","f72_status","afah_approved"]
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument("--seed",required=True);a.add_argument("--out",required=True);z=a.parse_args()
 s=json.loads(Path(z.seed).read_text()); missing=[k for k in REQ if not s.get(k)]
 eligible=not missing and s["f72_status"] in {"GOLD_VALIDATED","RED_VALIDATED"} and s["afah_approved"] is True
 if not eligible:
  out={"schema":"macro-seed-curriculum-v1","macro_seed_id":s.get("macro_seed_id"),"eligible":False,"missing":missing,"examples":[],"training_released":False}
 else:
  # Deterministic curriculum skeletons; content must later be instantiated and audited, never fabricated as validated data.
  templates={
   "APPLY":"Apply the invariant within its declared scope and justify each procedural step.",
   "DO_NOT_APPLY":"Detect a case outside scope and explain why the invariant must not be forced.",
   "COUNTEREXAMPLE":"Construct or analyze a counterexample that tests the invariant's boundary.",
   "TRANSFER":"Apply the invariant to a distinct domain while preserving only justified structure.",
   "ADVERSARIAL":"Handle a misleading case designed to trigger superficial use of the invariant.",
   "ABLATION_CONTROL":"Solve a matched case without the macro-seed cue for causal comparison."
  }
  ex=[{"type":t,"instruction_template":templates[t],"source_seed":s["macro_seed_id"],"validated_training_example":False} for t in TYPES]
  out={"schema":"macro-seed-curriculum-v1","macro_seed_id":s["macro_seed_id"],"eligible":True,"seed_sha256":h(s),"examples":ex,
       "training_released":False,"next_gate":"INSTANTIATE_THEN_AUDIT_COUNTERAUDIT_F72_AFAH",
       "claim_scope":"Curriculum skeleton only; examples are not validated training records."}
 out["curriculum_sha256"]=h(out);Path(z.out).parent.mkdir(parents=True,exist_ok=True);Path(z.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
