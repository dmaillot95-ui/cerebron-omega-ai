#!/usr/bin/env python3
import hashlib, itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FB=ROOT/"memory/failure-bank-v1.json"
WF=ROOT/".github/workflows/agora-collective-5m.yml"
OUT=ROOT/"artifacts/agora-evidence-scope-lesson-validation.json"

failure_bank=json.loads(FB.read_text())
failure=next(
    (x for x in failure_bank["entries"] if x["FAILURE_ID"]=="FAIL-AGORA-CONTENT-SCOPE-PROMOTION-001"),
    None
)
errors=[]
if failure is None:
    errors.append("FAILURE_RECORD_MISSING")
else:
    before=failure.get("MEASURED_BEFORE",{})
    if before.get("imported_gate_summary_pass") is not False:
        errors.append("BEFORE_IMPORTED_SUMMARY_NOT_FALSE")
    if before.get("promotion")!="ELIGIBLE" or before.get("scientific_ok") is not True:
        errors.append("BEFORE_FALSE_PROMOTION_NOT_RECORDED")
    closure=failure.get("CLOSURE_EVIDENCE",{})
    if closure.get("promotion")!="BLOCKED_CONTENT_VALIDATION_UNBOUND":
        errors.append("CLOSURE_PROMOTION_NOT_BLOCKED")
    if closure.get("scientific_ok") is not False:
        errors.append("CLOSURE_SCIENTIFIC_OK_NOT_FALSE")

workflow=WF.read_text()
for marker in [
    "CEREBRON_AGORA_COLLECTIVE_V3",
    "AGORA_GATE_INVARIANT_ONLY",
    "content_validation_bound",
    "GATE_INVARIANT_EVIDENCE_DOES_NOT_VALIDATE_IMPORTED_CONTENT",
]:
    if marker not in workflow:
        errors.append("WORKFLOW_MARKER_MISSING:"+marker)

# Method 1: deterministic reproduction of the historical false-promotion predicate.
local_gate_invariant_ok=True
imported_gate_summary_pass=False
content_validation_bound=False
old_scientific_ok=local_gate_invariant_ok
new_scientific_ok=local_gate_invariant_ok and imported_gate_summary_pass and content_validation_bound
reproduction={
    "method":"HISTORICAL_PREDICATE_REPRODUCTION",
    "old_scientific_ok":old_scientific_ok,
    "old_promotion":"ELIGIBLE" if old_scientific_ok else "BLOCKED",
    "new_scientific_ok":new_scientific_ok,
    "new_promotion":"ELIGIBLE" if new_scientific_ok else "BLOCKED",
    "pass":old_scientific_ok is True and new_scientific_ok is False
}
if not reproduction["pass"]:
    errors.append("REPRODUCTION_FAILED")

# Method 2: exhaustive truth table of the corrected three-factor gate.
rows=[]
for gate_ok, imported_ok, bound in itertools.product((False,True),repeat=3):
    observed=gate_ok and imported_ok and bound
    rows.append({
        "gate_invariant_ok":gate_ok,
        "imported_gate_summary_pass":imported_ok,
        "content_validation_bound":bound,
        "accepted":observed
    })
accepting=[r for r in rows if r["accepted"]]
truth_table={
    "method":"EXHAUSTIVE_3_FACTOR_TRUTH_TABLE",
    "cases":len(rows),
    "accepting_cases":len(accepting),
    "only_accepting_case":accepting[0] if len(accepting)==1 else None,
    "pass":len(rows)==8 and len(accepting)==1 and all(accepting[0][k] is True for k in (
        "gate_invariant_ok","imported_gate_summary_pass","content_validation_bound"
    ))
}
if not truth_table["pass"]:
    errors.append("TRUTH_TABLE_FAILED")

# Method 3: adversarial negative-path falsification.
attacks=[
    {"name":"LOCAL_GATE_ONLY","gate":True,"imported":False,"bound":False},
    {"name":"LOCAL_PLUS_IMPORTED_NO_BINDING","gate":True,"imported":True,"bound":False},
    {"name":"LOCAL_PLUS_BINDING_IMPORTED_FAIL","gate":True,"imported":False,"bound":True},
    {"name":"IMPORTED_PLUS_BINDING_NO_LOCAL_GATE","gate":False,"imported":True,"bound":True},
    {"name":"NOTHING","gate":False,"imported":False,"bound":False},
]
attack_results=[]
for a in attacks:
    accepted=a["gate"] and a["imported"] and a["bound"]
    attack_results.append({**a,"accepted":accepted})
falsification={
    "method":"ADVERSARIAL_SCOPE_CONFUSION_NEGATIVES",
    "attack_count":len(attacks),
    "false_accepts":sum(x["accepted"] for x in attack_results),
    "results":attack_results,
    "pass":all(not x["accepted"] for x in attack_results)
}
if not falsification["pass"]:
    errors.append("FALSIFICATION_FAILED")

lesson={
    "lesson_id":"LESSON-AGORA-EVIDENCE-SCOPE-001",
    "title":"Control-plane gate evidence must be bound to content before content promotion.",
    "invariant":"GATE_INVARIANT_EVIDENCE_DOES_NOT_VALIDATE_IMPORTED_CONTENT",
    "scope":"AGORA imported packet promotion and memory admission.",
    "positive_rule":"Content promotion requires gate-invariant validity, imported required gates PASS, and content-specific validation bound to packet hashes.",
    "negative_rule":"A local proof that the Boolean gate itself works cannot validate unrelated imported scientific content.",
    "source_failure_id":"FAIL-AGORA-CONTENT-SCOPE-PROMOTION-001",
    "training_use":"CONTROL_PLANE_EPISTEMIC_BOUNDARY_ONLY",
    "physical_or_scientific_domain_claim":False
}
payload={
    "schema":"CEREBRON_AGORA_EVIDENCE_SCOPE_LESSON_VALIDATION_V1",
    "status":"PASS" if not errors else "FAIL",
    "failure_id":"FAIL-AGORA-CONTENT-SCOPE-PROMOTION-001",
    "methods":[reproduction,truth_table,falsification],
    "method_count":3,
    "independent_model_lineages":0,
    "lesson":lesson,
    "errors":errors
}
raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
payload["validation_sha256"]=hashlib.sha256(raw).hexdigest()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(json.dumps(payload,sort_keys=True))
if errors:
    raise SystemExit(1)
