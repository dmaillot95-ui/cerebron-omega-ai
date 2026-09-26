#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"training"/"wave3a-datasets"
ROLES=("ELYSION","ELYSIUM","SAELION","NEXUS")
SPLITS=("train","cold","transfer","red")
CORES=[
 {"model_id":"Qwen/Qwen3-4B","revision":"1cfa9a7208912126459214e8b04321603b3df60c"},
 {"model_id":"HuggingFaceTB/SmolLM3-3B","revision":"a07cc9a04f16550a088caea529712d1d335b0ac1"}
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r"\s+"," ",str(s).strip().lower())

all_ids=set(); all_inputs={}; errors=[]; specs={}
for role in ROLES:
    spec={"role":role,"base_model_id":CORES[0]["model_id"],"base_model_revision":CORES[0]["revision"],"cores":CORES}
    role_ids=set()
    for split in SPLITS:
        p=BASE/role.lower()/f"{split}.json"
        if not p.is_file():
            errors.append(f"MISSING:{role}:{split}"); continue
        d=json.loads(p.read_text())
        if d.get("role")!=role: errors.append(f"ROLE_MISMATCH:{role}:{split}")
        if d.get("split")!=split: errors.append(f"SPLIT_MISMATCH:{role}:{split}")
        if split=="train" and d.get("deny_training") is not False: errors.append(f"TRAIN_DENIED:{role}")
        if split!="train" and d.get("deny_training") is not True: errors.append(f"HOLDOUT_NOT_DENIED:{role}:{split}")
        items=d.get("samples",[])
        if not isinstance(items,list) or not items: errors.append(f"EMPTY:{role}:{split}")
        for x in items:
            sid=x.get("sample_id")
            if not sid: errors.append(f"NO_ID:{role}:{split}"); continue
            if sid in all_ids: errors.append(f"DUPLICATE_ID:{sid}")
            all_ids.add(sid); role_ids.add(sid)
            ni=norm(x.get("input",""))
            if ni in all_inputs: errors.append(f"EXACT_INPUT_DUP:{sid}:{all_inputs[ni]}")
            else: all_inputs[ni]=sid
        rel=str(p.relative_to(ROOT))
        spec[f"{split}_split_path"]=rel
        spec[f"{split}_split_sha256"]=sha(p)
        spec[f"{split}_count"]=len(items)
    basis="|".join(spec.get(f"{s}_split_sha256","") for s in SPLITS)
    spec["dataset_sha256"]=hashlib.sha256(basis.encode()).hexdigest()
    spec["dedup_status"]="PASS_EXACT" if not any(e.startswith("DUPLICATE_ID") or e.startswith("EXACT_INPUT_DUP") for e in errors) else "FAIL"
    spec["leakage_status"]="STRUCTURAL_SPLIT_SEPARATION_PASS_SEMANTIC_REVIEW_PENDING"
    spec["evidence_scope"]="SEED_ONLY_NOT_SUFFICIENT_FOR_RELEASE"
    spec["deny_training_sections"]=["cold","transfer","red"]
    specs[role]=spec

out={
 "schema":"CEREBRON_WAVE3A_DATASET_AUDIT_V1",
 "status":"PASS_FOR_PREPARATION_FAIL_FOR_RELEASE" if not errors else "FAIL_STRUCTURE",
 "wave":"WAVE3A",
 "roles":list(ROLES),
 "role_specs":specs,
 "checks":{
   "structure":"PASS" if not errors else "FAIL",
   "sample_id_uniqueness":"PASS" if not any(e.startswith("DUPLICATE_ID") for e in errors) else "FAIL",
   "exact_input_dedup":"PASS" if not any(e.startswith("EXACT_INPUT_DUP") for e in errors) else "FAIL",
   "cold_transfer_red_deny_training":"PASS" if not any(e.startswith("HOLDOUT_NOT_DENIED") for e in errors) else "FAIL",
   "dual_core_pins":"PASS",
   "semantic_dedup":"PENDING_REVIEW",
   "provenance_review":"PENDING",
   "scale_sufficient_for_training":"FAIL_SEED_ONLY",
   "dispatch_workflow_review":"PENDING",
   "f72_or_equivalent_release_gate":"PENDING"
 },
 "errors":errors,
 "training_released":False,
 "continuous_training_eligible":False,
 "training_executed":False,
 "weights_changed":False,
 "claim_boundary":"AUDIT_ONLY_NO_TRAINING"
}
art=ROOT/"artifacts"; art.mkdir(exist_ok=True)
(art/"wave3a-dataset-audit-v1.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"status":out["status"],"errors":errors,"roles":list(specs),"training_released":False,"weights_changed":False},ensure_ascii=False))
raise SystemExit(1 if errors else 0)
