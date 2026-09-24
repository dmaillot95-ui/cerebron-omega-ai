#!/usr/bin/env python3
import argparse,glob,hashlib,json,re
from pathlib import Path

def tok(s):
    return set(re.findall(r"[a-z0-9_]{3,}",(s or "").lower()))
def jac(a,b):
    A=tok(a); B=tok(b)
    return 0.0 if not A or not B else len(A&B)/len(A|B)
def normtag(t): return t.lower().replace("_"," ")
def text_of(r):
    p=r.get("parsed") or {}
    return " ".join(str(p.get(k,"")) for k in ["PRIORITY","PROPOSAL","TEST","STOP","UNIQUE_VALUE","BENCHMARK","DUAL_CORE","RISK"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--glob",required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    rs=[json.loads(Path(p).read_text()) for p in glob.glob(a.glob,recursive=True)]
    rs.sort(key=lambda r:r.get("ai_id",""))
    texts=[text_of(r) for r in rs]
    rows=[]
    for i,r in enumerate(rs):
        p=r.get("parsed") or {}
        maxred=max([jac(texts[i],texts[j]) for j in range(len(rs)) if j!=i] or [0.0])
        novelty=1-maxred
        required=["PRIORITY","PROPOSAL","TEST","STOP","UNIQUE_VALUE","BENCHMARK","DUAL_CORE","RISK"]
        structure=sum(bool(p.get(k)) for k in required)/len(required)
        low=texts[i].lower()
        tags=r.get("specialization_tags") or []
        taghits=sum(1 for t in tags if normtag(t) in low or t.lower() in low)
        role_fidelity=taghits/max(1,len(tags))
        action_words=["test","benchmark","measure","audit","run","verify","compare","ablation","metric","gate"]
        actionability=min(1.0,sum(1 for w in action_words if w in low)/5)
        clean=1.0 if r.get("parse_ok") and not r.get("prompt_echo") else 0.0
        utility=0.25*structure+0.25*actionability+0.20*role_fidelity+0.20*novelty+0.10*clean
        rows.append({
          "ai_id":r.get("ai_id"),"identity":r.get("identity"),"executed":bool(r.get("llm_inference")),
          "parse_ok":bool(r.get("parse_ok")),"role_fidelity_proxy":round(role_fidelity,4),
          "actionability_proxy":round(actionability,4),"novelty_proxy":round(novelty,4),
          "max_redundancy_proxy":round(maxred,4),"future_utility_proxy":round(utility,4),
          "priority":p.get("PRIORITY"),"proposal":p.get("PROPOSAL"),"test":p.get("TEST"),
          "stop":p.get("STOP"),"unique_value":p.get("UNIQUE_VALUE"),"benchmark":p.get("BENCHMARK"),
          "dual_core":p.get("DUAL_CORE"),"risk":p.get("RISK")
        })
    ranked=sorted(rows,key=lambda x:x["future_utility_proxy"],reverse=True)
    lineages=set(r.get("lineage_fingerprint") for r in rs if r.get("lineage_fingerprint"))
    out={
      "schema":"CEREBRON_ALL_AI_STRATEGY_COUNCIL_AUDIT_V1","run_id":a.run_id,
      "requested_count":38,"receipt_count":len(rs),"executed_count":sum(x["executed"] for x in rows),
      "parse_pass_count":sum(x["parse_ok"] for x in rows),"unique_lineage_fingerprints":len(lineages),
      "independent_evidence_count":0,
      "evidence_note":"Shared runtime/model outputs are correlated advisory perspectives, not independent evidence.",
      "score_note":"future_utility_proxy is a deterministic descriptive heuristic, not a capability proof.",
      "rows":rows,"top_10_by_proxy":[x["ai_id"] for x in ranked[:10]],
      "bottom_10_by_proxy":[x["ai_id"] for x in ranked[-10:]],
      "mean_future_utility_proxy":round(sum(x["future_utility_proxy"] for x in rows)/max(1,len(rows)),4)
    }
    out["audit_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k not in ["rows"]},ensure_ascii=False,sort_keys=True))
if __name__=="__main__": main()
