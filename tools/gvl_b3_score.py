#!/usr/bin/env python3
import argparse,glob,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spiralix_bus import make_envelope,sha256_obj

CORE={
 "OBSERVATIONAL_ASSOCIATION_NE_CAUSAL_PROOF":[r"observational.*not.*causal",r"association.*not.*caus",r"cannot establish.*caus",r"does not establish.*caus",r"cannot conclude.*caus"],
 "UNMEASURED_CONFOUNDING_OR_SELECTION_RISK":[r"confound",r"selection bias",r"clinician choice",r"disease severity",r"unmeasured"],
 "IDENTIFICATION_ASSUMPTIONS_OR_STRONGER_DESIGN_REQUIRED":[r"random",r"identif",r"backdoor",r"instrument",r"natural experiment",r"causal design",r"exchangeab"],
 "OBSERVED_25_PERCENT_NE_CAUSAL_EFFECT_SIZE_WITHOUT_IDENTIFICATION":[r"25%.*not.*causal",r"cannot.*25%.*causal",r"observed.*25%.*association",r"effect size.*not.*causal"]
}
BAD=[
 r"dataset (by itself )?(establishes|proves|confirms) .*causal",
 r"25% lower mortality (is|represents) the causal effect",
 r"we can conclude .*causally reduces"
]
def norm(s): return " ".join((s or "").lower().split())
def hits(text):
    t=norm(text); out=[]
    for k,pats in CORE.items():
        if any(re.search(p,t) for p in pats): out.append(k)
    return out
def critical_bad(text):
    t=norm(text)
    for p in BAD:
        m=re.search(p,t)
        if m:
            left=t[max(0,m.start()-50):m.start()]
            if not any(n in left for n in ["not ","cannot ","can't ","does not ","doesn't ","no "]):
                return True
    return False
def wave_score(recs):
    rows=[]; collective=set()
    for w in recs:
        h=hits(w.get("raw_output","")); collective.update(h); bad=critical_bad(w.get("raw_output",""))
        executed=bool(w.get("llm_inference") and w.get("inference")=="PASS")
        spiralix=bool(w.get("spiralix_envelope_sha256"))
        parsed=bool(w.get("parse_ok"))
        clean=not bool(w.get("prompt_echo"))
        coverage=len(h)/4.0
        role_pass=coverage>=0.5
        quality=(0.15*executed+0.10*spiralix+0.10*parsed+0.10*clean+0.20*(not bad)+0.20*coverage+0.15*role_pass)
        rows.append({"worker_id":w["worker_id"],"role_id":w["role_id"],"core_hits":h,"core_hit_count":len(h),"critical_causal_error":bad,"quality":round(float(quality),6)})
    q=sum(r["quality"] for r in rows)/len(rows) if rows else 0.0
    return {"q":round(q,6),"rows":rows,"collective_core_hits":sorted(collective),"collective_core_count":len(collective),"critical_errors":sum(r["critical_causal_error"] for r in rows)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--baseline-glob",required=True); ap.add_argument("--gvl-glob",required=True); ap.add_argument("--run-id",required=True); ap.add_argument("--output",required=True); args=ap.parse_args()
    base=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.baseline_glob,recursive=True)],key=lambda x:x["worker_id"])
    gvl=sorted([json.loads(Path(f).read_text()) for f in glob.glob(args.gvl_glob,recursive=True)],key=lambda x:x["worker_id"])
    b=wave_score(base); g=wave_score(gvl)
    gain=round(g["q"]-b["q"],6)
    ratio=None if b["q"]<=0 else round(g["q"]/b["q"],6)
    out={"schema":"CEREBRON_GVL_B3_ABLATION_SCORE_V1","run_id":args.run_id,"benchmark_family":"B3","baseline":b,"gvl":g,"quality_before":b["q"],"quality_after":g["q"],"transfer_gain":gain,"ratio":ratio,"novelty":1.0,"evidence_weight":1.0,"audit_pass":g["critical_errors"]==0,"effective_gain":round(max(0,gain)*1.0*1.0*(1 if g["critical_errors"]==0 else 0),6),"gvl_improved":gain>0 and g["critical_errors"]<=b["critical_errors"],"geometric_growth_claim":"DENY_REQUIRES_4_CONSECUTIVE_HELD_OUT_POSITIVE_RATIOS"}
    env=make_envelope("SPIRALION:A7_SYNTHESIZER","AGORA","GVL-B3-CAUSAL-CONFOUNDING-001","AUDIT",f"B3 baseline Q={b['q']}; GVL Q={g['q']}; gain={gain}; ratio={ratio}.",problem_ref="B3_CAUSAL_CONFOUNDING",evidence_level="E2",confidence=1.0,risk=.3,dependencies=[w.get("spiralix_envelope_sha256") for w in base+gvl if w.get("spiralix_envelope_sha256")],json_payload={k:v for k,v in out.items() if k not in {"baseline","gvl"}})
    out["spiralix_audit_envelope"]=env; out["spiralix_audit_envelope_sha256"]=sha256_obj(env)
    out["score_sha256"]=hashlib.sha256(json.dumps({k:v for k,v in out.items() if k!="score_sha256"},sort_keys=True,default=str).encode()).hexdigest()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"quality_before":b["q"],"quality_after":g["q"],"transfer_gain":gain,"ratio":ratio,"baseline_critical_errors":b["critical_errors"],"gvl_critical_errors":g["critical_errors"],"gvl_improved":out["gvl_improved"]},sort_keys=True))
if __name__=="__main__": main()
