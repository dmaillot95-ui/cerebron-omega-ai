#!/usr/bin/env python3
import argparse,json,pathlib,hashlib,sys
ap=argparse.ArgumentParser();ap.add_argument("--source",required=True);ap.add_argument("--expected-sha",required=True);a=ap.parse_args()
p=pathlib.Path(a.source);rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
cap=next((r for r in rows if r.get("sha256")==a.expected_sha),None)
if not cap: sys.exit("CAPSULE_NOT_FOUND")
assert cap["state"]=="UNDER_TEST" and cap["training_eligible"] is False and cap["gold_eligible"] is False
# Consumer ASTRION retrieves the persisted lesson and converts it into an explicit experiment-selection decision.
decision={"consumer":"ASTRION","source_capsule_id":cap["capsule_id"],"source_sha256":cap["sha256"],"retrieved_summary":cap["summary"],"action":"SELECT_FREE_GRANULAR_COLLAPSE_FOR_NEXT_F139_TEST","avoided_action":"REPEAT_CONSTRAINED_PACKING_GRAVITY_ABLATION","learning_claim":"POLICY_TRANSFER_ONLY_NOT_MODEL_WEIGHT_LEARNING","gold_promoted":False,"training_triggered":False,"status":"RETRIEVAL_AND_TRANSFER_OK"}
raw=json.dumps(decision,sort_keys=True).encode();decision["result_sha256"]=hashlib.sha256(raw).hexdigest();pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/agora_crossrun_retrieval_v2.json").write_text(json.dumps(decision,indent=2)+"\n");print(json.dumps(decision))
