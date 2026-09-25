#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evolution.cerebron_self_evolution import selftest

cfg=json.loads((ROOT/"config/cerebron-self-evolution-v1.json").read_text())
errors=[]
if cfg.get("schema")!="CEREBRON_SELF_EVOLUTION_V1":
    errors.append("BAD_SCHEMA")
pop=cfg["current_learning_population"]
if pop.get("available_ai")!=38:
    errors.append("AVAILABLE_AI_NOT_38")
if pop.get("operationally_protected_farms")!=[172,173,174]:
    errors.append("PROTECTED_FARMS_CHANGED")
if pop.get("operational_mutation_f172_f173_f174") is not False:
    errors.append("OPERATIONAL_MUTATION_BOUNDARY_BROKEN")
if cfg["dataset"].get("cold_never_training") is not True:
    errors.append("COLD_LEAK_POLICY_DISABLED")
if cfg["dataset"].get("transfer_never_training") is not True:
    errors.append("TRANSFER_LEAK_POLICY_DISABLED")
if cfg["dataset"].get("redteam_answers_never_training") is not True:
    errors.append("REDTEAM_LEAK_POLICY_DISABLED")
if cfg["dataset"].get("m6_deny_training") is not True:
    errors.append("M6_TRAINING_NOT_DENIED")
if cfg["optimizer_backends"]["dspy_gepa"].get("automatic_paid_provider") is not False:
    errors.append("DSPY_GEPA_PAID_AUTO_ENABLED")
if cfg["optimizer_backends"]["dspy_gepa"].get("automatic_external_calls") is not False:
    errors.append("DSPY_GEPA_EXTERNAL_AUTO_ENABLED")
pilot=cfg["current_pilot_baseline"]
if not (pilot.get("run_id")==36171338416 and pilot.get("real_inferences")==16 and pilot.get("parse_pass")==6 and pilot.get("model_lineages")==2):
    errors.append("PILOT_BASELINE_MISMATCH")
if pilot.get("training_released") is not False:
    errors.append("PILOT_FALSE_TRAINING_RELEASE")
if cfg.get("no_vendored_third_party_code") is not True:
    errors.append("THIRD_PARTY_VENDORED_FLAG")
repos={x["repo"]:x["license"] for x in cfg["upstream_inspiration"]}
for r,lic in {
    "NousResearch/hermes-agent-self-evolution":"MIT",
    "stanfordnlp/dspy":"MIT",
    "EleutherAI/lm-evaluation-harness":"MIT",
    "huggingface/peft":"Apache-2.0",
}.items():
    if repos.get(r)!=lic:
        errors.append("PROVENANCE_MISMATCH:"+r)

st=selftest()
report={
    "schema":"CEREBRON_SELF_EVOLUTION_GUARD_REPORT_V1",
    "status":"PASS" if not errors else "FAIL",
    "config_schema":cfg.get("schema"),
    "available_ai":pop.get("available_ai"),
    "protected_farms":pop.get("operationally_protected_farms"),
    "pilot_run_id":pilot.get("run_id"),
    "pilot_real_inferences":pilot.get("real_inferences"),
    "pilot_parse_pass":pilot.get("parse_pass"),
    "optimizer_gepa":cfg["optimizer_backends"]["dspy_gepa"],
    "selftest":st,
    "errors":errors
}
out=ROOT/"artifacts/cerebron-self-evolution-guard.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
if errors:
    raise SystemExit(1)
