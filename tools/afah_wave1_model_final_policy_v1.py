#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

REQ=pathlib.Path("config/afah-wave1-model-final-review-request.json")
OUT=pathlib.Path("receipts/wave1/afah-wave1-model-final-review-v1.json")
POINTER=pathlib.Path("config/afah-wave1-research-adapter-v1.json")

def fetch_json(repo:str,commit:str,path:str):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        raw=r.read()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    req=json.loads(REQ.read_text())
    src=req["source"]
    receipt,rsha=fetch_json(src["repo"],src["commit"],src["role_receipt"])
    audit,asha=fetch_json(src["repo"],src["commit"],src["canonical_audit"])
    fcfg=req["f72"]
    f72,fsha=fetch_json(fcfg["repo"],fcfg["commit"],fcfg["receipt"])

    checks={}
    checks["role_afah"]=receipt.get("role")=="AFAH"
    checks["training_real"]=receipt.get("real_training") is True and receipt.get("training_executed") is True
    checks["weights_changed"]=receipt.get("weights_changed") is True
    checks["hf_private_readback"]=receipt.get("hf_private_readback_sha_pass") is True
    checks["cold_deny_training"]=receipt.get("cold_deny_training") is True
    checks["validation_gate"]=receipt.get("validation_gate_pass") is True
    checks["cold_gate"]=receipt.get("cold_gate_pass") is True
    checks["no_critical_regression"]=receipt.get("any_critical_regression") is False
    gains=receipt.get("gains",{})
    checks["cold_gains"]=(gains.get("M6",0)>0 and gains.get("TRANSFER",0)>0 and gains.get("RED",0)>=0)
    checks["not_pre_promoted"]=receipt.get("promotion")=="NOT_PROMOTED"
    checks["canonical_single_candidate"]=audit.get("candidate_roles")==["AFAH"] and audit.get("g6_candidate_count")==1
    checks["canonical_three_rollbacks"]=audit.get("rollback_count")==3
    checks["correlation_declared"]=audit.get("unique_base_lineage_count")==1 and audit.get("independent_evidence_count")==0

    checks["f72_farm"]=f72.get("farm_id")==72
    checks["f72_role"]=f72.get("role")=="AFAH"
    checks["f72_supported"]=f72.get("review_pass") is True and f72.get("evidence_status")=="SUPPORTED" and f72.get("evidence_level")=="E2"
    checks["f72_adapter_match"]=f72.get("adapter_sha256")==receipt.get("adapter_sha256")
    checks["f72_candidate_not_reviewer"]=f72.get("candidate_adapter_used_for_review") is False
    checks["f72_route"]=f72.get("route")=="AFAH_POLICY_FINAL_REVIEW"

    all_pass=all(checks.values())
    decision="G6_VERIFIED_RESEARCH_ONLY" if all_pass else "HOLD_OR_ROLLBACK"
    pointer={
      "schema":"AFAH_WAVE1_RESEARCH_ADAPTER_POINTER_V1",
      "role":"AFAH",
      "state":decision if all_pass else "INACTIVE",
      "adapter_sha256":receipt.get("adapter_sha256") if all_pass else None,
      "adapter_config_sha256":receipt.get("adapter_config_sha256") if all_pass else None,
      "hf_private_repo":receipt.get("hf_private_repo") if all_pass else None,
      "hf_private_object_prefix":receipt.get("hf_private_object_prefix") if all_pass else None,
      "runtime_activation":False,
      "default_runtime":False,
      "g7_promoted":False,
      "research_use_only":True,
      "claim_ceiling":"SCOPED_SYNTHETIC_EVIDENCE_CLASSIFICATION_G6_RESEARCH_ONLY"
    }
    out={
      "schema":"AFAH_WAVE1_MODEL_FINAL_POLICY_REVIEW_V1",
      "authority":"AFAH_POLICY_GATE",
      "authority_mode":"DETERMINISTIC_POLICY_GATE_NOT_CANDIDATE_MODEL_INFERENCE",
      "candidate_adapter_used_for_final_review":False,
      "checks":checks,
      "all_required_gates_pass":all_pass,
      "decision":decision,
      "pointer":pointer if all_pass else None,
      "source_content_sha256":{"role_receipt":rsha,"canonical_audit":asha,"f72":fsha},
      "limitations":[
        "The trained AFAH adapter was not used to judge itself.",
        "Evidence is synthetic and task-scoped.",
        "Wave1 roles share a base-model lineage and do not provide four independent confirmations.",
        "G6 research status does not imply general AFAH capability or runtime superiority."
      ],
      "g7_requirements":[
        "materially new held-out transfer family",
        "repeat stability without critical per-label regression",
        "independent or materially distinct reviewer/model lineage",
        "explicit runtime ablation versus current default before any activation"
      ]
    }
    canon=json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    out["review_sha256"]=hashlib.sha256(canon).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    if all_pass:
        POINTER.parent.mkdir(parents=True,exist_ok=True)
        POINTER.write_text(json.dumps(pointer,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "decision":decision,
      "all_required_gates_pass":all_pass,
      "runtime_activation":False,
      "g7_promoted":False,
      "review_sha256":out["review_sha256"]
    },sort_keys=True))
    if not all_pass:
        raise SystemExit(2)

if __name__=="__main__":
    main()
