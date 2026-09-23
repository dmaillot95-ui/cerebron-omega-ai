#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
VALID={"GOLD_VALIDATED","RED_VALIDATED"}
REQ=["lesson_id","source_ai","summary","chapter","concepts","procedure","examples","counterexamples","failure_modes","relations","provenance","evidence","dependency_fingerprint","f72_status","payload_sha256"]
def main():
 p=argparse.ArgumentParser();p.add_argument("--lesson",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 x=json.loads(Path(a.lesson).read_text()); miss=[k for k in REQ if k not in x or x[k] in (None,"",[])]
 validated=x.get("f72_status") in VALID and not miss
 stable=bool(x.get("stable_generalizable",False)); utility=float(x.get("reuse_score",0)); risk=float(x.get("regression_risk",1))
 vector=validated
 param=validated and stable and utility>=0.70 and risk<=0.30
 out={"schema":"cerebron-lesson-route-v1","lesson_id":x.get("lesson_id"),"validated":validated,
 "missing":miss,"routes":{"VECTOR_MEMORY":vector,"PARAMETER_CANDIDATE":param},
 "parameter_reason":"ELIGIBLE_FOR_CURATOR_REVIEW" if param else "NOT_ELIGIBLE",
 "training_released":False,
 "claim_scope":"Routing eligibility only; parameter candidate is not training, learning, or promotion."}
 raw=(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n").encode();out["route_sha256"]=hashlib.sha256(raw).hexdigest()
 Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
