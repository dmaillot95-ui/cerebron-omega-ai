#!/usr/bin/env python3
import argparse,glob,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

TAX={
 "SIMULATION_NE_REPRESENTATIVE_VALIDATION":[r"simulation.*not.*valid",r"digital twin.*not.*valid",r"simulation.*alone",r"model.*not.*physical"],
 "SUBSYSTEM_TEST_NE_INTEGRATED_SYSTEM_VALIDATION":[r"subsystem.*not.*system",r"bench.*not.*integrated",r"integrated system",r"system-level test"],
 "COMMON_CAUSE_DEPENDENCY":[r"common[- ]cause",r"shared sensor",r"shared software",r"shared power",r"correlat.*depend",r"single point"],
 "TRANSFER_LIMIT_FROM_SIMILAR_SYSTEMS":[r"similar system.*not.*transfer",r"analogous.*not.*same",r"transfer.*limit",r"different operating regime",r"external validity"],
 "EXTREME_OR_COMBINED_FAILURE_COVERAGE":[r"combined failure",r"degraded pump",r"extreme eclipse",r"fault injection",r"multiple failure"],
 "REPRESENTATIVE_ENVIRONMENT_TEST":[r"representative environment",r"thermal[- ]vacuum",r"environmental test",r"mission-representative",r"end-to-end test"],
 "METROLOGY_AND_ACCEPTANCE_CRITERIA":[r"acceptance criteria",r"metrology",r"measurement uncertainty",r"instrument calibration",r"pass/fail threshold"],
 "UNCERTAINTY_AND_MARGIN":[r"uncertaint",r"margin",r"sensitivity",r"error budget",r"confidence bound"],
 "MAINTENANCE_OR_HUMAN_VARIABILITY":[r"maintenance",r"operator",r"human variability",r"procedural variation"],
 "INFORMATION_GAIN_AND_STOP_RULE":[r"information gain",r"highest-value test",r"stop rule",r"stop testing",r"marginal gain",r"value of information"]
}
BAD=[
 r"digital twin .* proves .* ready",
 r"simulation .* validates representative operation",
 r"three .* benches .* validate .* integrated",
 r"500 .* hours .* proves? reliability",
 r"similar systems .* sufficient .* validation",
 r"shared .* (sensor|software|power) .* independent evidence"
]

def norm(x): return " ".join((x or "").lower().split())
def hits(text):
    t=norm(text)
    out=[]
    for k,pats in TAX.items():
        if any(re.search(p,t) for p in pats): out.append(k)
    return out
def critical_bad(text):
    t=norm(text)
    return any(re.search(p,t) for p in BAD)
def summarize(recs):
    rows=[]; union=set()
    for w in recs:
        h=hits(w.get("raw_output","")); union.update(h)
        bad=critical_bad(w.get("raw_output",""))
        executed=bool(w.get("llm_inference") and w.get("inference")=="PASS")
        spiralix=bool(w.get("spiralix_envelope_sha256"))
        parsed=bool(w.get("parse_ok"))
        clean=not bool(w.get("prompt_echo"))
        rows.append({
          "worker_id":w["worker_id"],"parent_ai":w["parent_ai"],"role_id":w["role_id"],
          "executed":executed,"spiralix":spiralix,"parsed":parsed,"clean":clean,
          "critical_error":bad,"findings":h,"finding_count":len(h)
        })
    return {
      "rows":rows,
      "executed":sum(r["executed"] for r in rows),
      "spiralix":sum(r["spiralix"] for r in rows),
      "parsed":sum(r["parsed"] for r in rows),
      "clean":sum(r["clean"] for r in rows),
      "critical_errors":sum(r["critical_error"] for r in rows),
      "finding_union":sorted(union),
      "finding_count":len(union)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--wave-a-glob",required=True)
    ap.add_argument("--wave-b-glob",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    cfg=json.loads((ROOT/"config/s10-marginal-gain-mission-v1.json").read_text())
    a=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.wave_a_glob,recursive=True)],key=lambda x:x["worker_id"])
    b=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.wave_b_glob,recursive=True)],key=lambda x:x["worker_id"])
    A=summarize(a); B=summarize(b)
    au=set(A["finding_union"]); bu=set(B["finding_union"])
    new=sorted(bu-au)
    b_rows=[]
    useful=0
    for row in B["rows"]:
        new_by_worker=sorted(set(row["findings"])-au)
        row=dict(row)
        row["new_findings_vs_wave_A"]=new_by_worker
        row["marginally_useful"]=len(new_by_worker)>0 and not row["critical_error"] and row["executed"] and row["spiralix"]
        useful+=int(row["marginally_useful"])
        b_rows.append(row)
    B["rows"]=b_rows
    all_receipts=a+b
    lineage={w.get("lineage_fingerprint") for w in all_receipts if w.get("lineage_fingerprint")}
    independent_evidence_count=0
    correlated_count=len(all_receipts)
    passed=(
      A["executed"]==5 and B["executed"]==5 and
      A["spiralix"]==5 and B["spiralix"]==5 and
      A["critical_errors"]==0 and B["critical_errors"]==0 and
      len(new)>=cfg["pass_gate"]["extension_min_new_findings"] and
      useful>=cfg["pass_gate"]["extension_min_useful_workers"]
    )
    stop="MARGINAL_GAIN_POSITIVE" if passed else "STAY_AT_5_NO_SUFFICIENT_MARGINAL_GAIN"
    out={
      "schema":"CEREBRON_S10_MARGINAL_GAIN_SCORE_V1",
      "run_id":args.run_id,
      "mission_id":cfg["mission_id"],
      "wave_A":A,
      "wave_B":B,
      "new_findings_from_wave_B":new,
      "new_finding_count":len(new),
      "extension_useful_workers":useful,
      "selected_count":10,
      "executed_count":A["executed"]+B["executed"],
      "useful_count":A["executed"]+useful,
      "correlated_count":correlated_count,
      "unique_lineage_fingerprints":len(lineage),
      "independent_evidence_count":independent_evidence_count,
      "marginal_gain_positive":passed,
      "scale_decision":"ELIGIBLE_FOR_CONTROLLED_S10_STAGE" if passed else "STAY_AT_5",
      "stop_reason":stop,
      "gvl_selection":cfg["gvl_selection"],
      "gold_status":"DENY",
      "training_status":"NO_TRAINING"
    }
    env=make_envelope(
      "F168-TAU:A2_ANALYST","AGORA",cfg["mission_id"],"AUDIT",
      f"S10 marginal gain positive={passed}; new_findings={len(new)}; useful_extension_workers={useful}; independent_evidence=0.",
      problem_ref="S10_MARGINAL_INFORMATION_GAIN",evidence_level="E2",confidence=1.0,
      risk=0.2 if passed else 0.6,
      dependencies=[w.get("spiralix_envelope_sha256") for w in all_receipts if w.get("spiralix_envelope_sha256")],
      json_payload={k:v for k,v in out.items() if k not in {"wave_A","wave_B"}}
    )
    out["spiralix_audit_envelope"]=env
    out["spiralix_audit_envelope_sha256"]=sha256_obj(env)
    out["score_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="score_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "wave_A_findings":A["finding_count"],"wave_B_findings":B["finding_count"],
      "new_findings":len(new),"extension_useful_workers":useful,
      "marginal_gain_positive":passed,"scale_decision":out["scale_decision"],
      "independent_evidence_count":0
    },sort_keys=True))

if __name__=="__main__":
    main()
