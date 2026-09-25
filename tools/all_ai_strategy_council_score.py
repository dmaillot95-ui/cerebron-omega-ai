#!/usr/bin/env python3
import argparse,glob,hashlib,json,re
from pathlib import Path

FIELDS=["PRIORITY","PROPOSAL","TEST","STOP","UNIQUE_VALUE","BENCHMARK","DUAL_CORE","RISK"]

def tokens(s):
    s=(s or "").lower().replace("_"," ")
    return set(re.findall(r"[a-z0-9]{3,}",s))

def jac(a,b):
    A=tokens(a); B=tokens(b)
    return 0.0 if not A or not B else len(A&B)/len(A|B)

def text_of(r):
    p=r.get("parsed") or {}
    return " ".join(str(p.get(k,"")) for k in FIELDS)

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
        executed=bool(r.get("llm_inference"))
        parse_ok=bool(r.get("parse_ok"))
        prompt_echo=bool(r.get("prompt_echo"))
        scorable=executed and parse_ok and not prompt_echo
        maxred=max([jac(texts[i],texts[j]) for j in range(len(rs)) if j!=i and texts[j]] or [0.0])
        novelty=max(0.0,1.0-maxred)
        coverage=sum(bool(p.get(k)) for k in FIELDS)/len(FIELDS)
        low=texts[i].lower()
        role_ref=(r.get("parent_function") or "")+" "+" ".join((r.get("specialization_tags") or []))
        R=tokens(role_ref); O=tokens(texts[i])
        role_alignment=(len(R&O)/len(R)) if R else 0.0
        action_terms={"test","benchmark","measure","audit","run","verify","compare","ablation","metric","gate","retest","held","rollback"}
        actionability=min(1.0,len(action_terms & O)/6.0)
        specificity=0.0
        if re.search(r"\b\d+(?:\.\d+)?\b",texts[i]): specificity+=0.25
        if any(x in low for x in ["sha","run id","run_id","artifact","held-out","held out","same scale","baseline"]): specificity+=0.35
        if p.get("TEST") and p.get("BENCHMARK"): specificity+=0.20
        if p.get("RISK") and p.get("STOP"): specificity+=0.20
        specificity=min(1.0,specificity)
        utility=None
        if scorable:
            utility=0.20*coverage+0.20*actionability+0.20*role_alignment+0.15*novelty+0.15*specificity+0.10
        rows.append({
          "ai_id":r.get("ai_id"),"identity":r.get("identity"),"executed":executed,
          "parse_ok":parse_ok,"scorable":scorable,
          "coverage_proxy":round(coverage,4),
          "role_alignment_proxy":round(role_alignment,4),
          "actionability_proxy":round(actionability,4),
          "specificity_proxy":round(specificity,4),
          "novelty_proxy":round(novelty,4),
          "max_redundancy_proxy":round(maxred,4),
          "future_utility_proxy":None if utility is None else round(utility,4),
          "priority":p.get("PRIORITY"),"proposal":p.get("PROPOSAL"),"test":p.get("TEST"),
          "stop":p.get("STOP"),"unique_value":p.get("UNIQUE_VALUE"),"benchmark":p.get("BENCHMARK"),
          "dual_core":p.get("DUAL_CORE"),"risk":p.get("RISK")
        })
    scorable_rows=[x for x in rows if x["scorable"]]
    ranked=sorted(scorable_rows,key=lambda x:x["future_utility_proxy"],reverse=True)
    lineages=set(r.get("lineage_fingerprint") for r in rs if r.get("lineage_fingerprint"))
    out={
      "schema":"CEREBRON_ALL_AI_STRATEGY_COUNCIL_AUDIT_V2","run_id":a.run_id,
      "requested_count":38,"receipt_count":len(rs),"executed_count":sum(x["executed"] for x in rows),
      "parse_pass_count":sum(x["parse_ok"] for x in rows),"scorable_count":len(scorable_rows),
      "unique_lineage_fingerprints":len(lineages),"independent_evidence_count":0,
      "evidence_note":"Shared runtime/model outputs are correlated advisory perspectives, not independent evidence.",
      "score_note":"All scores are deterministic descriptive proxies for this mission only. Unparseable outputs are UNSCORABLE, never assigned a fallback score.",
      "rows":rows,
      "ranked_scorable_by_proxy":[x["ai_id"] for x in ranked],
      "mean_future_utility_proxy":None if not ranked else round(sum(x["future_utility_proxy"] for x in ranked)/len(ranked),4)
    }
    out["audit_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="rows"},ensure_ascii=False,sort_keys=True))
if __name__=="__main__": main()
