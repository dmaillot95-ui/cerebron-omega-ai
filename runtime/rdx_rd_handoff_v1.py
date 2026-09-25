from __future__ import annotations
import argparse,hashlib,json,pathlib,re
from typing import Any,Dict,List

ROOT=pathlib.Path(__file__).resolve().parents[1]
POLICY=json.loads((ROOT/"config/memory-promotion-policy-v1.json").read_text())
CONTRACT=json.loads((ROOT/"config/rdx-rd-handoff-contract-v1.json").read_text())
HEX64=re.compile(r"^[0-9a-f]{64}$")
PREFIXES=tuple(CONTRACT["canonical_id_prefixes"])

def all_ids(obj:Dict[str,Any])->List[str]:
    ids=[]
    for x in obj.get("canonical_ids",[]):
        if isinstance(x,str): ids.append(x)
        elif isinstance(x,dict) and isinstance(x.get("id"),str): ids.append(x["id"])
    for section,key in [("sources","source_id"),("executions","exec_id"),("claims","claim_id")]:
        for row in obj.get(section,[]) or []:
            if isinstance(row,dict) and isinstance(row.get(key),str): ids.append(row[key])
    return ids

def validate(obj:Dict[str,Any])->Dict[str,Any]:
    errors=[]; blockers=[]
    missing=[k for k in CONTRACT["required_top_level"] if k not in obj]
    if missing: errors.append("MISSING_TOP_LEVEL:"+",".join(sorted(missing)))

    ids=all_ids(obj)
    canonical_ids_pass=bool(ids) and len(ids)==len(set(ids)) and all(i.startswith(PREFIXES) for i in ids)
    if not canonical_ids_pass: errors.append("CANONICAL_IDS_FAIL")

    arts=obj.get("artifacts") or []
    artifact_sha_pass=bool(arts) and all(
      isinstance(a,dict) and HEX64.match(str(a.get("sha256",""))) for a in arts
    )
    if not artifact_sha_pass: errors.append("ARTIFACT_SHA_FAIL")

    sources=obj.get("sources") or []
    provenance_pass=bool(sources) and all(
      isinstance(s,dict) and s.get("source_id") and s.get("origin") and s.get("citation_or_location")
      for s in sources
    )
    if not provenance_pass: errors.append("PROVENANCE_FAIL")

    dedup_pass=(obj.get("dedup") or {}).get("status")=="PASS"
    m6_clean=obj.get("m6_contamination") is False
    if not dedup_pass: blockers.append("DEDUP_PASS")
    if not m6_clean: blockers.append("M6_CLEAN")

    memory_ready=(not missing and canonical_ids_pass and artifact_sha_pass and provenance_pass and dedup_pass and m6_clean)

    execs=obj.get("executions") or []
    verified_exec=any(isinstance(x,dict) and x.get("status")=="PASS" and x.get("artifact_refs") for x in execs)
    human_review=(obj.get("human_review") or {}).get("complete") is True
    rights_clear=bool(sources) and all(s.get("rights_status")=="ALLOWED" for s in sources)
    rights_clear=rights_clear and (obj.get("rights") or {}).get("shared_training_allowed") is True
    open_work_empty=len(obj.get("open_work") or [])==0
    transfer=(obj.get("transfer") or {}).get("status")=="PASS"
    ablation=(obj.get("ablation") or {}).get("status")=="PASS"
    afah=(obj.get("afah_review") or {}).get("status")=="PASS"

    review_checks={
      "MEMORY_INGEST_READY":memory_ready,
      "VERIFIED_EXECUTION_PRESENT":verified_exec,
      "HUMAN_REVIEW_COMPLETE":human_review,
      "SOURCE_RIGHTS_CLEAR_FOR_TRAINING":rights_clear,
      "OPEN_WORK_EMPTY":open_work_empty,
      "TRANSFER_PASS":transfer,
      "ABLATION_PASS":ablation,
      "AFAH_PASS":afah,
    }
    for k,v in review_checks.items():
        if not v and k not in blockers: blockers.append(k)
    f72_candidate=all(review_checks.values())

    f72=(POLICY.get("live_gates",{}).get("F72",{}).get("current")=="PASS")
    train_split=(obj.get("rights") or {}).get("train_valid_split_ready") is True
    m6_e2e=(obj.get("rights") or {}).get("m6_exclusion_e2e") is True
    gold=f72_candidate and f72 and train_split and m6_e2e
    if f72_candidate and not f72: blockers.append("F72_GLOBAL_PASS")
    if f72_candidate and not train_split: blockers.append("TRAIN_VALID_SPLIT")
    if f72_candidate and not m6_e2e: blockers.append("M6_EXCLUSION_E2E")

    canonical=hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return {
      "schema":"CEREBRON_RDX_RD_HANDOFF_DECISION_V1",
      "handoff_id":obj.get("handoff_id"),
      "project_id":obj.get("project_id"),
      "handoff_sha256":canonical,
      "memory_ingest_ready":memory_ready,
      "f72_review_candidate":f72_candidate,
      "m4_gold_eligible":gold,
      "training_eligible":gold,
      "auto_train":False,
      "f72_global_current":POLICY.get("live_gates",{}).get("F72",{}).get("current"),
      "blockers":sorted(set(blockers)),
      "errors":errors,
      "claim_ceiling":"HANDOFF_VALIDATION_AND_PROMOTION_READINESS_ONLY_NO_NEURAL_TRAINING_EXECUTED"
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output")
    args=ap.parse_args()
    obj=json.loads(pathlib.Path(args.input).read_text())
    out=validate(obj)
    raw=json.dumps(out,indent=2,ensure_ascii=False)+"\n"
    if args.output:
        p=pathlib.Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(raw)
    print(raw,end="")
    return 0 if not out["errors"] else 2

if __name__=="__main__":
    raise SystemExit(main())
