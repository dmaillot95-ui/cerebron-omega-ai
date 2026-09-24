#!/usr/bin/env python3
import argparse,glob,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

CORE={
 "PROMPT_DIVERSITY_NE_EVIDENCE_INDEPENDENCE":[r"different prompt",r"prompt diversity",r"role-specific",r"does not.*independent",r"not.*independent"],
 "SHARED_MODEL_REVISION_IMPLIES_CORRELATED_FAILURE_RISK":[r"same model",r"shared model",r"same revision",r"shared revision",r"correlat",r"common failure"],
 "FIVE_EXECUTIONS_NE_FIVE_INDEPENDENT_EVIDENCE_SOURCES":[r"five.*not.*independent",r"not.*five independent",r"five executions.*not",r"do not constitute five independent"],
 "INDEPENDENCE_REQUIRES_MATERIALLY_DISTINCT_EVIDENCE_METHOD_DATA_MODEL_OR_EXTERNAL_REPRODUCTION":[r"independent.*evidence",r"distinct.*method",r"distinct.*data",r"different model",r"external reproduc",r"independent reproduc"]
}
FALSE_INDEPENDENCE=[
 r"constitute five independent evidentiary sources",
 r"are five independent evidentiary sources",
 r"counted as five independent evidentiary sources"
]

def norm(x): return " ".join(str(x or "").lower().split())
def concept_hits(text):
    t=norm(text);hits=[]
    for cid,pats in CORE.items():
        if any(re.search(p,t) for p in pats): hits.append(cid)
    return hits
def false_independence(text):
    t=norm(text)
    for p in FALSE_INDEPENDENCE:
        m=re.search(p,t)
        if m:
            left=t[max(0,m.start()-45):m.start()]
            if not any(n in left for n in ["not ","do not ","does not ","cannot ","can't ","no "]):
                return True
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--glob",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    rec=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.glob,recursive=True)],key=lambda x:x["worker_id"])
    rows=[];collective=set()
    for w in rec:
        raw=w.get("raw_output","");hits=concept_hits(raw);collective.update(hits)
        row={
          "worker_id":w["worker_id"],"role_id":w["role_id"],
          "real_execution":bool(w.get("llm_inference") and w.get("inference")=="PASS"),
          "spiralix":bool(w.get("spiralix_envelope_sha256")),
          "parse_ok":bool(w.get("parse_ok")),
          "prompt_echo":bool(w.get("prompt_echo")),
          "false_independence":false_independence(raw),
          "core_hits":hits,"core_hit_count":len(hits),
          "worker_quality_pass":bool(w.get("llm_inference") and w.get("inference")=="PASS" and w.get("spiralix_envelope_sha256") and w.get("parse_ok") and not w.get("prompt_echo") and not false_independence(raw) and len(hits)>=2)
        }
        rows.append(row)
    executed=sum(r["real_execution"] for r in rows);spiralix=sum(r["spiralix"] for r in rows);parsed=sum(r["parse_ok"] for r in rows);clean=sum(not r["prompt_echo"] for r in rows);wf=sum(r["worker_quality_pass"] for r in rows)
    pass1=executed==5 and spiralix==5 and parsed==5 and clean==5 and wf==5 and len(collective)==4 and not any(r["false_independence"] for r in rows)
    out={
      "schema":"CEREBRON_M11_QUALITY_PASS1_V3_SCORE",
      "run_id":args.run_id,"source_failed_run":36024003536,
      "executed_workers":executed,"spiralix_workers":spiralix,"parsed_workers":parsed,
      "no_prompt_echo_workers":clean,"worker_quality_passes":wf,
      "collective_core_hits":sorted(collective),"collective_core_count":len(collective),
      "false_independence_workers":sum(r["false_independence"] for r in rows),
      "rows":rows,"quality_pass1":pass1,
      "scale_5_to_10":"HOLD_REQUIRES_TRANSFER_PASS2" if pass1 else "DENY_REPAIR_AGAIN",
      "gold_status":"DENY_PENDING_TWO_PASS_QUALITY_POLICY"
    }
    env=make_envelope("SPIRALION:A7_SYNTHESIZER","AGORA","C80-M11-QUALITY-PASS1-V3","AUDIT",
      f"M11 V3 quality pass1={pass1}; worker_passes={wf}/5; core={len(collective)}/4.",
      problem_ref="268482a63cb1616367e9c0e2d2204f8c1b82cb00e60b8be28dacf9fcae81f230",
      evidence_level="E2",confidence=1.0,risk=0.2 if pass1 else 0.6,
      dependencies=[w.get("spiralix_envelope_sha256") for w in rec if w.get("spiralix_envelope_sha256")],
      json_payload={k:v for k,v in out.items() if k!="rows"})
    out["spiralix_audit_envelope"]=env;out["spiralix_audit_envelope_sha256"]=sha256_obj(env)
    out["score_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="score_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:out[k] for k in ["executed_workers","spiralix_workers","parsed_workers","no_prompt_echo_workers","worker_quality_passes","collective_core_count","false_independence_workers","quality_pass1","scale_5_to_10"]},sort_keys=True))
if __name__=="__main__": main()
