#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

REQ=pathlib.Path("config/afah-wave1-data-admission-request.json")
OUT=pathlib.Path("receipts/wave1/afah-wave1-data-admission-v1.json")
POINTER=pathlib.Path("training/WAVE1_DATA_ADMISSION_V1.json")

def fetch_json(repo:str,commit:str,path:str):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        raw=r.read()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    req=json.loads(REQ.read_text())
    src=req["source"]
    build,bsha=fetch_json(src["repo"],src["commit"],src["build_receipt"])
    audit,asha=fetch_json(src["repo"],src["commit"],src["audit_receipt"])
    baseline,lsha=fetch_json(src["repo"],src["commit"],src["baseline_receipt"])

    fcfg=req["f72"]
    f72,fsha=fetch_json(fcfg["repo"],fcfg["commit"],fcfg["receipt"])

    manifest=req["expected_manifest_sha256"]
    checks={}
    checks["manifest_consistent"]=(build.get("manifest_sha256")==audit.get("source_manifest_sha256")==f72.get("manifest_sha256")==manifest)
    checks["build_training_locked"]=build.get("training_released") is False
    checks["audit_training_locked"]=audit.get("training_released") is False
    checks["audit_semantic_432"]=audit.get("semantic_pass_count")==432 and audit.get("semantic_fail_count")==0
    checks["audit_tamper_pass"]=audit.get("tamper_case_count")==audit.get("tamper_detected_count")==18
    checks["baseline_real_four"]=baseline.get("real_inference_count")==4 and baseline.get("receipt_count")==4
    checks["baseline_no_training"]=baseline.get("training_executed_count")==0
    checks["baseline_correlation_declared"]=baseline.get("unique_lineage_fingerprints")==1 and baseline.get("independent_evidence_count")==0
    checks["f72_farm_72"]=f72.get("farm_id")==72
    checks["f72_review_pass"]=f72.get("review_pass") is True
    checks["f72_supported_e2"]=f72.get("evidence_status")=="SUPPORTED" and f72.get("evidence_level")=="E2"
    checks["f72_training_locked"]=f72.get("training_released") is False
    checks["f72_route"]=f72.get("route")=="AFAH_WAVE1_DATA_ADMISSION_REVIEW"
    checks["claim_ceiling_scoped"]=f72.get("claim_ceiling")=="SUPPORTED_SCOPED_SYNTHETIC_DATA_CONTRACT_EVIDENCE"

    all_pass=all(checks.values())
    decision="ADMIT_SYNTHETIC_CANDIDATE_POOL" if all_pass else "HOLD_OR_REJECT_DATA_POOL"
    admission={
      "schema":"CEREBRON_WAVE1_DATA_ADMISSION_V1",
      "state":"ADMITTED_SYNTHETIC_CANDIDATE_POOL" if all_pass else "NOT_ADMITTED",
      "manifest_sha256":manifest,
      "record_count":432 if all_pass else 0,
      "roles":{"AELYS":96,"ETHERION":144,"AFAH":96,"METRION":96} if all_pass else {},
      "training_released":False,
      "allowed_next_steps":["VERSIONED_ROLE_SPLITS","FRESH_BLIND_M6","FRESH_TRANSFER","FRESH_ADVERSARIAL"] if all_pass else [],
      "forbidden":["DIRECT_TRAINING_FROM_BASELINE_BENCHMARK","TRAIN_ON_M6","TRAIN_ON_TRANSFER","TRAIN_ON_ADVERSARIAL","AUTO_PROMOTION"],
      "claim_ceiling":"AUDITED_SYNTHETIC_CANDIDATE_DATA_ONLY_NOT_EMPIRICAL_GROUND_TRUTH_NOT_TRAINING_RELEASE"
    }
    receipt={
      "schema":"AFAH_WAVE1_DATA_ADMISSION_REVIEW_V1",
      "authority":"AFAH",
      "authority_mode":"DETERMINISTIC_POLICY_GATE_NOT_DEDICATED_AFAH_MODEL_INFERENCE",
      "checks":checks,
      "all_required_gates_pass":all_pass,
      "decision":decision,
      "admission":admission if all_pass else None,
      "source_content_sha256":{"build":bsha,"audit":asha,"baseline":lsha,"f72":fsha},
      "limitations":[
        "Candidate records are deterministic synthetic contract data, not empirical ground truth.",
        "Semantic counter-audit is separate code path but not external independent evidence.",
        "AFAH admission does not release model training.",
        "Fresh blind M6, transfer and adversarial splits remain required before LoRA training."
      ]
    }
    canon=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    receipt["review_sha256"]=hashlib.sha256(canon).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    if all_pass:
        POINTER.parent.mkdir(parents=True,exist_ok=True)
        POINTER.write_text(json.dumps(admission,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "decision":decision,
      "all_required_gates_pass":all_pass,
      "review_sha256":receipt["review_sha256"],
      "training_released":False
    },sort_keys=True))
    if not all_pass:
        raise SystemExit(2)

if __name__=="__main__":
    main()
