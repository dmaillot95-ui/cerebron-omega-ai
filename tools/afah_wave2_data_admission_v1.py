#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,urllib.request

REQ=pathlib.Path("config/afah-wave2-data-admission-request.json")
OUT=pathlib.Path("receipts/wave2/afah-wave2-data-admission-v1.json")
POINTER=pathlib.Path("training/WAVE2_DATA_ADMISSION_V1.json")

def fetch(repo,commit,path):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        raw=r.read()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    req=json.loads(REQ.read_text())
    src=req["source"]
    baseline,bsha=fetch(src["repo"],src["baseline_commit"],src["baseline_receipt"])
    data,dsha=fetch(src["repo"],src["quarantine_commit"],src["quarantine_receipt"])
    fcfg=req["f72"]
    f72,fsha=fetch(fcfg["repo"],fcfg["commit"],fcfg["receipt"])
    manifest=req["expected_manifest_sha256"]

    checks={}
    checks["manifest_consistent"]=data.get("manifest_sha256")==f72.get("manifest_sha256")==manifest
    checks["baseline_real_four"]=baseline.get("receipt_count")==4 and baseline.get("real_inference_count")==4
    checks["baseline_training_zero"]=baseline.get("training_executed_count")==0
    checks["baseline_independent_zero"]=baseline.get("independent_evidence_count")==0
    checks["quarantine_456"]=data.get("record_count")==456 and data.get("semantic_pass_count")==456
    checks["quarantine_no_fail"]=data.get("semantic_fail_count")==0 and data.get("unresolved_count")==0
    checks["quarantine_tamper_pass"]=data.get("tamper_case_count")==19 and data.get("tamper_detected_count")==19
    checks["quarantine_no_baseline_overlap"]=data.get("exact_baseline_prompt_overlap_count")==0
    checks["quarantine_training_locked"]=data.get("training_released") is False
    checks["f72_farm"]=f72.get("farm_id")==72
    checks["f72_supported"]=f72.get("review_pass") is True and f72.get("evidence_status")=="SUPPORTED" and f72.get("evidence_level")=="E2"
    checks["f72_training_locked"]=f72.get("training_released") is False
    checks["f72_route"]=f72.get("route")=="AFAH_WAVE2_DATA_ADMISSION_REVIEW"

    ok=all(checks.values())
    decision="ADMIT_WAVE2_SYNTHETIC_CANDIDATE_POOL" if ok else "HOLD_OR_REJECT_WAVE2_POOL"
    admission={
      "schema":"CEREBRON_WAVE2_DATA_ADMISSION_V1",
      "state":"ADMITTED_SYNTHETIC_CANDIDATE_POOL" if ok else "NOT_ADMITTED",
      "manifest_sha256":manifest,
      "record_count":456 if ok else 0,
      "roles":{"SPIRALION":96,"HYPERION":96,"ASTRION":96,"SAPHEA_MICRO":168} if ok else {},
      "training_released":False,
      "allowed_next_steps":["VERSIONED_ROLE_SPLITS","FRESH_BLIND_M6","FRESH_TRANSFER","FRESH_ADVERSARIAL"] if ok else [],
      "forbidden":["BASELINE_TO_TRAIN","M6_TO_TRAIN","TRANSFER_TO_TRAIN","ADVERSARIAL_TO_TRAIN","AUTO_PROMOTION"],
      "claim_ceiling":"AUDITED_SYNTHETIC_CANDIDATE_DATA_ONLY_NOT_EMPIRICAL_GROUND_TRUTH_NOT_TRAINING_RELEASE"
    }
    out={
      "schema":"AFAH_WAVE2_DATA_ADMISSION_REVIEW_V1",
      "authority":"AFAH_POLICY_GATE",
      "authority_mode":"DETERMINISTIC_POLICY_GATE_NOT_DEDICATED_AFAH_MODEL_INFERENCE",
      "checks":checks,
      "all_required_gates_pass":ok,
      "decision":decision,
      "admission":admission if ok else None,
      "source_content_sha256":{"baseline":bsha,"quarantine":dsha,"f72":fsha},
      "limitations":[
        "Candidate records are deterministic synthetic contract data, not empirical ground truth.",
        "F72 is a real farm review but not external third-party validation.",
        "Training remains locked until fresh blind M6, transfer and adversarial suites are created and leakage-audited."
      ]
    }
    out["review_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    if ok:
        POINTER.parent.mkdir(parents=True,exist_ok=True)
        POINTER.write_text(json.dumps(admission,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"decision":decision,"all_required_gates_pass":ok,"training_released":False,"review_sha256":out["review_sha256"]},sort_keys=True))
    if not ok: raise SystemExit(2)
if __name__=="__main__":
    main()
