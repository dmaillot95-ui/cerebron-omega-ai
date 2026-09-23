#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
TYPES={"APPLY","DO_NOT_APPLY","COUNTEREXAMPLE","TRANSFER","ADVERSARIAL","ABLATION_CONTROL"}
REQ={"example_id","macro_seed_id","type","input","target_behavior","rationale","provenance","dependency_fingerprint","blind_split"}
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--example",required=True); p.add_argument("--out",required=True); a=p.parse_args()
 x=json.loads(Path(a.example).read_text()); missing=sorted(k for k in REQ if not x.get(k))
 valid_type=x.get("type") in TYPES
 contaminated=bool(x.get("benchmark_leakage",False)) or bool(x.get("answer_seen_before_generation",False))
 structural=not missing and valid_type and not contaminated
 out={"schema":"macro-seed-instantiated-example-v1","example_id":x.get("example_id"),"macro_seed_id":x.get("macro_seed_id"),
 "type":x.get("type"),"structurally_eligible":structural,"missing":missing,"contaminated":contaminated,
 "example_sha256":digest(x),"validation_state":"AUDIT_REQUIRED" if structural else "REJECT",
 "audit_pass":False,"counter_audit_pass":False,"f72_pass":False,"afah_pass":False,
 "validated_training_example":False,"training_released":False,
 "claim_scope":"Instantiation gate only; this does not validate scientific correctness or authorize training."}
 Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out))
 if not structural: raise SystemExit(3)
if __name__=="__main__": main()
