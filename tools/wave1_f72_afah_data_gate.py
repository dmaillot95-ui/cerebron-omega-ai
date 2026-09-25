#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--audit",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    cand=json.loads(pathlib.Path(a.candidates).read_text())
    audit=json.loads(pathlib.Path(a.audit).read_text())

    checks={
      "record_count_432":cand.get("record_count")==432,
      "candidate_state_quarantine":cand.get("state")=="QUARANTINE",
      "candidate_training_released_false":cand.get("training_released") is False,
      "benchmark_records_excluded":cand.get("benchmark_records_included") is False,
      "audit_source_matches":audit.get("source_manifest_sha256")==cand.get("manifest_sha256"),
      "semantic_pass_432":audit.get("semantic_pass_count")==432,
      "semantic_fail_zero":audit.get("semantic_fail_count")==0,
      "unresolved_zero":audit.get("unresolved_count")==0,
      "tamper_all_detected":audit.get("tamper_detected_count")==audit.get("tamper_case_count"),
      "audit_decision_pass":audit.get("decision")=="AUDIT_COUNTER_AUDIT_PASS_F72_AFAH_PENDING",
      "all_candidates_nontrainable":all(r.get("training_eligible") is False for r in cand.get("records",[])),
      "all_candidates_quarantine":all(r.get("state")=="QUARANTINE" for r in cand.get("records",[])),
      "all_provenance_present":all(bool(r.get("provenance")) for r in cand.get("records",[])),
      "all_dependency_fingerprint_present":all(bool(r.get("dependency_fingerprint")) for r in cand.get("records",[])),
      "all_sha_present":all(bool(r.get("payload_sha256")) for r in cand.get("records",[])),
    }
    f72_pass=all(checks.values())

    # AFAH deterministic admission gate: F72 can approve structural/semantic
    # admission to a versioned candidate dataset, but cannot convert synthetic
    # contract candidates into empirical/scientific truth.
    role_counts=cand.get("roles",{})
    afah_checks={
      "f72_pass":f72_pass,
      "role_counts_expected":role_counts=={"AELYS":96,"ETHERION":144,"AFAH":96,"METRION":96},
      "synthetic_provenance_declared":all(
        r.get("provenance",{}).get("kind")=="DETERMINISTIC_CONTRACT_SYNTHETIC_CANDIDATE"
        for r in cand.get("records",[])
      ),
      "benchmark_leakage_denied":cand.get("benchmark_records_included") is False,
      "no_auto_promotion":True,
    }
    afah_pass=all(afah_checks.values())

    if f72_pass and afah_pass:
        decision="ADMIT_AS_SYNTHETIC_GOLD_CANDIDATE_POOL_NOT_TRAINING_RELEASED"
    else:
        decision="HOLD_OR_REJECT"

    report={
      "schema":"CEREBRON_WAVE1_F72_AFAH_DATA_GATE_V1",
      "source_manifest_sha256":cand.get("manifest_sha256"),
      "source_audit_sha256":audit.get("report_sha256"),
      "f72_checks":checks,
      "f72_pass":f72_pass,
      "afah_checks":afah_checks,
      "afah_pass":afah_pass,
      "decision":decision,
      "training_released":False,
      "admission_class":"SYNTHETIC_CONTRACT_GOLD_CANDIDATE" if decision.startswith("ADMIT") else "NONE",
      "requires_before_training_release":[
        "VERSIONED_ROLE_SPLITS",
        "FRESH_BLIND_M6_PER_ROLE",
        "TRANSFER_SPLIT",
        "ADVERSARIAL_SPLIT",
        "NO_BENCHMARK_LEAKAGE",
        "ROLE_SPECIFIC_BASELINE_RECEIPT",
      ],
      "claim_ceiling":"DATA_CONTRACT_ADMISSION_ONLY_NOT_EMPIRICAL_TRUTH_NOT_MODEL_TRAINING",
    }
    report["report_sha256"]=h(report)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "f72_pass":f72_pass,"afah_pass":afah_pass,"decision":decision,
      "source_manifest_sha256":report["source_manifest_sha256"],
      "report_sha256":report["report_sha256"]
    },sort_keys=True))
    if not (f72_pass and afah_pass):
        raise SystemExit(2)

if __name__=="__main__":
    main()
