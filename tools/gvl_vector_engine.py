#!/usr/bin/env python3
import argparse,json,math,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config/geometric-vector-learning-v1.json"

def load():
    return json.loads(CFG.read_text())

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(sum(x*x for x in a))
def cosine(a,b):
    na,nb=norm(a),norm(b)
    if na==0 or nb==0: return 0.0
    return max(-1.0,min(1.0,dot(a,b)/(na*nb)))

def pairwise(cfg):
    ais=[x for x in cfg["ais"] if x["available"]]
    rows=[]
    for i in range(len(ais)):
        for j in range(i+1,len(ais)):
            s=cosine(ais[i]["specialization_vector"],ais[j]["specialization_vector"])
            rows.append({
                "ai_a":ais[i]["ai_id"],"ai_b":ais[j]["ai_id"],
                "redundancy":round(s,6),
                "complementarity":round(1-s,6),
                "overlap_tags":sorted(set(ais[i]["specialization_tags"]) & set(ais[j]["specialization_tags"]))
            })
    return rows

def greedy_select(cfg,k=5):
    ais=[x for x in cfg["ais"] if x["available"]]
    # deterministic seed: most dimensions active, then ai_id
    ais=sorted(ais,key=lambda x:(-len(x["specialization_tags"]),x["ai_id"]))
    selected=[ais[0]]
    remaining=ais[1:]
    while remaining and len(selected)<k:
        best=None
        best_score=-1
        for cand in remaining:
            sims=[cosine(cand["specialization_vector"],s["specialization_vector"]) for s in selected]
            novelty=1-max(sims) if sims else 1.0
            breadth=len(cand["specialization_tags"])/len(cfg["vector_space"]["basis"])
            score=0.8*novelty+0.2*breadth
            key=(score,cand["ai_id"])
            if best is None or key>(best_score,best["ai_id"]):
                best=cand;best_score=score
        selected.append(best);remaining=[x for x in remaining if x["ai_id"]!=best["ai_id"]]
    return [{
        "rank":i+1,"ai_id":x["ai_id"],"identity":x["identity"],
        "specialization_tags":x["specialization_tags"],
        "novelty_vs_previous":1.0 if i==0 else round(1-max(cosine(x["specialization_vector"],p["specialization_vector"]) for p in selected[:i]),6)
    } for i,x in enumerate(selected)]

def growth_status(history):
    cycles=history.get("cycles",[])
    transferable=[c for c in cycles if c.get("held_out_transfer") and c.get("quality_after") is not None and c.get("quality_before") is not None]
    ratios=[]
    for c in transferable:
        before=float(c["quality_before"]);after=float(c["quality_after"])
        ratios.append(None if before<=0 else after/before)
    valid=[r for r in ratios if r is not None]
    last4=valid[-4:]
    geometric_like=len(last4)>=4 and all(r>1.0 for r in last4) and all(c.get("critical_regression_count",0)==0 for c in transferable[-4:])
    return {
        "transfer_cycles":len(transferable),
        "ratios":[round(r,6) for r in valid],
        "last4":[round(r,6) for r in last4],
        "geometric_like_claim_allowed":geometric_like,
        "status":"MEASURED_GEOMETRIC_LIKE" if geometric_like else "INSUFFICIENT_OR_NON_GEOMETRIC",
        "required_min_cycles":4
    }

def canary():
    cfg=load()
    pairs=pairwise(cfg)
    max_pair=max(pairs,key=lambda x:x["redundancy"]) if pairs else None
    min_pair=min(pairs,key=lambda x:x["redundancy"]) if pairs else None
    selection=greedy_select(cfg,5)
    hist_path=ROOT/"memory/gvl-learning-history.json"
    history=json.loads(hist_path.read_text()) if hist_path.exists() else {"cycles":[]}
    growth=growth_status(history)
    out={
        "schema":"CEREBRON_GVL_CANARY_V1",
        "status":"PASS",
        "logical_ai":cfg["counts"]["logical_ai"],
        "available_ai":cfg["counts"]["available_ai"],
        "vector_dimension":cfg["vector_space"]["dimension"],
        "pair_count":len(pairs),
        "highest_redundancy_pair":max_pair,
        "highest_complementarity_pair":min_pair,
        "nonredundant_example_selection":selection,
        "growth":growth,
        "checks":{
            "all_available_have_vectors":all(len(x["specialization_vector"])==cfg["vector_space"]["dimension"] for x in cfg["ais"] if x["available"]),
            "vectors_finite":all(all(math.isfinite(float(v)) for v in x["specialization_vector"]) for x in cfg["ais"]),
            "growth_not_overclaimed":not growth["geometric_like_claim_allowed"] if growth["transfer_cycles"]<4 else True
        }
    }
    assert all(out["checks"].values())
    body=json.dumps(out,sort_keys=True,separators=(",",":"))
    out["receipt_sha256"]=hashlib.sha256(body.encode()).hexdigest()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--canary",action="store_true")
    ap.add_argument("--output")
    ap.add_argument("--select",type=int)
    args=ap.parse_args()
    cfg=load()
    if args.select:
        print(json.dumps(greedy_select(cfg,args.select),indent=2))
        return
    if args.canary:
        out=canary()
        s=json.dumps(out,indent=2)+"\n"
        if args.output:
            p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
        print(json.dumps({k:v for k,v in out.items() if k not in {"nonredundant_example_selection"}},sort_keys=True))
if __name__=="__main__": main()
