#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, pathlib

LABELS={
 "SPIRALION":["CONTINUE","ISOLATE_CONTRADICTION","COMPRESS","VERIFY_NEXT"],
 "HYPERION":["ALTERNATIVE","COUNTERFACTUAL","MECHANISM","DIVERSIFY"],
 "ASTRION":["REQUIREMENTS","PHYSICS_MODEL","CALCULATE","TEST"],
 "SAPHEA_MICRO":["ROUTE","MATH","CODE","RESEARCH","INVENT","RED_TEAM","FUSION"]
}

def sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def infer(role,p):
    s=p.lower()
    if role=="SPIRALION":
        if ("direct continuation" in s or "no contradiction=true" in s) and "blocked=true" not in s:return "CONTINUE"
        if "conclusions conflict=true" in s or "violates verified invariant" in s:return "ISOLATE_CONTRADICTION"
        if "duplicate summaries" in s or "repeated facts=true" in s:return "COMPRESS"
        if "unverified item=" in s or "cold receipt missing=true" in s:return "VERIFY_NEXT"
    if role=="HYPERION":
        if "distinct plausible explanation" in s or "materially different route" in s:return "ALTERNATIVE"
        if "hypothetical" in s or "assumption=" in s and "reversed" in s:return "COUNTERFACTUAL"
        if "causal process" in s or "causal chain" in s:return "MECHANISM"
        if "orthogonal families" in s or "non-overlapping candidate generation" in s:return "DIVERSIFY"
    if role=="ASTRION":
        if "acceptance criteria incomplete=true" in s or "lacks frozen duty cycle" in s:return "REQUIREMENTS"
        if "governing relation" in s or "physical model" in s and "missing" in s:return "PHYSICS_MODEL"
        if "validated equation=true" in s or "model frozen=true" in s:return "CALCULATE"
        if "hardware evidence missing=true" in s or "operational claim blocked" in s:return "TEST"
    if role=="SAPHEA_MICRO":
        if "specialist coalition" in s or "specialist routing" in s:return "ROUTE"
        if "formal symbolic proof" in s or "derivation of identity" in s:return "MATH"
        if "traceback present=true" in s or "parser implementation" in s:return "CODE"
        if "current external source" in s or "authoritative retrieval" in s:return "RESEARCH"
        if "novel architecture" in s or "generative design" in s:return "INVENT"
        if "counterexample search" in s or "falsification" in s:return "RED_TEAM"
        if "without double-counting evidence" in s or "dependency-preserving decision" in s:return "FUSION"
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--baseline-config",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    d=json.loads(pathlib.Path(a.input).read_text())
    b=json.loads(pathlib.Path(a.baseline_config).read_text())
    bench=set()
    for role,spec in b["roles"].items():
        for row in spec["tasks"]: bench.add(row[2].strip())

    exact_overlap=[r["record_id"] for r in d["records"] if r["prompt"].strip() in bench]
    rows=[]
    for r in d["records"]:
        pred=infer(r["source_ai"],r["prompt"])
        rows.append({"record_id":r["record_id"],"role":r["source_ai"],"target":r["target"],"prediction":pred,"pass":pred==r["target"]})
    pass_count=sum(x["pass"] for x in rows)
    unresolved=sum(x["prediction"] is None for x in rows)

    tamper=[]
    for role,labels in LABELS.items():
        for label in labels:
            src=next(r for r in d["records"] if r["source_ai"]==role and r["target"]==label)
            wrong=next(x for x in labels if x!=label)
            pred=infer(role,src["prompt"])
            tamper.append({"role":role,"original":label,"tampered":wrong,"prediction":pred,"detected":pred!=wrong})
    detected=sum(x["detected"] for x in tamper)

    decision="AUDIT_COUNTER_AUDIT_PASS_F72_PENDING" if pass_count==len(rows) and unresolved==0 and not exact_overlap and detected==len(tamper) else "REJECT_OR_REPAIR"
    out={
      "schema":"CEREBRON_WAVE2_QUARANTINE_SEMANTIC_AUDIT_V1",
      "source_manifest_sha256":d["manifest_sha256"],
      "record_count":len(rows),
      "semantic_pass_count":pass_count,
      "semantic_fail_count":len(rows)-pass_count,
      "unresolved_count":unresolved,
      "exact_baseline_prompt_overlap_count":len(exact_overlap),
      "tamper_case_count":len(tamper),
      "tamper_detected_count":detected,
      "training_released":False,
      "independent_model_evidence":False,
      "audit_codepath":"INDEPENDENT_RULE_VALIDATOR_DOES_NOT_IMPORT_GENERATOR",
      "decision":decision,
      "rows":rows,
      "tamper_tests":tamper,
      "claim_ceiling":"SYNTHETIC_CONTRACT_CANDIDATE_SEMANTIC_CONSISTENCY_ONLY"
    }
    out["report_sha256"]=sha(out)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:out[k] for k in ["record_count","semantic_pass_count","semantic_fail_count","unresolved_count","exact_baseline_prompt_overlap_count","tamper_case_count","tamper_detected_count","decision","report_sha256"]},sort_keys=True))
    if decision!="AUDIT_COUNTER_AUDIT_PASS_F72_PENDING": raise SystemExit(2)

if __name__=="__main__":
    main()
