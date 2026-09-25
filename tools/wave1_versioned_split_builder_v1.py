#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

EXPECTED_MANIFEST="4fe279c2941b324d1a7fb2620bff945aa6558c7596aa5814ac4802d55ac36abe"
ROLE_LABELS={
  "AELYS":["ANSWER","CLARIFY","SUMMARIZE","LIMIT"],
  "ETHERION":["DEFINE","SOURCE","MODEL","CALCULATE","RED_TEAM","DESIGN_TEST"],
  "AFAH":["ACCEPT","HOLD","REJECT","CORRELATED"],
  "METRION":["PASS","FAIL_UNITS","FAIL_TOLERANCE","SIMULATION_ONLY"],
}

def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--admission",required=True)
    ap.add_argument("--output-dir",required=True)
    a=ap.parse_args()

    c=json.loads(pathlib.Path(a.candidates).read_text())
    adm=json.loads(pathlib.Path(a.admission).read_text())
    if c.get("manifest_sha256")!=EXPECTED_MANIFEST:
        raise SystemExit("CANDIDATE_MANIFEST_SHA_MISMATCH")
    if adm.get("state")!="ADMITTED_SYNTHETIC_CANDIDATE_POOL":
        raise SystemExit("AFAH_ADMISSION_MISSING")
    if adm.get("manifest_sha256")!=EXPECTED_MANIFEST:
        raise SystemExit("ADMISSION_MANIFEST_SHA_MISMATCH")
    if adm.get("training_released") is not False:
        raise SystemExit("UNEXPECTED_PREEXISTING_TRAINING_RELEASE")

    outdir=pathlib.Path(a.output_dir)
    outdir.mkdir(parents=True,exist_ok=True)
    summary={
      "schema":"CEREBRON_WAVE1_VERSIONED_ROLE_SPLITS_V1",
      "source_manifest_sha256":EXPECTED_MANIFEST,
      "training_released":False,
      "roles":{},
      "claim_ceiling":"VERSIONED_SYNTHETIC_TRAIN_VALIDATION_CANDIDATE_SPLITS_ONLY"
    }

    rows=c["records"]
    for role,labels in ROLE_LABELS.items():
        role_rows=[r for r in rows if r["source_ai"]==role]
        train=[]; validation=[]
        per_label={}
        for label in labels:
            grp=[r for r in role_rows if r["target"]==label]
            grp=sorted(grp,key=lambda r: hashlib.sha256((r["record_id"]+"|split-v1").encode()).hexdigest())
            if len(grp)!=24:
                raise SystemExit(f"ROLE_LABEL_COUNT_DRIFT:{role}:{label}:{len(grp)}")
            tr=grp[:18]; va=grp[18:]
            train.extend(tr);validation.extend(va)
            per_label[label]={"train":len(tr),"validation":len(va)}
        train_ids={r["record_id"] for r in train}
        val_ids={r["record_id"] for r in validation}
        if train_ids & val_ids:
            raise SystemExit(f"SPLIT_OVERLAP:{role}")
        train_out=[{
          **r,
          "split":"TRAIN_CANDIDATE",
          "training_eligible":False,
          "training_release_reason":"FRESH_M6_TRANSFER_RED_GATES_PENDING"
        } for r in train]
        val_out=[{
          **r,
          "split":"VALIDATION_CANDIDATE",
          "training_eligible":False
        } for r in validation]
        payload={
          "schema":"CEREBRON_WAVE1_ROLE_SPLIT_V1",
          "role":role,
          "source_manifest_sha256":EXPECTED_MANIFEST,
          "split_method":"SHA256_SORT_18_TRAIN_6_VALIDATION_PER_LABEL",
          "per_label":per_label,
          "train_count":len(train_out),
          "validation_count":len(val_out),
          "training_released":False,
          "train_records":train_out,
          "validation_records":val_out,
        }
        payload["split_sha256"]=h(payload)
        (outdir/f"{role.lower()}-split-v1.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
        summary["roles"][role]={
          "train_count":len(train_out),
          "validation_count":len(val_out),
          "split_sha256":payload["split_sha256"],
          "per_label":per_label
        }

    summary["summary_sha256"]=h(summary)
    (outdir/"wave1-split-summary-v1.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
