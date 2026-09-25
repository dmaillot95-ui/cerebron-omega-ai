from __future__ import annotations
import hashlib,json,os,pathlib,re,secrets,tempfile
from collections import Counter,defaultdict
import numpy as np
from huggingface_hub import HfApi,hf_hub_download
from sentence_transformers import SentenceTransformer

MODEL_ID="sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION="1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
POLICY="RRF_SEM_LEX"
SOURCE_DEV_RUN=36161040992
SOURCE_DEV_RECORD_SHA="91d3bac5ba9eb5a17f5925dcfbfbdb4276a864c78271eb45e62cfdb1c65136e2"

DOC_VARIANTS={
"orbital_assembly":[
"During orbital construction, a service robot can attach to a structural hardpoint before pushing or fastening so attitude thrusters are not used to resist every reaction force.",
"Space assembly equipment can brace against prepared interfaces before applying tools, reducing the need to counter construction loads with propellant."
],
"m6_isolation":[
"Cold evaluation material is quarantined from training. Hidden benchmark prompts, answers, paraphrases, and corrections derived from them are excluded from every training dataset.",
"A sealed benchmark remains evaluation-only; no content originating from its private questions may enter fine-tuning or adapter data."
],
"provenance":[
"A technical claim should point to its source, test, result, confidence, limitation, and version so an auditor can trace the evidence chain.",
"Research assertions keep canonical provenance links from the claim to supporting sources, executed tests, outcomes, uncertainty, and known limits."
],
"dedup":[
"Before evidence is counted, the knowledge system detects duplicate records and shared ancestry so repeated copies do not appear to be independent confirmation.",
"Research fusion records lineage and collapses duplicate findings before computing evidence counts."
],
"memory_governor":[
"A storage governor watches quota thresholds and can stop raw writes, drain queues, freeze durable memory, or switch the store to read-only mode.",
"Capacity protection escalates from warning and compression to write stop and freeze when memory usage crosses configured limits."
],
"semantic_retrieval":[
"Meaning-based retrieval embeds documents and questions so related engineering knowledge can be found even when the wording and vocabulary differ.",
"Vector retrieval searches by semantic similarity rather than depending only on exact token overlap."
],
"simulation_replay":[
"A reproducible simulation record stores the code version, configuration, random seed, inputs, outputs, and hashes needed to replay the run.",
"Simulation evidence is replayable only when its parameters, software revision, seed, artifacts, and checksums are retained."
],
"gold":[
"Training-grade GOLD knowledge requires validated provenance, deduplication, rights clearance, evidence gates, and explicit exclusion of cold benchmark material.",
"Only audited, licensed or owned, deduplicated research that passes promotion gates can become M4 GOLD training source material."
],
"rollback":[
"Before a neural update is promoted, the previous model or adapter checkpoint is retained so regressions can trigger rollback after cold evaluation.",
"A training campaign keeps the prior weights or adapter checkpoint and restores it if post-training benchmarks or transfer tests regress."
],
"tenant_privacy":[
"Customer research stays inside its tenant scope and is excluded from shared model training unless the contract explicitly grants that training right.",
"Private client data cannot be copied into common training datasets without explicit authorization and tenant-isolation controls."
],
"tool_routing":[
"A mission router selects the smallest useful set of tools and specialist models from dependency and provenance requirements instead of invoking every available agent.",
"Knowledge orchestration maps task dependencies and chooses only the relevant tools or specialist models needed to execute the mission."
],
"evidence_gate":[
"Promotion gates fail closed when reproduction, provenance, or scientific evidence is missing; a successful workflow alone is insufficient.",
"An evidence gate blocks promotion unless required tests and reproducibility checks pass, even when the automation itself completed successfully."
]
}

QUERY_VARIANTS={
"orbital_assembly":[
"How can a construction robot resist tool reaction forces in orbit without burning fuel for every push?",
"What lets an orbital assembly machine stay fixed while fastening a structure instead of using continuous thruster corrections?"
],
"m6_isolation":[
"How do we keep secret evaluation questions and their derived corrections out of fine-tuning data?",
"What rule prevents cold benchmark material from leaking into adapters or training sets?"
],
"provenance":[
"How can an auditor follow a research statement back through its source, test, outcome, uncertainty and limits?",
"What record links a technical assertion to the evidence chain that supports it?"
],
"dedup":[
"How do we stop copied findings with common ancestry from being counted as several independent confirmations?",
"What should collapse repeated research records before evidence is counted?"
],
"memory_governor":[
"What shuts down or freezes memory writes when storage approaches dangerous capacity?",
"Which control escalates from compression to write stop and read-only freeze as quotas fill?"
],
"semantic_retrieval":[
"How can the knowledge base find a relevant engineering result when my wording is very different from the stored text?",
"What retrieval method matches concepts by meaning instead of exact words?"
],
"simulation_replay":[
"What must be preserved so another run can reproduce the same simulation later?",
"Which metadata makes a numerical experiment replayable rather than just a screenshot of results?"
],
"gold":[
"What conditions must research satisfy before it can become approved training-quality GOLD data?",
"When is validated knowledge allowed to enter an M4 training-source library?"
],
"rollback":[
"What lets us restore the earlier model if a newly trained adapter performs worse?",
"Which safeguard reverses a neural update after cold benchmarks reveal regression?"
],
"tenant_privacy":[
"Can confidential customer R&D be used to train the shared models automatically?",
"What protects one client's private research from entering common training without contractual permission?"
],
"tool_routing":[
"How should the orchestrator choose only the specialists and tools actually needed for a task?",
"What mechanism avoids calling every agent by selecting a minimal useful tool coalition?"
],
"evidence_gate":[
"Why should a successful automation still be blocked from promotion when scientific verification is missing?",
"What fails closed when provenance or reproduction evidence is insufficient despite a green workflow?"
]
}

STOP={"the","a","an","and","or","of","to","in","on","for","by","is","are","be","can","how","what","when","do","does","we","it","its","from","with","that","this","into","only","every","which","should"}

def toks(s):
    return [x for x in re.findall(r"[a-z0-9]+",s.lower()) if x not in STOP and len(x)>1]

def lexical_scores(query,docs):
    dt=[toks(x) for x in docs]; q=toks(query); n=len(dt); df=Counter()
    for row in dt:
        for t in set(row): df[t]+=1
    idf={t:np.log((n+1)/(df[t]+1))+1.0 for t in df}
    qset=set(q); scores=[]
    for row in dt:
        c=Counter(row)
        score=sum(idf.get(t,np.log(n+1)+1.0)*(1.0+np.log(c[t])) for t in qset if c[t]>0)
        scores.append(float(score))
    a=np.array(scores,dtype=float)
    return a/(a.max() if a.max()>0 else 1.0)

def rrf(sem,lex,k=60):
    sr=np.empty(len(sem),dtype=int); lr=np.empty(len(lex),dtype=int)
    sr[np.argsort(-sem)]=np.arange(1,len(sem)+1)
    lr[np.argsort(-lex)]=np.arange(1,len(lex)+1)
    return 1.0/(k+sr)+1.0/(k+lr)

def canonical(x):
    return (json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()

def evaluate(scores_by_query,queries,corpus):
    correct=0; rr=[]; rows=[]; per=defaultdict(lambda:{"correct":0,"total":0})
    for q,scores in zip(queries,scores_by_query):
        order=np.argsort(-scores)
        ranked=[corpus[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        ok=rank==1; correct+=int(ok); rr.append(1.0/rank)
        per[q["expected"]]["total"]+=1; per[q["expected"]]["correct"]+=int(ok)
        rows.append({"query_id":q["id"],"expected":q["expected"],"top1":ranked[0]["domain"],"rank":rank,"ok":ok})
    return {"top1_correct":correct,"top1_accuracy":correct/len(queries),"mrr":sum(rr)/len(rr),"per_domain":dict(sorted(per.items())),"rows":rows}

def main():
    token=os.environ.get("HF_TOKEN",""); repo=os.environ.get("HF_REPO","")
    if not token: raise SystemExit("HF_TOKEN_MISSING")
    if not repo: raise SystemExit("HF_REPO_MISSING")
    api=HfApi(token=token)
    info=api.repo_info(repo_id=repo,repo_type="model")
    if not bool(getattr(info,"private",False)): raise SystemExit("HF_REPO_NOT_PRIVATE")

    # Exact variant choices are generated only at runtime and persisted privately.
    seed=secrets.randbits(64)
    rng=np.random.default_rng(seed)
    domains=sorted(DOC_VARIANTS)
    corpus=[]
    for i,d in enumerate(domains,1):
        opts=DOC_VARIANTS[d]
        corpus.append({"id":f"H2-D{i:02d}","domain":d,"text":opts[int(rng.integers(0,len(opts)))]})
    queries=[]
    qn=1
    for d in domains:
        opts=QUERY_VARIANTS[d]
        order=rng.permutation(len(opts))
        for oi in order[:2]:
            queries.append({"id":f"H2-Q{qn:02d}","expected":d,"text":opts[int(oi)]}); qn+=1
    rng.shuffle(queries)

    holdout={"schema":"CEREBRON_RDX_SEMANTIC_FRESH_HOLDOUT_V2","run_id":int(os.environ["GITHUB_RUN_ID"]),
             "classification":"FRESH_PRIVATE_RUNTIME_GENERATED","generator_family":"PUBLIC_VARIANT_FAMILY_EXACT_SELECTION_PRIVATE",
             "corpus":corpus,"queries":queries}
    hraw=canonical(holdout); hsha=hashlib.sha256(hraw).hexdigest()
    with tempfile.NamedTemporaryFile("wb",delete=False) as tf: tf.write(hraw); src=tf.name
    holdout_path=f"rdx/semantic-holdout-v2/run-{os.environ['GITHUB_RUN_ID']}/holdout.json"
    api.upload_file(path_or_fileobj=src,path_in_repo=holdout_path,repo_id=repo,repo_type="model",
                    commit_message=f"RDX semantic fresh holdout V2 {os.environ['GITHUB_RUN_ID']}")
    dst=pathlib.Path(hf_hub_download(repo_id=repo,filename=holdout_path,repo_type="model",token=token,force_download=True))
    if hashlib.sha256(dst.read_bytes()).hexdigest()!=hsha: raise SystemExit("HOLDOUT_READBACK_SHA_FAIL")

    model=SentenceTransformer(MODEL_ID,revision=MODEL_REVISION,device="cpu")
    docs=[x["text"] for x in corpus]
    ce=model.encode(docs,normalize_embeddings=True,convert_to_numpy=True)
    qe=model.encode([x["text"] for x in queries],normalize_embeddings=True,convert_to_numpy=True)
    sem=[np.dot(ce,q) for q in qe]
    lex=[lexical_scores(q["text"],docs) for q in queries]
    rrf_scores=[rrf(s,l) for s,l in zip(sem,lex)]

    base=evaluate(sem,queries,corpus)
    fused=evaluate(rrf_scores,queries,corpus)
    gain=fused["top1_accuracy"]-base["top1_accuracy"]
    critical={"m6_isolation","provenance","tenant_privacy","evidence_gate"}
    critical_pass=all(fused["per_domain"][d]["correct"]==fused["per_domain"][d]["total"] for d in critical)
    decision="FRESH_HOLDOUT_PASS_MEASURED_RETRIEVAL_GAIN" if (
        gain>0 and fused["top1_accuracy"]>=0.90 and fused["mrr"]>=0.95 and critical_pass
    ) else "FRESH_HOLDOUT_HOLD_NO_MEASURED_ROBUST_GAIN"

    private_result={"schema":"CEREBRON_RDX_SEMANTIC_FRESH_HOLDOUT_V2_PRIVATE_RESULT",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),"holdout_sha256":hsha,
      "baseline":base,"rrf_sem_lex":fused,"gain_over_semantic_only":gain,
      "critical_domains_pass":critical_pass,"decision":decision}
    praw=canonical(private_result); psha=hashlib.sha256(praw).hexdigest()
    with tempfile.NamedTemporaryFile("wb",delete=False) as tf: tf.write(praw); psrc=tf.name
    private_path=f"rdx/semantic-holdout-v2/run-{os.environ['GITHUB_RUN_ID']}/private-result.json"
    api.upload_file(path_or_fileobj=psrc,path_in_repo=private_path,repo_id=repo,repo_type="model",
                    commit_message=f"RDX semantic fresh holdout result {os.environ['GITHUB_RUN_ID']}")
    pdst=pathlib.Path(hf_hub_download(repo_id=repo,filename=private_path,repo_type="model",token=token,force_download=True))
    if hashlib.sha256(pdst.read_bytes()).hexdigest()!=psha: raise SystemExit("PRIVATE_RESULT_READBACK_SHA_FAIL")

    receipt={
      "schema":"CEREBRON_RDX_SEMANTIC_RETRIEVAL_FRESH_HOLDOUT_V2_RECEIPT",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "status":"PASS" if decision.startswith("FRESH_HOLDOUT_PASS") else "HOLD",
      "source_farm_id":152,"linked_memory_farm_id":115,
      "policy":POLICY,"policy_frozen_from_dev_run":SOURCE_DEV_RUN,
      "policy_dev_source_record_sha256":SOURCE_DEV_RECORD_SHA,
      "embedding_model_id":MODEL_ID,"embedding_model_revision":MODEL_REVISION,
      "holdout_classification":"FRESH_PRIVATE_RUNTIME_GENERATED",
      "holdout_exact_prompts_public":False,
      "holdout_generator_family_public":True,
      "holdout_sha256":hsha,"holdout_private_path":holdout_path,
      "private_result_sha256":psha,"private_result_path":private_path,
      "corpus_size":len(corpus),"query_count":len(queries),
      "semantic_only_top1_accuracy":base["top1_accuracy"],"semantic_only_mrr":base["mrr"],
      "rrf_sem_lex_top1_accuracy":fused["top1_accuracy"],"rrf_sem_lex_mrr":fused["mrr"],
      "gain_over_semantic_only":gain,"critical_domains_pass":critical_pass,
      "decision":decision,"fresh_holdout_consumed":True,
      "training":"NOT_EXECUTED","weights_changed":False,
      "claim_ceiling":"SYNTHETIC_PRIVATE_FRESH_HOLDOUT_RETRIEVAL_EVIDENCE_ONLY_NOT_PRODUCTION_SCALE_NOT_F115_FULL_RUNTIME"
    }
    receipt["receipt_sha256"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    out=pathlib.Path("receipts/rdx/rdx-semantic-retrieval-fresh-holdout-v2.json")
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
