#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib

ROLES=["SPIRALION","HYPERION","ASTRION","SAPHEA_MICRO"]
EXPECTED_SPLITS={"SPIRALION":(72,24),"HYPERION":(72,24),"ASTRION":(72,24),"SAPHEA_MICRO":(126,42)}
EXPECTED_COLD={
 "SPIRALION":{"M6":32,"TRANSFER":32,"RED":16},
 "HYPERION":{"M6":32,"TRANSFER":32,"RED":16},
 "ASTRION":{"M6":32,"TRANSFER":32,"RED":16},
 "SAPHEA_MICRO":{"M6":56,"TRANSFER":56,"RED":28}
}

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--split-dir",required=True)
    ap.add_argument("--cold-dir",required=True)
    ap.add_argument("--admission",required=True)
    ap.add_argument("--baseline-config",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    c=json.loads(pathlib.Path(a.candidates).read_text())
    adm=json.loads(pathlib.Path(a.admission).read_text())
    base=json.loads(pathlib.Path(a.baseline_config).read_text())
    manifest=c["manifest_sha256"]

    checks={}
    checks["admission_state"]=adm.get("state")=="ADMITTED_SYNTHETIC_CANDIDATE_POOL"
    checks["admission_manifest_match"]=adm.get("manifest_sha256")==manifest
    checks["admission_locked_before_release"]=adm.get("training_released") is False
    checks["candidate_count_456"]=c.get("record_count")==456
    checks["candidate_locked"]=all(r.get("training_eligible") is False for r in c.get("records",[]))

    baseline_prompts={row[2].strip() for spec in base["roles"].values() for row in spec["tasks"]}
    candidate_prompts={r["prompt"].strip() for r in c["records"]}
    checks["candidate_baseline_prompt_disjoint"]=not bool(candidate_prompts & baseline_prompts)

    splitdir=pathlib.Path(a.split_dir);colddir=pathlib.Path(a.cold_dir)
    all_candidate_ids={r["record_id"] for r in c["records"]}
    seen_cold_ids=set();seen_cold_prompts=set()
    role_release={};split_ok=True;cold_ok=True;no_leak=True
    for role in ROLES:
        sp=json.loads((splitdir/f"{role.lower()}-split-v1.json").read_text())
        tr=sp["train_records"];va=sp["validation_records"]
        tr_ids={r["record_id"] for r in tr};va_ids={r["record_id"] for r in va}
        tr_prompts={r["prompt"].strip() for r in tr};va_prompts={r["prompt"].strip() for r in va}
        exptr,expva=EXPECTED_SPLITS[role]
        if sp.get("source_manifest_sha256")!=manifest or len(tr)!=exptr or len(va)!=expva: split_ok=False
        if tr_ids&va_ids: split_ok=False
        role_ids={r["record_id"] for r in c["records"] if r["source_ai"]==role}
        if tr_ids|va_ids!=role_ids: split_ok=False
        if tr_prompts&baseline_prompts or va_prompts&baseline_prompts: no_leak=False

        coldmeta={}
        for suite in ["M6","TRANSFER","RED"]:
            cp=json.loads((colddir/f"{role.lower()}-{suite.lower()}-v1.json").read_text())
            rows=cp["records"];ids={r["id"] for r in rows};prompts={r["prompt"].strip() for r in rows}
            if cp.get("deny_training") is not True or cp.get("training_eligible") is not False: cold_ok=False
            if len(rows)!=EXPECTED_COLD[role][suite]: cold_ok=False
            if ids&all_candidate_ids or prompts&candidate_prompts or prompts&baseline_prompts: no_leak=False
            if ids&seen_cold_ids or prompts&seen_cold_prompts: no_leak=False
            seen_cold_ids|=ids;seen_cold_prompts|=prompts
            coldmeta[suite]={"count":len(rows),"dataset_sha256":cp["dataset_sha256"],"deny_training":True}

        role_release[role]={
          "train_count":len(tr),"validation_count":len(va),
          "train_record_ids":sorted(tr_ids),"validation_record_ids":sorted(va_ids),
          "split_sha256":sp["split_sha256"],"cold":coldmeta,
          "model":base["roles"][role]["model"]
        }

    checks["split_integrity"]=split_ok
    checks["cold_integrity"]=cold_ok
    checks["no_exact_id_or_prompt_leakage"]=no_leak
    checks["cold_total_380"]=len(seen_cold_ids)==380
    ok=all(checks.values())
    out={
      "schema":"CEREBRON_WAVE2_PARALLEL_TRAINING_RELEASE_V1",
      "state":"RELEASED_FOR_SCOPED_LORA_TRAINING" if ok else "BLOCKED",
      "source_manifest_sha256":manifest,
      "admission_review_sha256":adm.get("review_sha256"),
      "training_released":ok,
      "roles":role_release if ok else {},
      "checks":checks,
      "rules":["TRAIN_ONLY_LISTED_IDS","VALIDATION_DENY_TRAINING","M6_DENY_TRAINING","TRANSFER_DENY_TRAINING","RED_DENY_TRAINING","BASELINE_DENY_TRAINING","ONE_ADAPTER_PER_ROLE","NO_AUTO_PROMOTION"],
      "claim_ceiling":"SCOPED_SYNTHETIC_ROLE_TRAINING_RELEASE_NOT_GENERAL_CAPABILITY"
    }
    out["release_sha256"]=h(out)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"state":out["state"],"training_released":out["training_released"],"checks":checks,"release_sha256":out["release_sha256"]},sort_keys=True))
    if not ok: raise SystemExit(2)
if __name__=="__main__":
    main()
