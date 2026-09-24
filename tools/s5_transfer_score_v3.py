#!/usr/bin/env python3
import argparse,glob,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj
PATS={
 "SIMULATION_NE_TEST":[r"simulation.*not.*test",r"simulation.*does not.*validate",r"not.*physical test",r"model-based"],
 "ASSUMPTIONS_BOUNDARIES":[r"boundary condition",r"material propert",r"assumption",r"uncertaint",r"calibrat"],
 "REPRESENTATIVE_TEST_REQUIRED":[r"physical.*test",r"thermal.?vacuum",r"representative.*test",r"hardware.*test"],
 "PREDICTION_NE_OPERATIONAL_VALIDATION":[r"prediction",r"operational validation",r"real subsystem",r"representative operation"]
}
def hits(t):
    s=" ".join((t or "").lower().split());return [k for k,v in PATS.items() if any(re.search(p,s) for p in v)]
def bad(t):
    s=" ".join((t or "").lower().split())
    positive_claims=[
      r"simulation (result )?(alone )?(validates|proves|confirms) (that )?the real",
      r"simulation (result )?alone validates",
      r"simulation can validate the claim if",
      r"simulation validates the claim if",
      r"yes,? the simulation can validate",
      r"no physical test .* needed"
    ]
    return any(re.search(p,s) for p in positive_claims)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--glob",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
    rec=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.glob,recursive=True)],key=lambda x:x["worker_id"])
    rows=[];collective=set()
    for w in rec:
      h=hits(w.get("raw_output",""));collective.update(h);b=bad(w.get("raw_output",""))
      ok=bool(w.get("llm_inference") and w.get("inference")=="PASS" and w.get("spiralix_envelope_sha256") and w.get("parse_ok") and not w.get("prompt_echo") and not b and len(h)>=2)
      rows.append({"worker_id":w["worker_id"],"role_id":w["role_id"],"core_hits":h,"core_hit_count":len(h),"false_operational_validation":b,"worker_quality_pass":ok})
    pass2=len(rec)==5 and all(r["worker_quality_pass"] for r in rows) and len(collective)==4
    out={"schema":"CEREBRON_S5_TRANSFER_PASS2_V3_SCORE","run_id":args.run_id,"rows":rows,"collective_core_hits":sorted(collective),"collective_core_count":len(collective),"worker_quality_passes":sum(r["worker_quality_pass"] for r in rows),"quality_pass2":pass2,"scale_5_to_10":"ELIGIBLE_FOR_MARGINAL_GAIN_TEST" if pass2 else "HOLD_AT_5"}
    env=make_envelope("SPIRALION:A7_SYNTHESIZER","AGORA","C80-S5-QUALITY-PASS2-TRANSFER-001","AUDIT",f"Transfer pass2={pass2}; worker passes={out['worker_quality_passes']}/5; core={len(collective)}/4.",problem_ref="THERMAL_SIMULATION_VALIDATION",evidence_level="E2",confidence=1.0,risk=.2 if pass2 else .6,dependencies=[w.get("spiralix_envelope_sha256") for w in rec if w.get("spiralix_envelope_sha256")],json_payload={k:v for k,v in out.items() if k!="rows"})
    out["spiralix_audit_envelope"]=env;out["spiralix_audit_envelope_sha256"]=sha256_obj(env);out["score_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="score_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+"\n");print(json.dumps({"quality_pass2":pass2,"worker_quality_passes":out["worker_quality_passes"],"collective_core_count":len(collective),"scale_5_to_10":out["scale_5_to_10"]},sort_keys=True))
if __name__=="__main__":main()
