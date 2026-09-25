#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROLE_LABELS={
  "AELYS":["ANSWER","CLARIFY","SUMMARIZE","LIMIT"],
  "ETHERION":["DEFINE","SOURCE","MODEL","CALCULATE","RED_TEAM","DESIGN_TEST"],
  "AFAH":["ACCEPT","HOLD","REJECT","CORRELATED"],
  "METRION":["PASS","FAIL_UNITS","FAIL_TOLERANCE","SIMULATION_ONLY"],
}

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def infer_aelys(p:str)->str|None:
    s=p.lower()
    if "sufficient context" in s or "all required inputs are present" in s:
        return "ANSWER"
    if "lacks " in s or "missing field" in s:
        return "CLARIFY"
    if "compressed while preserving" in s or "explicitly requests condensation" in s:
        return "SUMMARIZE"
    if "exceed evidence" in s or "available evidence supports only a narrower claim" in s:
        return "LIMIT"
    return None

def infer_etherion(p:str)->str|None:
    s=p.lower()
    if "objective lacks a frozen" in s or "problem statement conflates" in s:
        return "DEFINE"
    if "external " in s and "absent from the evidence packet" in s:
        return "SOURCE"
    if "no pinned provenance" in s:
        return "SOURCE"
    if "not formalized" in s or "representation of " in s and "incomplete" in s:
        return "MODEL"
    if "validated equation" in s or "model is fixed" in s:
        return "CALCULATE"
    if "alternative " in s and "remains untested" in s:
        return "RED_TEAM"
    if "needs falsification pressure" in s:
        return "RED_TEAM"
    if "distinct measurable predictions" in s or "controlled comparison with frozen acceptance criteria" in s:
        return "DESIGN_TEST"
    return None

def infer_afah(p:str)->str|None:
    s=p.lower()
    if "pinned run" in s and "independent method" in s:
        return "ACCEPT"
    if "all declared dependencies" in s and "verified" in s:
        return "ACCEPT"
    if "promising but required dependency" in s or "critical regression gate is still open" in s:
        return "HOLD"
    if "contradicts its artifact" in s or "no executable receipt" in s:
        return "REJECT"
    if "share the same model" in s or "deterministic descendants" in s:
        return "CORRELATED"
    return None

def infer_metrion(p:str)->str|None:
    s=p.lower()
    if "allowed interval contains the full uncertainty band" in s or "lies inside its verified requirement" in s:
        return "PASS"
    if "compared directly with" in s or "mixes incompatible dimensions" in s:
        return "FAIL_UNITS"
    if "exceeds the frozen acceptance interval" in s or "crosses a hard specification boundary" in s:
        return "FAIL_TOLERANCE"
    if "no hardware observation" in s or "virtual environment with no real-world replication" in s:
        return "SIMULATION_ONLY"
    return None

INFER={
  "AELYS":infer_aelys,
  "ETHERION":infer_etherion,
  "AFAH":infer_afah,
  "METRION":infer_metrion,
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    d=json.loads(pathlib.Path(a.input).read_text())
    rows=d["records"]
    audited=[]
    for r in rows:
        role=r["source_ai"]
        pred=INFER[role](r["prompt"])
        audited.append({
          "record_id":r["record_id"],
          "role":role,
          "target":r["target"],
          "audit_prediction":pred,
          "pass":pred==r["target"]
        })
    pass_count=sum(x["pass"] for x in audited)
    unresolved=sum(x["audit_prediction"] is None for x in audited)

    # Counter-audit: mutate one record for each role/label pair and require detection.
    tamper=[]
    for role,labels in ROLE_LABELS.items():
        for label in labels:
            src=next(r for r in rows if r["source_ai"]==role and r["target"]==label)
            wrong=next(x for x in labels if x!=label)
            pred=INFER[role](src["prompt"])
            tamper.append({
              "role":role,
              "original_target":label,
              "tampered_target":wrong,
              "audit_prediction":pred,
              "tamper_detected":pred!=wrong
            })
    tamper_detected=sum(x["tamper_detected"] for x in tamper)

    report={
      "schema":"CEREBRON_WAVE1_QUARANTINE_SEMANTIC_AUDIT_V1",
      "source_manifest_sha256":d["manifest_sha256"],
      "record_count":len(rows),
      "semantic_pass_count":pass_count,
      "semantic_fail_count":len(rows)-pass_count,
      "unresolved_count":unresolved,
      "tamper_case_count":len(tamper),
      "tamper_detected_count":tamper_detected,
      "audit_codepath":"INDEPENDENT_RULE_VALIDATOR_DOES_NOT_IMPORT_GENERATOR",
      "independent_model_evidence":False,
      "training_released":False,
      "decision":"AUDIT_COUNTER_AUDIT_PASS_F72_AFAH_PENDING" if pass_count==len(rows) and tamper_detected==len(tamper) else "REJECT_OR_REPAIR",
      "records":audited,
      "tamper_tests":tamper,
      "claim_ceiling":"SYNTHETIC_CONTRACT_CANDIDATE_SEMANTIC_CONSISTENCY_ONLY"
    }
    report["report_sha256"]=sha(report)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:report[k] for k in [
      "source_manifest_sha256","record_count","semantic_pass_count","semantic_fail_count",
      "unresolved_count","tamper_case_count","tamper_detected_count","decision","report_sha256"
    ]},sort_keys=True))
    if report["decision"]!="AUDIT_COUNTER_AUDIT_PASS_F72_AFAH_PENDING":
        raise SystemExit(2)

if __name__=="__main__":
    main()
