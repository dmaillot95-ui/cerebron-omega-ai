#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

REQ=pathlib.Path("config/afah-saphea-g1-promotion-request.json")
OUT=pathlib.Path("receipts/training/afah-saphea-g1-promotion-v1.json")
PROMO=pathlib.Path("config/saphea-g1-epistemic-adapter-v1.json")

def fetch_json(repo:str,commit:str,path:str):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        raw=r.read()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    req=json.loads(REQ.read_text())
    contract=json.loads(pathlib.Path("training/SAPHEA_FIRST_ADAPTER_CONTRACT.json").read_text())

    src=req["source"]
    training,tsha=fetch_json(src["repo"],src["commit"],src["training_receipt"])
    transfer,xsha=fetch_json(src["repo"],src["commit"],src["transfer_receipt"])
    audit,asha=fetch_json(src["repo"],src["commit"],src["counter_audit_receipt"])

    f72cfg=req["f72"]
    f72,f72sha=fetch_json(f72cfg["repo"],f72cfg["commit"],f72cfg["receipt"])

    checks={}
    checks["p03_unified_recall_pass"]=contract.get("p03_evidence",{}).get("status")=="PASS"
    checks["real_training_required"]=contract["execution"]["real_training_required"] is True
    checks["base_immutable"]=contract["scope"]["base_model_policy"]=="IMMUTABLE_G0"
    checks["weights_changed"]=training.get("weights_changed") is True
    checks["hf_artifact_write_read_pass"]=training.get("hf_private_readback_sha_pass") is True
    checks["adapter_sha_present"]=training.get("adapter_sha256")==req["expected_adapter_sha256"]
    checks["cold_gain_positive"]=(training.get("cold_gain") or 0)>0
    checks["m6_deny_training"]=training.get("m6_deny_training") is True
    checks["transfer_gain_positive"]=(transfer.get("transfer_gain") or 0)>0
    checks["transfer_frozen"]=transfer.get("transfer_deny_training") is True
    checks["transfer_disjoint"]=transfer.get("prompt_overlap_with_gold_m6")==0 and transfer.get("id_overlap_with_gold_m6")==0
    checks["ablation_supports_value"]=transfer.get("ablation_supports_value") is True
    checks["no_critical_regression"]=transfer.get("critical_regression") is False
    checks["counter_audit_pass"]=audit.get("counter_audit_pass") is True
    checks["red_team_pass"]=audit.get("redteam_pass") is True
    checks["internal_independent_codepath_pass"]=audit.get("independent_codepath_reproduction_pass") is True
    checks["external_independence_not_overclaimed"]="not external independent" in str(audit.get("independence_note","")).lower()
    checks["f72_review_pass"]=f72.get("review_pass") is True
    checks["f72_supported_e2"]=f72.get("evidence_status")=="SUPPORTED" and f72.get("evidence_level")=="E2"
    checks["f72_routes_to_afah"]=f72.get("route")=="AFAH_SCOPED_PROMOTION_REVIEW"

    all_pass=all(checks.values())
    decision="PROMOTE_SCOPED_G7" if all_pass else "HOLD_OR_ROLLBACK"
    promotion={
      "schema":"SAPHEA_G1_EPISTEMIC_ADAPTER_PROMOTION_V1",
      "ai_id":"SAPHEA",
      "generation":"G1",
      "scope":"CEREBRON_EPISTEMIC_STATUS_CLASSIFICATION_ONLY",
      "state":"SCOPED_G7_PROMOTED" if all_pass else "NOT_PROMOTED",
      "base_model":{
        "id":training["base_model_id"],
        "revision":training["base_revision"],
        "immutable":True
      },
      "adapter":{
        "sha256":training["adapter_sha256"],
        "config_sha256":training["adapter_config_sha256"],
        "private_repo":training["hf_private_repo"],
        "private_object_prefix":training["hf_private_object_prefix"]
      },
      "routing":{
        "mode":"SCOPED_OPT_IN",
        "allowed_task":"epistemic-status-classification",
        "general_default":False
      },
      "rollback":{
        "target":"G0_BASE_MODEL_NO_ADAPTER",
        "automatic_on_critical_regression":True
      },
      "evidence":{
        "training_run":training["run_id"],
        "cold_baseline":training["baseline_m6_score"],
        "cold_posttrain":training["posttrain_m6_score"],
        "transfer_run":transfer["run_id"],
        "transfer_base":transfer["base_score"],
        "transfer_adapter":transfer["adapter_score"],
        "counter_audit_run":audit["run_id"],
        "f72_run":f72cfg["run_id"],
        "f72_status":f72["evidence_status"],
        "f72_level":f72["evidence_level"]
      },
      "claim_ceiling":"SCOPED_EPISTEMIC_CLASSIFICATION_G7_SUPPORTED_E2",
      "external_independent_reproduction":"NOT_PRESENT",
      "no_general_capability_claim":True
    }

    receipt={
      "schema":"AFAH_SAPHEA_G1_PROMOTION_REVIEW_V1",
      "authority":"AFAH",
      "authority_mode":"DETERMINISTIC_POLICY_GATE_NOT_DEDICATED_AFAH_MODEL_INFERENCE",
      "checks":checks,
      "all_required_gates_pass":all_pass,
      "decision":decision,
      "promotion":promotion if all_pass else None,
      "source_content_sha256":{
        "training":tsha,"transfer":xsha,"counter_audit":asha,"f72":f72sha
      },
      "limitations":[
        "No external independent scientific reproduction.",
        "All capability evidence is scoped to synthetic epistemic-status classification.",
        "Promotion does not modify immutable base weights.",
        "Promotion does not imply general SAPHEA intelligence or generalization."
      ]
    }
    canon=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    receipt["review_sha256"]=hashlib.sha256(canon).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    if all_pass:
        PROMO.write_text(json.dumps(promotion,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "decision":decision,
      "all_required_gates_pass":all_pass,
      "review_sha256":receipt["review_sha256"],
      "claim_ceiling":promotion["claim_ceiling"] if all_pass else None
    },sort_keys=True))

if __name__=="__main__":
    main()
