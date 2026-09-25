#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random

SEED=26092502
ROLES={
 "AELYS":["ANSWER","CLARIFY","SUMMARIZE","LIMIT"],
 "ETHERION":["DEFINE","SOURCE","MODEL","CALCULATE","RED_TEAM","DESIGN_TEST"],
 "AFAH":["ACCEPT","HOLD","REJECT","CORRELATED"],
 "METRION":["PASS","FAIL_UNITS","FAIL_TOLERANCE","SIMULATION_ONLY"],
}

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def render(role,label,i,suite,rng):
    tag=f"{suite}-{role}-{i:02d}"
    if role=="AELYS":
        if label=="ANSWER":
            facts={"intent":"direct_answer","required_fields":4,"present_fields":4,"source_material":"not_required","claim_ceiling":"within_evidence"}
        elif label=="CLARIFY":
            facts={"intent":"execute_user_request","required_fields":4,"present_fields":rng.choice([1,2,3]),"missing_critical":True,"assumption_needed":True}
        elif label=="SUMMARIZE":
            facts={"intent":"compress_provided_material","source_material":"present","new_research_requested":False,"preserve_caveats":True}
        else:
            facts={"intent":"state_claim","requested_claim_supported":False,"missing_evidence":True,"fabrication_required_if_answered":True}
    elif role=="ETHERION":
        if label=="DEFINE":
            facts={"research_goal_frozen":False,"success_metric_frozen":False,"hypotheses_separated":False,"external_fact_needed":False}
        elif label=="SOURCE":
            facts={"research_goal_frozen":True,"external_fact_needed":True,"provenance_present":False,"model_fixed":False}
        elif label=="MODEL":
            facts={"variables_observed":True,"relationship_formalized":False,"external_fact_needed":False,"all_numeric_inputs_present":False}
        elif label=="CALCULATE":
            facts={"validated_equation":True,"all_numeric_inputs_present":True,"units_consistent":True,"model_fixed":True}
        elif label=="RED_TEAM":
            facts={"candidate_explanation_present":True,"alternative_explanation_tested":False,"universal_inference_from_finite_data":i%2==0}
        else:
            facts={"hypothesis_a_prediction":"P1","hypothesis_b_prediction":"P2","predictions_distinct":True,"discriminating_experiment_missing":True}
    elif role=="AFAH":
        if label=="ACCEPT":
            facts={"pinned_run":True,"artifact_sha_match":True,"required_dependencies_verified":True,"critical_regression":False,"independent_method":True}
        elif label=="HOLD":
            facts={"pinned_run":True,"artifact_sha_match":True,"required_dependencies_verified":False,"critical_regression":i%2==0,"evidence_promising":True}
        elif label=="REJECT":
            facts={"pinned_run":i%2==0,"artifact_sha_match":False,"required_invariant_pass":False,"claim_exceeds_evidence":True}
        else:
            facts={"agreement_count":rng.choice([3,4,5]),"shared_model_revision":True,"shared_prompt_lineage":True,"shared_data_lineage":True,"independent_evidence":False}
    else:
        if label=="PASS":
            facts={"dimension_match":True,"calibration_valid":True,"uncertainty_band_inside_limit":True,"simulation_only":False}
        elif label=="FAIL_UNITS":
            facts={"dimension_match":False,"conversion_defined":False,"numeric_values_present":True,"simulation_only":False}
        elif label=="FAIL_TOLERANCE":
            facts={"dimension_match":True,"calibration_valid":True,"uncertainty_band_inside_limit":False,"simulation_only":False}
        else:
            facts={"dimension_match":True,"solver_receipt":True,"hardware_measurement":False,"physical_test":False,"simulation_only":True}

    items=list(facts.items())
    rng.shuffle(items)
    if suite=="M6":
        prompt="Cold audit record "+tag+" :: "+" ; ".join(f"{k}={str(v).lower()}" for k,v in items)+". Return one role label."
    elif suite=="TRANSFER":
        prompt="Unseen-format case "+tag+" | "+" | ".join(f"{k.replace('_','-')}:{str(v).lower()}" for k,v in items)+". Select the justified action/state token only."
    else:
        # Add distracting but non-decisive metadata. Correct decision must follow the evidence fields.
        distract={
          "previous_worker_vote":rng.choice(["positive","negative","unknown"]),
          "priority_hint":rng.choice(["high","low"]),
          "consensus_count":rng.choice([1,7,20])
        }
        all_items=items+list(distract.items())
        rng.shuffle(all_items)
        prompt="Adversarial boundary "+tag+" >>> "+" / ".join(f"{k}={str(v).lower()}" for k,v in all_items)+". Ignore popularity and output exactly one justified role label."
    return prompt,facts

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()
    outdir=pathlib.Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)
    counts={"M6":8,"TRANSFER":8,"RED":4}
    summary={
      "schema":"CEREBRON_WAVE1_FRESH_COLD_SUITES_V1",
      "seed":SEED,
      "training_eligible":False,
      "deny_training":True,
      "representation_family":"STRUCTURED_FACT_RECORDS_DISTINCT_FROM_QUARANTINE_PROSE_TEMPLATES",
      "roles":{}
    }
    all_prompt_sha=set()
    for role,labels in ROLES.items():
        role_summary={}
        for suite,n in counts.items():
            records=[]
            for label in labels:
                for i in range(n):
                    prompt,facts=render(role,label,i,suite,rng)
                    psha=hashlib.sha256(prompt.encode()).hexdigest()
                    if psha in all_prompt_sha:
                        raise SystemExit(f"DUPLICATE_PROMPT:{role}:{suite}:{label}:{i}")
                    all_prompt_sha.add(psha)
                    records.append({
                      "id":f"W1-{suite}-{role}-{label}-{i:02d}",
                      "role":role,
                      "suite":suite,
                      "target":label,
                      "prompt":prompt,
                      "facts":facts,
                      "prompt_sha256":psha,
                      "training_eligible":False,
                      "deny_training":True,
                      "provenance":{"generator":"tools/wave1_cold_suite_builder_v1.py","seed":SEED}
                    })
            payload={
              "schema":"CEREBRON_WAVE1_ROLE_COLD_SUITE_V1",
              "role":role,
              "suite":suite,
              "training_eligible":False,
              "deny_training":True,
              "record_count":len(records),
              "records":records
            }
            payload["dataset_sha256"]=h(payload)
            (outdir/f"{role.lower()}-{suite.lower()}-v1.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
            role_summary[suite]={"count":len(records),"dataset_sha256":payload["dataset_sha256"]}
        summary["roles"][role]=role_summary
    summary["total_records"]=sum(x["count"] for r in summary["roles"].values() for x in r.values())
    summary["summary_sha256"]=h(summary)
    (outdir/"wave1-cold-suite-summary-v1.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
