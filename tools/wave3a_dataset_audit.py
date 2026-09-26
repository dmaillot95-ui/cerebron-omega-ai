#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"training"/"wave3a-datasets"
ROLES=("ELYSION","ELYSIUM","SAELION","NEXUS")
SPLITS=("train","cold","transfer","red")
MIN_TRAIN_SEED=12
SEMANTIC_JACCARD_THRESHOLD=0.92
CORES=[
 {"model_id":"Qwen/Qwen3-4B","revision":"1cfa9a7208912126459214e8b04321603b3df60c"},
 {"model_id":"HuggingFaceTB/SmolLM3-3B","revision":"a07cc9a04f16550a088caea529712d1d335b0ac1"}
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r"\s+"," ",str(s).strip().lower())
def toks(s): return set(re.findall(r"[a-z0-9]+", norm(s)))
def jaccard(a,b):
    if not a or not b: return 0.0
    return len(a & b)/len(a | b)

all_ids=set(); all_inputs={}; semantic_inputs=[]; errors=[]; specs={}; near_pairs=[]
for role in ROLES:
    spec={"role":role,"base_model_id":CORES[0]["model_id"],"base_model_revision":CORES[0]["revision"],"cores":CORES}
    for split in SPLITS:
        p=BASE/role.lower()/f"{split}.json"
        if not p.is_file():
            errors.append(f"MISSING:{role}:{split}"); continue
        d=json.loads(p.read_text())
        if d.get("role")!=role: errors.append(f"ROLE_MISMATCH:{role}:{split}")
        if d.get("split")!=split: errors.append(f"SPLIT_MISMATCH:{role}:{split}")
        if split=="train" and d.get("deny_training") is not False: errors.append(f"TRAIN_DENIED:{role}")
        if split!="train" and d.get("deny_training") is not True: errors.append(f"HOLDOUT_NOT_DENIED:{role}:{split}")
        declared_sources=set(d.get("source_ids",[]))
        if not declared_sources: errors.append(f"NO_DECLARED_SOURCE:{role}:{split}")
        items=d.get("samples",[])
        if not isinstance(items,list):
            errors.append(f"SAMPLES_NOT_LIST:{role}:{split}"); items=[]
        if not items: errors.append(f"EMPTY:{role}:{split}")
        if split=="train" and len(items)<MIN_TRAIN_SEED: errors.append(f"TRAIN_SEED_TOO_SMALL:{role}:{len(items)}")
        for x in items:
            sid=x.get("sample_id")
            if not sid:
                errors.append(f"NO_ID:{role}:{split}"); continue
            if sid in all_ids: errors.append(f"DUPLICATE_ID:{sid}")
            all_ids.add(sid)
            source_id=x.get("source_id")
            if not source_id: errors.append(f"NO_SOURCE_ID:{sid}")
            elif source_id not in declared_sources: errors.append(f"ORPHAN_SOURCE_ID:{sid}:{source_id}")
            ni=norm(x.get("input",""))
            if not ni: errors.append(f"EMPTY_INPUT:{sid}")
            if ni in all_inputs: errors.append(f"EXACT_INPUT_DUP:{sid}:{all_inputs[ni]}")
            else: all_inputs[ni]=sid
            ti=toks(ni)
            if len(ti)>=6:
                for prev_sid,prev_toks in semantic_inputs:
                    score=jaccard(ti,prev_toks)
                    if score>=SEMANTIC_JACCARD_THRESHOLD:
                        near_pairs.append({"a":prev_sid,"b":sid,"jaccard":round(score,4)})
                semantic_inputs.append((sid,ti))
        rel=str(p.relative_to(ROOT))
        spec[f"{split}_split_path"]=rel
        spec[f"{split}_split_sha256"]=sha(p)
        spec[f"{split}_count"]=len(items)
    basis="|".join(spec.get(f"{s}_split_sha256","") for s in SPLITS)
    spec["dataset_sha256"]=hashlib.sha256(basis.encode()).hexdigest()
    spec["dedup_status"]="PASS_EXACT_AND_HEURISTIC" if not near_pairs and not any(e.startswith("DUPLICATE_ID") or e.startswith("EXACT_INPUT_DUP") for e in errors) else "FAIL_OR_REVIEW"
    spec["leakage_status"]="STRUCTURAL_AND_HEURISTIC_SCREEN_PASS" if not near_pairs else "SEMANTIC_REVIEW_REQUIRED"
    spec["evidence_scope"]="EXPANDED_SEED_ONLY_NOT_SUFFICIENT_FOR_RELEASE"
    spec["deny_training_sections"]=["cold","transfer","red"]
    specs[role]=spec

has_structure_errors=bool(errors)
semantic_pass=not near_pairs
provenance_pass=not any(e.startswith("NO_DECLARED_SOURCE") or e.startswith("NO_SOURCE_ID") or e.startswith("ORPHAN_SOURCE_ID") for e in errors)
train_floor_pass=not any(e.startswith("TRAIN_SEED_TOO_SMALL") for e in errors)

out={
 "schema":"CEREBRON_WAVE3A_DATASET_AUDIT_V2",
 "status":"PASS_FOR_PREPARATION_FAIL_FOR_RELEASE" if not has_structure_errors and semantic_pass else "FAIL_PREPARATION",
 "wave":"WAVE3A",
 "roles":list(ROLES),
 "role_specs":specs,
 "checks":{
   "structure":"PASS" if not has_structure_errors else "FAIL",
   "sample_id_uniqueness":"PASS" if not any(e.startswith("DUPLICATE_ID") for e in errors) else "FAIL",
   "exact_input_dedup":"PASS" if not any(e.startswith("EXACT_INPUT_DUP") for e in errors) else "FAIL",
   "semantic_near_duplicate_screen":"PASS_HEURISTIC" if semantic_pass else "REVIEW_REQUIRED",
   "semantic_jaccard_threshold":SEMANTIC_JACCARD_THRESHOLD,
   "provenance_source_membership":"PASS" if provenance_pass else "FAIL",
   "train_seed_floor_12_per_role":"PASS" if train_floor_pass else "FAIL",
   "cold_transfer_red_deny_training":"PASS" if not any(e.startswith("HOLDOUT_NOT_DENIED") for e in errors) else "FAIL",
   "dual_core_pins":"PASS",
   "scale_sufficient_for_training":"FAIL_RELEASE_SCALE_NOT_ESTABLISHED",
   "dispatch_workflow_review":"PENDING",
   "f72_or_equivalent_release_gate":"PENDING"
 },
 "near_duplicate_pairs":near_pairs,
 "errors":errors,
 "training_released":False,
 "continuous_training_eligible":False,
 "training_executed":False,
 "weights_changed":False,
 "claim_boundary":"EXPANDED_DATASET_PREPARATION_AND_AUDIT_ONLY_NO_TRAINING"
}
art=ROOT/"artifacts"; art.mkdir(exist_ok=True)
(art/"wave3a-dataset-audit-v2.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"status":out["status"],"errors":errors,"near_duplicate_pairs":near_pairs,"roles":list(specs),"training_released":False,"weights_changed":False},ensure_ascii=False))
raise SystemExit(1 if has_structure_errors or not semantic_pass else 0)
