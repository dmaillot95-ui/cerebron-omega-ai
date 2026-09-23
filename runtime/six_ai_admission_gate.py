#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path

VALIDATED={"GOLD_VALIDATED","RED_VALIDATED"}
FINAL={"GOLD_VALIDATED","RED_VALIDATED","SILVER","OPEN","REJECT"}

def fail(reason, rec):
    return {"schema":"six-ai-admission-receipt-v1","record_id":rec.get("record_id"),"decision":"REJECT","admitted":False,"reason":reason}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); rec=json.loads(Path(a.candidate).read_text())
    required=["record_id","source_ai","task_id","payload_sha256","provenance","dependency_fingerprint","audit_receipts","f72_receipt","requested_classification"]
    missing=[k for k in required if not rec.get(k)]
    if missing: out=fail("MISSING:"+",".join(missing),rec)
    elif rec["source_ai"] not in {"SAPHEA","SPIRALION","ETHERION","HYPERION","AFAH","CEREBRON"}: out=fail("UNKNOWN_SOURCE_AI",rec)
    elif rec["requested_classification"] not in FINAL: out=fail("INVALID_CLASSIFICATION",rec)
    else:
      ar=rec["audit_receipts"]
      checks={
       "audit":bool(ar.get("audit_pass")),
       "counter_audit":bool(ar.get("counter_audit_pass")),
       "clean_reproduction":bool(ar.get("clean_reproduction_pass")),
       "provenance":bool(rec.get("provenance")),
       "dependency":bool(rec.get("dependency_fingerprint")),
       "f72":bool(rec["f72_receipt"].get("pass")),
       "no_benchmark_leakage":not bool(rec.get("benchmark_leakage",False))
      }
      wanted=rec["requested_classification"]
      admitted=wanted in VALIDATED and all(checks.values())
      decision=wanted if admitted else ("REJECT" if wanted in VALIDATED else wanted)
      out={"schema":"six-ai-admission-receipt-v1","record_id":rec["record_id"],"source_ai":rec["source_ai"],
       "decision":decision,"admitted":admitted,"checks":checks,
       "payload_sha256":rec["payload_sha256"],"dependency_fingerprint":rec["dependency_fingerprint"],
       "claim_scope":"Admission gate result only; admitted means dataset-eligible, not trained or scientifically universal."}
      if wanted in VALIDATED and not admitted: out["reason"]="VALIDATION_GATE_FAILED"
    raw=(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n").encode()
    out["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out))
    if rec.get("requested_classification") in VALIDATED and not out["admitted"]: raise SystemExit(3)
if __name__=="__main__": main()
