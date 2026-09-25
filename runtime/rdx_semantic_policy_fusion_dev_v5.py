from __future__ import annotations
import hashlib,json,os,pathlib,re
from collections import Counter,defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer
from rdx_semantic_multilingual_ablation_dev_v4 import DOCS,QUERIES,FR_QUERIES,CRITICAL

BASE_ID="sentence-transformers/all-MiniLM-L6-v2"
BASE_REV="1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MULTI_ID="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MULTI_REV="e8f8c211226b894fcb81acc59f3b34ba3efd5f42"

STOP={
 "the","a","an","and","or","of","to","in","on","for","by","is","are","be","can","how","what","when","do","does","we","it","its","from","with","that","this",
 "le","la","les","un","une","des","de","du","et","ou","dans","sur","pour","par","est","sont","être","comment","quel","quelle","quels","quelles","ce","cette","ces"
}
def toks(s):
    return [x for x in re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ0-9]+",s.lower()) if x not in STOP and len(x)>1]

def lexical_scores(query,docs):
    dt=[toks(x) for x in docs]; q=toks(query); n=len(dt)
    df=Counter()
    for row in dt:
        for t in set(row): df[t]+=1
    idf={t:np.log((n+1)/(df[t]+1))+1.0 for t in df}
    arr=[]
    for row in dt:
        c=Counter(row)
        arr.append(sum(idf.get(t,np.log(n+1)+1.0)*(1.0+np.log(c[t])) for t in set(q) if c[t]>0))
    a=np.array(arr,dtype=float)
    return a/(a.max() if a.max()>0 else 1.0)

def ranks(scores):
    r=np.empty(len(scores),dtype=int)
    r[np.argsort(-scores)]=np.arange(1,len(scores)+1)
    return r

def rrf_weighted(parts,weights,k=60):
    out=np.zeros_like(parts[0],dtype=float)
    for p,w in zip(parts,weights):
        out += w/(k+ranks(p))
    return out

def minmax(a):
    lo=float(a.min()); hi=float(a.max())
    return np.zeros_like(a) if hi-lo<1e-12 else (a-lo)/(hi-lo)

def evaluate(score_rows,queries,corpus,name):
    correct=0; rr=[]; per=defaultdict(lambda:{"correct":0,"total":0}); rows=[]
    for q,scores in zip(queries,score_rows):
        order=np.argsort(-scores); ranked=[corpus[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        ok=rank==1; correct+=int(ok); rr.append(1.0/rank)
        per[q["expected"]]["total"]+=1; per[q["expected"]]["correct"]+=int(ok)
        rows.append({"id":q["id"],"lang":q["lang"],"expected":q["expected"],"top1":ranked[0]["domain"],"rank":rank,"ok":ok})
    critical_pass=all(per[d]["correct"]==per[d]["total"] for d in CRITICAL)
    return {"policy":name,"top1_correct":correct,"top1_accuracy":correct/len(queries),"mrr":sum(rr)/len(rr),"critical_domains_pass":critical_pass,"per_domain":dict(sorted(per.items())),"rows":rows}

def main():
    domains=sorted(DOCS)
    corpus=[{"id":f"DEV-D{i:02d}","domain":d,"text":DOCS[d][0]} for i,d in enumerate(domains,1)]
    en=[{"id":f"DEV-EN-Q{i:02d}","lang":"en","expected":d,"text":QUERIES[d][0]} for i,d in enumerate(domains,1)]
    fr=[{"id":f"DEV-FR-Q{i:02d}","lang":"fr","expected":d,"text":FR_QUERIES[d]} for i,d in enumerate(domains,1)]
    qs=en+fr; docs=[x["text"] for x in corpus]

    base=SentenceTransformer(BASE_ID,revision=BASE_REV,device="cpu")
    multi=SentenceTransformer(MULTI_ID,revision=MULTI_REV,device="cpu")
    be=base.encode(docs,normalize_embeddings=True,convert_to_numpy=True)
    me=multi.encode(docs,normalize_embeddings=True,convert_to_numpy=True)
    bq=base.encode([q["text"] for q in qs],normalize_embeddings=True,convert_to_numpy=True)
    mq=multi.encode([q["text"] for q in qs],normalize_embeddings=True,convert_to_numpy=True)
    bs=[np.dot(be,q) for q in bq]
    ms=[np.dot(me,q) for q in mq]
    ls=[lexical_scores(q["text"],docs) for q in qs]

    policies={
      "BASELINE_ONLY":bs,
      "MULTILINGUAL_ONLY":ms,
      "LANG_ROUTER":[ms[i] if q["lang"]=="fr" else bs[i] for i,q in enumerate(qs)],
      "RRF_BASE_MULTI":[rrf_weighted([bs[i],ms[i]],[1,1]) for i in range(len(qs))],
      "RRF_BASE_MULTI_LEX":[rrf_weighted([bs[i],ms[i],ls[i]],[1,1,0.75]) for i in range(len(qs))],
      "LANG_WEIGHTED_RRF":[
        rrf_weighted([bs[i],ms[i],ls[i]],[1.5,0.75,0.5] if q["lang"]=="en" else [0.75,1.5,0.5])
        for i,q in enumerate(qs)
      ],
      "LANG_WEIGHTED_BLEND":[
        (0.60*minmax(bs[i])+0.30*minmax(ms[i])+0.10*ls[i]) if q["lang"]=="en"
        else (0.25*minmax(bs[i])+0.65*minmax(ms[i])+0.10*ls[i])
        for i,q in enumerate(qs)
      ]
    }
    metrics={name:evaluate(rows,qs,corpus,name) for name,rows in policies.items()}
    base_all=metrics["BASELINE_ONLY"]
    base_en=evaluate(bs[:len(en)],en,corpus,"BASELINE_EN")
    base_fr=evaluate(bs[len(en):],fr,corpus,"BASELINE_FR")

    candidates=[]
    for name,m in metrics.items():
        if name=="BASELINE_ONLY": continue
        en_m=evaluate(policies[name][:len(en)],en,corpus,name+"_EN")
        fr_m=evaluate(policies[name][len(en):],fr,corpus,name+"_FR")
        robust=(
          m["top1_accuracy"]>base_all["top1_accuracy"]
          and m["mrr"]>=base_all["mrr"]
          and en_m["top1_accuracy"]>=base_en["top1_accuracy"]-0.0556
          and fr_m["top1_accuracy"]>base_fr["top1_accuracy"]
          and m["critical_domains_pass"]
        )
        candidates.append((robust,m["top1_accuracy"],m["mrr"],fr_m["top1_accuracy"],name,en_m,fr_m))

    passing=[x for x in candidates if x[0]]
    if passing:
        chosen=max(passing,key=lambda x:(x[1],x[2],x[3],x[4]))
        selected=chosen[4]
        decision="DEV_POLICY_PASS_FREEZE_FOR_FRESH_BILINGUAL_HOLDOUT_V5"
    else:
        selected="BASELINE_ONLY"
        decision="DEV_POLICY_HOLD_NO_ROBUST_FUSION_GAIN"

    detail={}
    for name,m in metrics.items():
        detail[name]={
          "overall":m,
          "en":evaluate(policies[name][:len(en)],en,corpus,name+"_EN"),
          "fr":evaluate(policies[name][len(en):],fr,corpus,name+"_FR")
        }

    out={
      "schema":"CEREBRON_RDX_SEMANTIC_POLICY_FUSION_DEV_V5",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "classification":"PUBLIC_DEV_POLICY_ABLATION_NOT_COLD",
      "source_v4_run_id":36164021509,
      "source_v4_receipt_sha256":"750eea725eb23e025f55fb8381da8c642db05852dd2d628315cfc91b0b6510fb",
      "models":[{"model_id":BASE_ID,"revision":BASE_REV},{"model_id":MULTI_ID,"revision":MULTI_REV}],
      "corpus_size":len(corpus),"query_count":len(qs),
      "policies":detail,
      "selected_policy":selected,
      "decision":decision,
      "fresh_holdout_consumed":False,
      "training":"NOT_EXECUTED","weights_changed":False,
      "claim_ceiling":"PUBLIC_BILINGUAL_DEV_POLICY_ABLATION_ONLY_NO_PRODUCTION_RAG_CLAIM"
    }
    out["receipt_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=pathlib.Path("receipts/rdx/rdx-semantic-policy-fusion-dev-v5.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"run_id":out["run_id"],"selected_policy":selected,"decision":decision,"receipt_sha256":out["receipt_sha256"]},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
