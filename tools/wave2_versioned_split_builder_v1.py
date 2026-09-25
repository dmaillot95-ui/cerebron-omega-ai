#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,pathlib

ROLE_LABELS={
 "SPIRALION":["CONTINUE","ISOLATE_CONTRADICTION","COMPRESS","VERIFY_NEXT"],
 "HYPERION":["ALTERNATIVE","COUNTERFACTUAL","MECHANISM","DIVERSIFY"],
 "ASTRION":["REQUIREMENTS","PHYSICS_MODEL","CALCULATE","TEST"],
 "SAPHEA_MICRO":["ROUTE","MATH","CODE","RESEARCH","INVENT","RED_TEAM","FUSION"]
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
    manifest=c["manifest_sha256"]
    if adm.get("state")!="ADMITTED_SYNTHETIC_CANDIDATE_POOL": raise SystemExit("AFAH_ADMISSION_MISSING")
    if adm.get("manifest_sha256")!=manifest: raise SystemExit("ADMISSION_MANIFEST_MISMATCH")
    if adm.get("training_released") is not False: raise SystemExit("UNEXPECTED_TRAINING_RELEASE")

    outdir=pathlib.Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True)
    summary={"schema":"CEREBRON_WAVE2_VERSIONED_ROLE_SPLITS_V1","source_manifest_sha256":manifest,"training_released":False,"roles":{}}
    for role,labels in ROLE_LABELS.items():
        role_rows=[r for r in c["records"] if r["source_ai"]==role]
        train=[];val=[];per={}
        for label in labels:
            grp=[r for r in role_rows if r["target"]==label]
            if len(grp)!=24: raise SystemExit(f"ROLE_LABEL_COUNT_DRIFT:{role}:{label}:{len(grp)}")
            grp=sorted(grp,key=lambda r:hashlib.sha256((r["record_id"]+"|wave2-split-v1").encode()).hexdigest())
            tr,va=grp[:18],grp[18:]
            train.extend(tr);val.extend(va);per[label]={"train":18,"validation":6}
        if {r["record_id"] for r in train}&{r["record_id"] for r in val}: raise SystemExit(f"SPLIT_OVERLAP:{role}")
        payload={
          "schema":"CEREBRON_WAVE2_ROLE_SPLIT_V1","role":role,"source_manifest_sha256":manifest,
          "split_method":"SHA256_SORT_18_TRAIN_6_VALIDATION_PER_LABEL","per_label":per,
          "train_count":len(train),"validation_count":len(val),"training_released":False,
          "train_records":[{**r,"split":"TRAIN_CANDIDATE","training_eligible":False,"training_release_reason":"FRESH_COLD_GATES_PENDING"} for r in train],
          "validation_records":[{**r,"split":"VALIDATION_CANDIDATE","training_eligible":False} for r in val]
        }
        payload["split_sha256"]=h(payload)
        (outdir/f"{role.lower()}-split-v1.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
        summary["roles"][role]={"train_count":len(train),"validation_count":len(val),"split_sha256":payload["split_sha256"],"per_label":per}
    summary["summary_sha256"]=h(summary)
    (outdir/"wave2-split-summary-v1.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(summary,sort_keys=True))
if __name__=="__main__":
    main()
