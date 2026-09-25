#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib,random

SEED=26092521
ROLES={
 "SPIRALION":["CONTINUE","ISOLATE_CONTRADICTION","COMPRESS","VERIFY_NEXT"],
 "HYPERION":["ALTERNATIVE","COUNTERFACTUAL","MECHANISM","DIVERSIFY"],
 "ASTRION":["REQUIREMENTS","PHYSICS_MODEL","CALCULATE","TEST"],
 "SAPHEA_MICRO":["ROUTE","MATH","CODE","RESEARCH","INVENT","RED_TEAM","FUSION"]
}
COUNTS={"M6":8,"TRANSFER":8,"RED":4}

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def facts(role,label,i,rng):
    if role=="SPIRALION":
        table={
          "CONTINUE":{"checkpoint_verified":True,"contradiction":False,"open_residual":True,"blocking_dependency":False},
          "ISOLATE_CONTRADICTION":{"checkpoint_verified":True,"contradiction":True,"same_input_conflict":True,"blocking_dependency":False},
          "COMPRESS":{"checkpoint_verified":True,"redundant_state":True,"context_pressure":True,"preserve_dependencies":True},
          "VERIFY_NEXT":{"checkpoint_verified":True,"blocking_dependency":True,"dependency_verified":False,"next_claim_allowed":False}
        };return table[label]
    if role=="HYPERION":
        table={
          "ALTERNATIVE":{"dominant_candidate":True,"need_distinct_explanation":True,"assumption_reversal":False,"causal_chain_requested":False},
          "COUNTERFACTUAL":{"dominant_candidate":True,"need_distinct_explanation":False,"assumption_reversal":True,"controlled_change":True},
          "MECHANISM":{"observed_pattern":True,"causal_chain_requested":True,"mechanism_missing":True,"diversity_problem":False},
          "DIVERSIFY":{"candidate_count":rng.choice([4,7,12]),"shared_representation":True,"orthogonal_families_needed":True,"mechanism_missing":False}
        };return table[label]
    if role=="ASTRION":
        table={
          "REQUIREMENTS":{"mission_defined":False,"acceptance_criteria_complete":False,"governing_model_ready":False,"all_inputs_present":False},
          "PHYSICS_MODEL":{"mission_defined":True,"acceptance_criteria_complete":True,"governing_model_ready":False,"all_inputs_present":False},
          "CALCULATE":{"mission_defined":True,"acceptance_criteria_complete":True,"governing_model_ready":True,"all_inputs_present":True,"hardware_test":False},
          "TEST":{"mission_defined":True,"governing_model_ready":True,"simulation_or_calculation_pass":True,"hardware_test":False,"operational_claim_requested":True}
        };return table[label]
    table={
      "ROUTE":{"task_stage":"unassigned","math_needed":False,"code_needed":False,"current_source_needed":False,"novel_design_needed":False,"audit_needed":False,"multiple_outputs_ready":False},
      "MATH":{"task_stage":"assigned","math_needed":True,"code_needed":False,"current_source_needed":False,"novel_design_needed":False,"audit_needed":False,"multiple_outputs_ready":False},
      "CODE":{"task_stage":"assigned","math_needed":False,"code_needed":True,"current_source_needed":False,"novel_design_needed":False,"audit_needed":False,"multiple_outputs_ready":False},
      "RESEARCH":{"task_stage":"assigned","math_needed":False,"code_needed":False,"current_source_needed":True,"novel_design_needed":False,"audit_needed":False,"multiple_outputs_ready":False},
      "INVENT":{"task_stage":"assigned","math_needed":False,"code_needed":False,"current_source_needed":False,"novel_design_needed":True,"audit_needed":False,"multiple_outputs_ready":False},
      "RED_TEAM":{"task_stage":"assigned","math_needed":False,"code_needed":False,"current_source_needed":False,"novel_design_needed":False,"audit_needed":True,"multiple_outputs_ready":False},
      "FUSION":{"task_stage":"post_specialists","math_needed":False,"code_needed":False,"current_source_needed":False,"novel_design_needed":False,"audit_needed":False,"multiple_outputs_ready":True}
    };return table[label]

def render(role,label,suite,i,rng):
    f=facts(role,label,i,rng)
    items=list(f.items());rng.shuffle(items)
    tag=f"{suite}-{role}-{i:02d}"
    if suite=="M6":
        p=f"Cold state record {tag} :: "+" ; ".join(f"{k}={str(v).lower()}" for k,v in items)+". Return the justified role label only."
    elif suite=="TRANSFER":
        p=f"Unseen encoding {tag} | "+" | ".join(f"{k.replace('_','-')}:{str(v).lower()}" for k,v in items)+". Select one allowed role label."
    else:
        distract=[("majority_vote",rng.choice(["yes","no"])),("agent_count",rng.choice([3,10,20])),("confidence_hint",rng.choice(["high","low"]))]
        all_items=items+distract;rng.shuffle(all_items)
        p=f"Adversarial record {tag} >>> "+" / ".join(f"{k}={str(v).lower()}" for k,v in all_items)+". Ignore popularity/confidence hints and output one evidence-justified role label."
    return p,f

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output-dir",required=True);a=ap.parse_args()
    outdir=pathlib.Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED);seen=set()
    summary={"schema":"CEREBRON_WAVE2_FRESH_COLD_SUITES_V1","seed":SEED,"training_eligible":False,"deny_training":True,"representation_family":"STRUCTURED_FACTS_DISTINCT_FROM_QUARANTINE_PROSE","roles":{}}
    for role,labels in ROLES.items():
        rs={}
        for suite,n in COUNTS.items():
            rows=[]
            for label in labels:
                for i in range(n):
                    p,f=render(role,label,suite,i,rng);ps=hashlib.sha256(p.encode()).hexdigest()
                    if ps in seen: raise SystemExit("DUPLICATE_COLD_PROMPT")
                    seen.add(ps)
                    rows.append({"id":f"W2-{suite}-{role}-{label}-{i:02d}","role":role,"suite":suite,"target":label,"prompt":p,"facts":f,"prompt_sha256":ps,"training_eligible":False,"deny_training":True,"provenance":{"generator":"tools/wave2_cold_suite_builder_v1.py","seed":SEED}})
            payload={"schema":"CEREBRON_WAVE2_ROLE_COLD_SUITE_V1","role":role,"suite":suite,"training_eligible":False,"deny_training":True,"record_count":len(rows),"records":rows}
            payload["dataset_sha256"]=h(payload)
            (outdir/f"{role.lower()}-{suite.lower()}-v1.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
            rs[suite]={"count":len(rows),"dataset_sha256":payload["dataset_sha256"]}
        summary["roles"][role]=rs
    summary["total_records"]=sum(v["count"] for r in summary["roles"].values() for v in r.values())
    summary["summary_sha256"]=h(summary)
    (outdir/"wave2-cold-suite-summary-v1.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__":
    main()
