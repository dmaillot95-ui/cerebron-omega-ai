#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

EXPECTED_MANIFEST="4fe279c2941b324d1a7fb2620bff945aa6558c7596aa5814ac4802d55ac36abe"
ROLES=["AELYS","ETHERION","AFAH","METRION"]
EXPECTED_SPLITS={
  "AELYS":(72,24),
  "ETHERION":(108,36),
  "AFAH":(72,24),
  "METRION":(72,24),
}
EXPECTED_COLD={
  "AELYS":{"M6":32,"TRANSFER":32,"RED":16},
  "ETHERION":{"M6":48,"TRANSFER":48,"RED":24},
  "AFAH":{"M6":32,"TRANSFER":32,"RED":16},
  "METRION":{"M6":32,"TRANSFER":32,"RED":16},
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

    cand=json.loads(pathlib.Path(a.candidates).read_text())
    adm=json.loads(pathlib.Path(a.admission).read_text())
    basecfg=json.loads(pathlib.Path(a.baseline_config).read_text())
    splitdir=pathlib.Path(a.split_dir)
    colddir=pathlib.Path(a.cold_dir)

    checks={}
    checks["manifest_expected"]=cand.get("manifest_sha256")==EXPECTED_MANIFEST
    checks["afah_admitted"]=adm.get("state")=="ADMITTED_SYNTHETIC_CANDIDATE_POOL"
    checks["afah_manifest_matches"]=adm.get("manifest_sha256")==EXPECTED_MANIFEST
    checks["pre_release_locked"]=adm.get("training_released") is False
    checks["candidate_count_432"]=cand.get("record_count")==432
    checks["candidate_training_locked"]=all(r.get("training_eligible") is False for r in cand.get("records",[]))

    baseline_prompts=set()
    for role,spec in basecfg["roles"].items():
        for row in spec["tasks"]:
            baseline_prompts.add(row[2].strip())
    candidate_prompts={r["prompt"].strip() for r in cand["records"]}
    checks["candidate_not_baseline"]=not bool(candidate_prompts & baseline_prompts)

    role_release={}
    all_candidate_ids={r["record_id"] for r in cand["records"]}
    seen_cold_ids=set()
    seen_cold_prompts=set()
    split_ok=True
    cold_ok=True
    no_leak=True

    for role in ROLES:
        sp=json.loads((splitdir/f"{role.lower()}-split-v1.json").read_text())
        tr=sp["train_records"];va=sp["validation_records"]
        tr_ids={r["record_id"] for r in tr};va_ids={r["record_id"] for r in va}
        tr_prompts={r["prompt"].strip() for r in tr};va_prompts={r["prompt"].strip() for r in va}
        exptr,expva=EXPECTED_SPLITS[role]
        if sp.get("source_manifest_sha256")!=EXPECTED_MANIFEST or len(tr)!=exptr or len(va)!=expva:
            split_ok=False
        if tr_ids & va_ids:
            split_ok=False
        role_candidate_ids={r["record_id"] for r in cand["records"] if r["source_ai"]==role}
        if tr_ids|va_ids != role_candidate_ids:
            split_ok=False
        if tr_prompts & baseline_prompts or va_prompts & baseline_prompts:
            no_leak=False

        cold_meta={}
        role_cold_ids=set();role_cold_prompts=set()
        for suite in ["M6","TRANSFER","RED"]:
            cp=json.loads((colddir/f"{role.lower()}-{suite.lower()}-v1.json").read_text())
            recs=cp["records"]
            if cp.get("deny_training") is not True or cp.get("training_eligible") is not False:
                cold_ok=False
            if len(recs)!=EXPECTED_COLD[role][suite]:
                cold_ok=False
            ids={r["id"] for r in recs}
            prompts={r["prompt"].strip() for r in recs}
            if ids & all_candidate_ids:
                no_leak=False
            if prompts & candidate_prompts or prompts & baseline_prompts:
                no_leak=False
            if ids & seen_cold_ids or prompts & seen_cold_prompts:
                no_leak=False
            seen_cold_ids |= ids;seen_cold_prompts |= prompts
            role_cold_ids |= ids;role_cold_prompts |= prompts
            cold_meta[suite]={
              "count":len(recs),
              "dataset_sha256":cp["dataset_sha256"],
              "deny_training":True
            }

        role_release[role]={
          "train_count":len(tr),
          "validation_count":len(va),
          "train_record_ids":sorted(tr_ids),
          "validation_record_ids":sorted(va_ids),
          "split_sha256":sp["split_sha256"],
          "cold":cold_meta
        }

    checks["split_integrity"]=split_ok
    checks["cold_integrity"]=cold_ok
    checks["no_exact_id_or_prompt_leakage"]=no_leak
    checks["cold_total_360"]=len(seen_cold_ids)==360

    all_pass=all(checks.values())
    release={
      "schema":"CEREBRON_WAVE1_PARALLEL_TRAINING_RELEASE_V1",
      "state":"RELEASED_FOR_SCOPED_LORA_TRAINING" if all_pass else "BLOCKED",
      "source_manifest_sha256":EXPECTED_MANIFEST,
      "admission_review_sha256":adm.get("review_sha256"),
      "training_released":bool(all_pass),
      "roles":role_release if all_pass else {},
      "checks":checks,
      "training_scope":"ROLE_LABEL_CLASSIFICATION_ONLY",
      "base_model":{
        "id":"Qwen/Qwen2.5-0.5B-Instruct",
        "revision":"ec7ddfa904d4d447eedd0b7f126df16957734abb",
        "immutable":True
      },
      "rules":[
        "TRAIN_ONLY_ON_LISTED_TRAIN_RECORD_IDS",
        "VALIDATION_DENY_TRAINING",
        "M6_DENY_TRAINING",
        "TRANSFER_DENY_TRAINING",
        "RED_DENY_TRAINING",
        "BASELINE_BENCHMARK_DENY_TRAINING",
        "ONE_ADAPTER_PER_ROLE",
        "NO_AUTO_PROMOTION"
      ],
      "claim_ceiling":"SCOPED_SYNTHETIC_ROLE_TRAINING_RELEASE_NOT_GENERAL_CAPABILITY"
    }
    release["release_sha256"]=h(release)
    p=pathlib.Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(release,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "state":release["state"],
      "training_released":release["training_released"],
      "checks":checks,
      "release_sha256":release["release_sha256"]
    },sort_keys=True))
    if not all_pass:
        raise SystemExit(2)

if __name__=="__main__":
    main()
