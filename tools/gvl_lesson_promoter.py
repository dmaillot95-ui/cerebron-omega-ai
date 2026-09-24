#!/usr/bin/env python3
import argparse,json,math,re,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GVL=ROOT/"config/geometric-vector-learning-v1.json"
REG=ROOT/"config/gvl-specialization-registry-v2.json"
IDX=ROOT/"memory/gvl-lesson-index.json"

def norm_text(s):
    return re.sub(r"[^A-Z0-9]+","_",str(s).upper()).strip("_")

def cos(a,b):
    dot=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    return 0.0 if na==0 or nb==0 else max(-1.0,min(1.0,dot/(na*nb)))

def source_vector(ai_id,reg):
    for x in reg["ais"]:
        if x["ai_id"]==ai_id:
            return x["specialization_vector"]
    raise KeyError(f"UNKNOWN_AI:{ai_id}")

def evaluate(candidate):
    g=json.loads(GVL.read_text())
    reg=json.loads(REG.read_text())
    idx=json.loads(IDX.read_text())
    inv=norm_text(candidate["invariant"])
    coax={norm_text(x):x for x in g["coaxial_axis"]["invariants"]}
    existing={norm_text(x["invariant"]):x for x in idx["lessons"]}
    vec=candidate.get("specialization_vector") or source_vector(candidate["source_ai"],reg)
    result={
      "lesson_id":candidate["lesson_id"],
      "normalized_invariant":inv,
      "specialization_vector":vec,
      "decision":None,
      "reason":None,
      "novelty_score":None,
      "effective_gain":0.0
    }
    if inv in coax:
        result.update(decision="MERGED_REDUNDANT",reason="COAXIAL_INVARIANT_EXISTS",novelty_score=0.0,merged_into=f"coaxial:{coax[inv]}")
        return result
    if inv in existing:
        result.update(decision="MERGED_REDUNDANT",reason="LESSON_INVARIANT_EXISTS",novelty_score=0.0,merged_into=f"lesson:{existing[inv]['lesson_id']}")
        return result

    promoted=[x for x in idx["lessons"] if x.get("promotion_status")=="PROMOTED_VALIDATED" and x.get("specialization_vector")]
    max_red=max((cos(vec,x["specialization_vector"]) for x in promoted),default=0.0)
    novelty=1-max_red
    transfer_gain=candidate.get("transfer_gain")
    evidence_level=int(str(candidate.get("evidence_level","E0")).replace("E","") or 0)
    counter_audit=bool(candidate.get("counter_audit_pass"))
    audit=bool(candidate.get("audit_pass"))
    evidence_weight=min(1.0,evidence_level/8)
    effective=max(0.0,float(transfer_gain or 0.0))*novelty*evidence_weight*(1.0 if audit and counter_audit else 0.0)
    result.update(novelty_score=round(novelty,6),max_redundancy=round(max_red,6),effective_gain=round(effective,6))

    if novelty < float(g["promotion_gates"]["novelty_floor"]):
        result.update(decision="MERGED_REDUNDANT",reason="NOVELTY_BELOW_FLOOR")
    elif transfer_gain is None:
        result.update(decision="TRANSFER_PENDING",reason="TRANSFER_GAIN_MISSING")
    elif float(transfer_gain)<=0:
        result.update(decision="REJECTED",reason="NON_POSITIVE_TRANSFER_GAIN")
    elif evidence_level<2:
        result.update(decision="REJECTED",reason="EVIDENCE_BELOW_E2")
    elif not audit or not counter_audit:
        result.update(decision="TRANSFER_PENDING",reason="AUDIT_OR_COUNTER_AUDIT_PENDING")
    elif effective<=0:
        result.update(decision="REJECTED",reason="NON_POSITIVE_EFFECTIVE_GAIN")
    else:
        result.update(decision="PROMOTED_VALIDATED",reason="ALL_GVL_GATES_PASS")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--output")
    args=ap.parse_args()
    c=json.loads(Path(args.candidate).read_text())
    out=evaluate(c)
    out["decision_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    s=json.dumps(out,indent=2)+"\n"
    if args.output:
        p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
    print(s,end="")
if __name__=="__main__": main()
