#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
fb=json.loads((ROOT/"memory/failure-bank-v1.json").read_text())
rows={x["FAILURE_ID"]:x for x in fb["entries"] if x.get("FAILURE_CLASS")=="F_TRANSFER"}
required=[
 "FAIL-M43-SAPHEA-G7-CLASS-COLLAPSE-001",
 "FAIL-M43-SAPHEA-TRANSFER-001",
 "FAIL-WAVE1-AELYS-LORA-TRANSFER-001",
 "FAIL-WAVE1-ETHERION-LORA-TRANSFER-001",
 "FAIL-WAVE1-METRION-LORA-TRANSFER-001",
]
errors=[]
for rid in required:
    if rid not in rows:
        errors.append("MISSING_CASE:"+rid)

cases=[]

# Explicit measured cases from the failure bank. These are promotion-decision examples,
# not benchmark answers and not new model executions.
if not errors:
    cases.append({
      "id":"SAPHEA_G6",
      "validation_signal":"M6_GAIN_PLUS12",
      "cold_gain":12,
      "transfer_gain":20,
      "red_gain":0,
      "critical_regression":True,
      "recorded_decision":"ROLLBACK_OR_BLOCK",
      "source":"FAIL-M43-SAPHEA-G7-CLASS-COLLAPSE-001"
    })
    v3=rows["FAIL-M43-SAPHEA-TRANSFER-001"]["V3_EVIDENCE"]
    cases.append({
      "id":"SAPHEA_V3",
      "validation_signal":"VALIDATION_5_TO_12",
      "cold_gain":v3["m6_gain"],
      "transfer_gain":None,
      "red_gain":None,
      "critical_regression":bool(v3["validation_critical_regression"]),
      "recorded_decision":v3["decision"],
      "source":"FAIL-M43-SAPHEA-TRANSFER-001"
    })
    v4=rows["FAIL-M43-SAPHEA-TRANSFER-001"]["V4_EVIDENCE"]
    cases.append({
      "id":"SAPHEA_V4",
      "validation_signal":"VALIDATION_GATE_PASS",
      "cold_gain":v4["m6_gain"],
      "transfer_gain":None,
      "red_gain":None,
      "critical_regression":bool(v4["critical_regression"]),
      "recorded_decision":v4["decision"],
      "source":"FAIL-M43-SAPHEA-TRANSFER-001"
    })
    cases.extend([
      {
        "id":"AELYS_WAVE1","validation_gain":6,"cold_gain":0,"transfer_gain":-4,"red_gain":0,
        "critical_regression":True,"recorded_decision":"ROLLBACK_RETAIN_EVIDENCE",
        "source":"FAIL-WAVE1-AELYS-LORA-TRANSFER-001"
      },
      {
        "id":"ETHERION_WAVE1","validation_gain":9,"cold_gain":-2,"transfer_gain":-1,"red_gain":-2,
        "critical_regression":True,"recorded_decision":"ROLLBACK_RETAIN_EVIDENCE",
        "source":"FAIL-WAVE1-ETHERION-LORA-TRANSFER-001"
      },
      {
        "id":"METRION_WAVE1","validation_gain":9,"cold_gain":7,"transfer_gain":0,"red_gain":-2,
        "critical_regression":True,"recorded_decision":"ROLLBACK_RETAIN_EVIDENCE",
        "source":"FAIL-WAVE1-METRION-LORA-TRANSFER-001"
      }
    ])

def strict_gate(c):
    return (
      c.get("cold_gain") is not None and c["cold_gain"]>0
      and c.get("transfer_gain") is not None and c["transfer_gain"]>0
      and c.get("red_gain") is not None and c["red_gain"]>=0
      and c.get("critical_regression") is False
    )

for c in cases:
    c["strict_gate_promote"]=strict_gate(c)
    c["expected_reject"]=not c["strict_gate_promote"]

# Every recorded failure case must be rejected by the strict rule.
if any(c["strict_gate_promote"] for c in cases):
    errors.append("STRICT_GATE_FALSE_PROMOTION")

# The rule must also accept a synthetic boundary control only when every required condition is met.
positive_control={
  "id":"SYNTHETIC_BOUNDARY_CONTROL",
  "cold_gain":1,"transfer_gain":1,"red_gain":0,"critical_regression":False
}
negative_controls=[
  {"cold_gain":0,"transfer_gain":1,"red_gain":0,"critical_regression":False},
  {"cold_gain":1,"transfer_gain":0,"red_gain":0,"critical_regression":False},
  {"cold_gain":1,"transfer_gain":1,"red_gain":-1,"critical_regression":False},
  {"cold_gain":1,"transfer_gain":1,"red_gain":0,"critical_regression":True},
]
if not strict_gate(positive_control):
    errors.append("POSITIVE_CONTROL_REJECTED")
if any(strict_gate(x) for x in negative_controls):
    errors.append("NEGATIVE_CONTROL_ACCEPTED")

# Cross-case empirical statement: positive validation/M6 signals appeared in multiple cases that were rejected.
positive_signal_rejected=sum(
    1 for c in cases
    if (c.get("validation_gain",0)>0 or c.get("cold_gain",0)>0 or "PASS" in str(c.get("validation_signal","")))
    and c["expected_reject"]
)
if positive_signal_rejected < 4:
    errors.append("INSUFFICIENT_CROSS_CASE_SUPPORT")

lesson={
  "lesson_id":"LESSON-TRANSFER-PROMOTION-001",
  "title":"Validation gain alone cannot promote an adapter.",
  "invariant":"PROMOTION_REQUIRES_COLD_TRANSFER_REDTEAM_AND_NO_CRITICAL_REGRESSION",
  "positive_rule":"Promote only when cold gain is positive, transfer gain is positive, Red Team is not worse, and no critical regression is present.",
  "negative_rule":"Validation or in-family gain alone is insufficient and must never override transfer, adversarial, or critical-regression failures.",
  "scope":"CEREBRON adapter/LoRA promotion policy across model identities.",
  "source_failure_ids":required,
  "physical_or_scientific_domain_claim":False
}
report={
  "schema":"CEREBRON_TRANSFER_PROMOTION_LESSON_VALIDATION_V1",
  "status":"PASS" if not errors else "FAIL",
  "case_count":len(cases),
  "positive_signal_rejected_count":positive_signal_rejected,
  "strict_gate_false_promotions":sum(c["strict_gate_promote"] for c in cases),
  "positive_control_pass":strict_gate(positive_control),
  "negative_control_count":len(negative_controls),
  "negative_control_false_accepts":sum(strict_gate(x) for x in negative_controls),
  "cases":cases,
  "lesson":lesson,
  "errors":errors
}
raw=json.dumps(report,sort_keys=True,separators=(",",":")).encode()
report["validation_sha256"]=hashlib.sha256(raw).hexdigest()
out=ROOT/"artifacts/transfer-promotion-lesson-validation.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
if errors:
    raise SystemExit(1)
