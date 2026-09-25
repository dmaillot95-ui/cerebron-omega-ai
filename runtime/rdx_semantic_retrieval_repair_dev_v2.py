from __future__ import annotations
import hashlib,json,os,re,pathlib
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer
from runtime.rdx_semantic_retrieval_canary_v1 import CORPUS, QUERIES

MODEL_ID="sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION="1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
SOURCE_V1_RUN=36156985796
SOURCE_V1_RECEIPT_SHA="2cc40644334fbb7e2425194d26d400e5ab904c692860fa9973be56e94797ab30"

STOP={
 "the","a","an","and","or","of","to","in","on","for","by","is","are","be","can","how","what",
 "when","do","does","we","it","its","from","with","that","this","into","later","even","only"
}
def toks(s):
    return [x for x in re.findall(r"[a-z0-9]+",s.lower()) if x not in STOP and len(x)>1]

def lexical_scores(query,docs):
    dt=[toks(x) for x in docs]
    q=toks(query)
    n=len(dt)
    df=Counter()
    for row in dt:
        for t in set(row): df[t]+=1
    idf={t:np.log((n+1)/(df[t]+1))+1.0 for t in df}
    qset=set(q)
    scores=[]
    for row in dt:
        c=Counter(row)
        score=sum(idf.get(t,np.log(n+1)+1.0)*(1.0+np.log(c[t])) for t in qset if c[t]>0)
        scores.append(float(score))
    a=np.array(scores,dtype=float)
    return a/(a.max() if a.max()>0 else 1.0)

def minmax(a):
    lo=float(a.min()); hi=float(a.max())
    if hi-lo<1e-12: return np.zeros_like(a)
    return (a-lo)/(hi-lo)

def rrf(sem,lex,k=60):
    sr=np.empty(len(sem),dtype=int); lr=np.empty(len(lex),dtype=int)
    sr[np.argsort(-sem)]=np.arange(1,len(sem)+1)
    lr[np.argsort(-lex)]=np.arange(1,len(lex)+1)
    return 1.0/(k+sr)+1.0/(k+lr)

def evaluate(scores_by_query,name):
    results=[]; correct=0; rr=[]
    for q,scores in zip(QUERIES,scores_by_query):
        order=np.argsort(-scores)
        ranked=[CORPUS[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        top=ranked[0]; ok=top["domain"]==q["expected"]
        correct+=int(ok); rr.append(1/rank)
        results.append({"query_id":q["id"],"expected":q["expected"],"top1":top["domain"],"rank":rank,"ok":ok})
    return {"policy":name,"top1_correct":correct,"top1_accuracy":correct/len(QUERIES),"mrr":sum(rr)/len(rr),"results":results}

def main():
    model=SentenceTransformer(MODEL_ID,revision=MODEL_REVISION,device="cpu")
    docs=[x["text"] for x in CORPUS]
    ce=model.encode(docs,normalize_embeddings=True,convert_to_numpy=True)
    qe=model.encode([x["text"] for x in QUERIES],normalize_embeddings=True,convert_to_numpy=True)
    sem=[np.dot(ce,q) for q in qe]
    lex=[lexical_scores(q["text"],docs) for q in QUERIES]
    policies={}
    policies["SEMANTIC_ONLY"]=sem
    for lw in (0.25,0.50,0.75):
        policies[f"HYBRID_LEX_{int(lw*100)}"]=[
          (1-lw)*minmax(s)+lw*l for s,l in zip(sem,lex)
        ]
    policies["RRF_SEM_LEX"]=[rrf(s,l) for s,l in zip(sem,lex)]
    metrics={name:evaluate(scores,name) for name,scores in policies.items()}
    base=metrics["SEMANTIC_ONLY"]
    candidates=[v for k,v in metrics.items() if k!="SEMANTIC_ONLY"]
    selected=max(candidates,key=lambda x:(x["top1_accuracy"],x["mrr"],x["policy"]))
    gain=selected["top1_accuracy"]-base["top1_accuracy"]
    decision="DEV_POLICY_PASS_FREEZE_FOR_FRESH_HOLDOUT_V2" if (
      gain>0 and selected["top1_accuracy"]>=0.9 and selected["mrr"]>=0.9
    ) else "DEV_POLICY_HOLD_NO_ROBUST_GAIN"
    out={
      "schema":"CEREBRON_RDX_SEMANTIC_RETRIEVAL_REPAIR_DEV_V2",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "classification":"DEV_POLICY_TUNING_NOT_COLD",
      "source_v1_run_id":SOURCE_V1_RUN,
      "source_v1_receipt_sha256":SOURCE_V1_RECEIPT_SHA,
      "embedding_model_id":MODEL_ID,"embedding_model_revision":MODEL_REVISION,
      "corpus_size":len(CORPUS),"query_count":len(QUERIES),
      "candidate_policies":metrics,
      "baseline_policy":"SEMANTIC_ONLY",
      "baseline_top1_accuracy":base["top1_accuracy"],
      "baseline_mrr":base["mrr"],
      "selected_policy":selected["policy"],
      "selected_top1_accuracy":selected["top1_accuracy"],
      "selected_mrr":selected["mrr"],
      "gain_over_semantic_only":gain,
      "decision":decision,
      "fresh_holdout_consumed":False,
      "training":"NOT_EXECUTED","weights_changed":False,
      "claim_ceiling":"DEV_RETRIEVAL_POLICY_TUNING_ONLY; NO_PRODUCTION_RAG_CLAIM"
    }
    out["source_record_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=pathlib.Path("receipts/rdx/rdx-semantic-retrieval-repair-dev-v2.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
