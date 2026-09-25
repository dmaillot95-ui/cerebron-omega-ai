#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,pathlib,urllib.request

REQ=pathlib.Path("config/afah-wave2-model-final-review-request.json")
OUT=pathlib.Path("receipts/wave2/afah-wave2-model-final-review-v1.json")
PTRDIR=pathlib.Path("config/wave2-research-adapters")

def fetch(repo,commit,path):
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:
        raw=r.read()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def main():
    req=json.loads(REQ.read_text())
    src=req["source"]; fcfg=req["f72"]
    audit,asha=fetch(src["repo"],src["commit"],src["canonical_audit"])
    f72,fsha=fetch(fcfg["repo"],fcfg["commit"],fcfg["receipt"])
    results={};all_pass=True;content_shas={"canonical_audit":asha,"f72":fsha}
    for c in req["candidates"]:
        role=c["role"]
        rec,rsha=fetch(src["repo"],src["commit"],c["receipt"])
        content_shas[role]=rsha
        f72r=f72.get("results",{}).get(role,{})
        checks={
          "role_match":rec.get("role")==role,
          "candidate_in_canonical":role in audit.get("candidate_roles",[]),
          "real_training":rec.get("real_training") is True and rec.get("training_executed") is True,
          "weights_changed":rec.get("weights_changed") is True,
          "hf_readback":rec.get("hf_private_readback_sha_pass") is True,
          "cold_gate":rec.get("cold_gate_pass") is True,
          "validation_gate":rec.get("validation_gate_pass") is True,
          "no_critical_regression":rec.get("any_critical_regression") is False,
          "f72_supported":f72r.get("review_pass") is True and f72r.get("evidence_status")=="SUPPORTED" and f72r.get("evidence_level")=="E2",
          "f72_adapter_match":f72r.get("adapter_sha256")==rec.get("adapter_sha256"),
          "candidate_not_self_reviewer":f72.get("candidate_adapters_used_for_review") is False,
          "not_pre_promoted":rec.get("promotion")=="NOT_PROMOTED"
        }
        ok=all(checks.values());all_pass=all_pass and ok
        pointer={
          "schema":"CEREBRON_WAVE2_RESEARCH_ADAPTER_POINTER_V1",
          "role":role,
          "state":"G6_VERIFIED_RESEARCH_ONLY" if ok else "INACTIVE",
          "adapter_sha256":rec.get("adapter_sha256") if ok else None,
          "adapter_config_sha256":rec.get("adapter_config_sha256") if ok else None,
          "hf_private_repo":rec.get("hf_private_repo") if ok else None,
          "hf_private_object_prefix":rec.get("hf_private_object_prefix") if ok else None,
          "runtime_activation":False,
          "default_runtime":False,
          "g7_promoted":False,
          "research_use_only":True,
          "claim_ceiling":"SCOPED_SYNTHETIC_ROLE_CLASSIFIER_G6_RESEARCH_ONLY"
        }
        results[role]={"checks":checks,"decision":"G6_VERIFIED_RESEARCH_ONLY" if ok else "HOLD_OR_ROLLBACK","pointer":pointer if ok else None}
        if ok:
            PTRDIR.mkdir(parents=True,exist_ok=True)
            (PTRDIR/f"{role.lower()}-v1.json").write_text(json.dumps(pointer,indent=2)+"\n")
    out={
      "schema":"AFAH_WAVE2_MODEL_FINAL_POLICY_REVIEW_V1",
      "authority":"AFAH_POLICY_GATE",
      "authority_mode":"DETERMINISTIC_POLICY_GATE_NOT_CANDIDATE_MODEL_INFERENCE",
      "candidate_adapters_used_for_final_review":False,
      "results":results,
      "all_requested_candidates_pass":all_pass,
      "source_content_sha256":content_shas,
      "runtime_activation":False,
      "g7_promoted":False,
      "independent_evidence_count":0,
      "limitations":[
        "Evidence remains synthetic and role-scoped.",
        "Two shared base-model lineages remain correlated.",
        "G6 research status is not runtime superiority or general capability."
      ]
    }
    out["review_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"all_requested_candidates_pass":all_pass,"roles":list(results),"review_sha256":out["review_sha256"]},sort_keys=True))
    if not all_pass: raise SystemExit(2)

if __name__=="__main__": main()
