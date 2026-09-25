from __future__ import annotations
import hashlib,json,os,pathlib,secrets,tempfile
from collections import defaultdict
import numpy as np
from huggingface_hub import HfApi,hf_hub_download
from sentence_transformers import SentenceTransformer

MODEL_ID="sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION="1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
POLICY="SEMANTIC_ONLY"
SOURCE_SELECTION_RUN=36161387023
SOURCE_SELECTION_RECEIPT="04a93068314f1740d27c150f20e79f3fd6ec46f9dd1ccd6f412d33d6380c3bcd"

DOCS={
"source_freshness":[
"Technical sources carry publication and retrieval dates so time-sensitive claims can be rechecked when the underlying information may have changed.",
"Freshness metadata identifies when evidence was published, observed, and last verified before it supports a current claim."
],
"claim_ceiling":[
"A conclusion must not be stronger than the evidence that supports it; uncertainty and untested scope remain explicit in the final claim.",
"Claim ceilings prevent an experiment or simulation from being described as proof beyond the conditions actually tested."
],
"dimensional_consistency":[
"Engineering equations are checked so units balance across every term before a numerical result is accepted.",
"Dimensional analysis catches formulas that combine incompatible physical quantities or inconsistent unit conversions."
],
"failure_modes":[
"Design reviews enumerate credible failure modes, triggers, consequences, detection signals, and mitigations before qualification.",
"Failure analysis records how a component or architecture can fail and what evidence would reveal the degraded state."
],
"dependency_graph":[
"Mission knowledge is represented as a dependency graph linking prerequisites, tools, data, claims, and downstream decisions.",
"Dependency tracking prevents a result from being promoted when one of its required upstream assumptions or artifacts is missing."
],
"licensing_rights":[
"External material enters training only when its origin and license or ownership rights allow that use.",
"Rights checks distinguish owned, licensed, public, and restricted sources before they are admitted to training datasets."
],
"evidence_provenance":[
"Every important result retains canonical identifiers for its sources, executed tests, outputs, confidence, limitations, and version history.",
"Provenance links let an auditor trace a technical result back through the evidence chain that produced it."
],
"cold_benchmark":[
"Cold benchmark questions and answers remain sealed and excluded from all training, tuning, prompt-derived correction, and adapter datasets.",
"Evaluation-only material is isolated so model improvement cannot come from memorizing hidden benchmark content."
],
"rollback":[
"Model releases keep the previous weights or adapter checkpoint so a regression can be reversed after post-training evaluation.",
"A rollback path restores the earlier neural artifact when a new training campaign reduces capability or transfer performance."
],
"tenant_privacy":[
"Private customer research remains tenant-scoped and cannot enter shared model training without explicit contractual authorization.",
"Tenant isolation prevents one client's confidential research from becoming reusable shared training data by default."
],
"dedup_lineage":[
"Duplicate and shared-lineage research is collapsed before evidence counts are computed so copies do not look independent.",
"Lineage-aware deduplication identifies repeated findings that descend from the same source or execution."
],
"semantic_retrieval":[
"Embedding-based retrieval finds technically related knowledge by meaning even when the user's vocabulary differs from stored wording.",
"Semantic search compares vector representations of questions and records instead of requiring exact lexical matches."
],
"replayability":[
"Reproducible computational evidence stores code revision, configuration, seed, inputs, outputs, and checksums needed to replay the run.",
"A replay receipt preserves enough deterministic state to recreate a simulation or computation later."
],
"gold_promotion":[
"Knowledge becomes GOLD only after provenance, deduplication, rights, evidence gates, and benchmark-contamination checks pass.",
"M4 GOLD is a curated training-source class reached only after validation and fail-closed promotion gates."
],
"memory_freeze":[
"Memory governance can drain queues, stop raw writes, freeze durable state, or enforce read-only mode when quota thresholds are exceeded.",
"Storage protection escalates to freeze when capacity or integrity limits make further writes unsafe."
],
"tool_routing":[
"An orchestrator chooses the smallest useful set of specialist models and tools required by the mission dependency graph.",
"Tool routing avoids invoking every available agent and selects only capabilities relevant to the current task."
],
"contradiction_tracking":[
"Conflicting research claims remain linked as an explicit contradiction until additional evidence resolves or narrows the disagreement.",
"Knowledge fusion preserves unresolved disagreements rather than erasing them through majority voting."
],
"versioning":[
"Research objects are versioned so corrections create traceable successors while prior evidence and decisions remain reproducible.",
"Version history records how a claim, test, dataset, or decision changed without silently overwriting its earlier state."
]
}

QUERIES={
"source_freshness":[
"How do we know whether evidence supporting a current answer has become outdated?",
"What metadata tells us when a technical source was published and last rechecked?"
],
"claim_ceiling":[
"What rule stops a simulation result from being described as stronger proof than it really is?",
"How should conclusions remain limited to the scope actually supported by evidence?"
],
"dimensional_consistency":[
"What check catches an equation whose physical units do not balance?",
"How can we detect a formula that mixes incompatible engineering dimensions?"
],
"failure_modes":[
"What analysis lists ways a design can break, their consequences, warning signs, and mitigations?",
"Where do we record credible degraded states before qualification testing?"
],
"dependency_graph":[
"How do we represent which data, tools, assumptions, and earlier results a mission depends on?",
"What stops a downstream result from passing when an upstream prerequisite is missing?"
],
"licensing_rights":[
"What check determines whether external material is legally allowed to enter a training dataset?",
"How do we distinguish owned or licensed sources from restricted content before model training?"
],
"evidence_provenance":[
"How can an auditor trace a result back to its sources, tests, outputs, uncertainty and limitations?",
"Which links preserve the full evidence chain behind a technical conclusion?"
],
"cold_benchmark":[
"What prevents hidden evaluation content from leaking into fine-tuning or adapter data?",
"How are sealed benchmark questions kept evaluation-only rather than becoming training examples?"
],
"rollback":[
"What lets us restore the previous neural artifact when a new adapter causes regression?",
"Which safeguard reverses a model update after post-training tests get worse?"
],
"tenant_privacy":[
"Can one customer's confidential research automatically become training data for everyone?",
"What control keeps private client knowledge isolated from shared model training?"
],
"dedup_lineage":[
"How do we stop repeated copies of the same research ancestry from counting as independent proof?",
"What identifies findings that look separate but descend from the same source?"
],
"semantic_retrieval":[
"How can the encyclopedia find relevant knowledge when I phrase the question with different words?",
"What search method retrieves related concepts by meaning rather than exact vocabulary?"
],
"replayability":[
"What must be saved so another machine can reproduce the same simulation run later?",
"Which run metadata makes computational evidence replayable?"
],
"gold_promotion":[
"When is research allowed to become curated M4 training-source knowledge?",
"What gates must pass before validated information is promoted to GOLD?"
],
"memory_freeze":[
"What mechanism stops writes and freezes durable memory when storage limits become unsafe?",
"Which governor can drain queues and switch memory to read-only mode?"
],
"tool_routing":[
"How should the system choose only the specialists and tools actually needed for a mission?",
"What prevents the orchestrator from calling every available agent for every task?"
],
"contradiction_tracking":[
"How should the knowledge base handle two validated claims that still disagree?",
"What preserves an unresolved conflict instead of hiding it through voting?"
],
"versioning":[
"How can a corrected research object replace an older one without erasing its history?",
"What records the evolution of claims and decisions across revisions?"
]
}

def canonical(x):
    return (json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()

def evaluate(scores_by_query,queries,corpus):
    correct=0; rr=[]; per=defaultdict(lambda:{"correct":0,"total":0}); rows=[]
    for q,scores in zip(queries,scores_by_query):
        order=np.argsort(-scores); ranked=[corpus[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        ok=rank==1; correct+=int(ok); rr.append(1.0/rank)
        per[q["expected"]]["total"]+=1; per[q["expected"]]["correct"]+=int(ok)
        rows.append({"id":q["id"],"expected":q["expected"],"top1":ranked[0]["domain"],"rank":rank,"ok":ok})
    return {"top1_correct":correct,"top1_accuracy":correct/len(queries),"mrr":sum(rr)/len(rr),"per_domain":dict(sorted(per.items())),"rows":rows}

def main():
    token=os.environ.get("HF_TOKEN",""); repo=os.environ.get("HF_REPO","")
    if not token: raise SystemExit("HF_TOKEN_MISSING")
    if not repo: raise SystemExit("HF_REPO_MISSING")
    api=HfApi(token=token)
    info=api.repo_info(repo_id=repo,repo_type="model")
    if not bool(getattr(info,"private",False)): raise SystemExit("HF_REPO_NOT_PRIVATE")

    seed=secrets.randbits(64); rng=np.random.default_rng(seed)
    domains=sorted(DOCS)
    corpus=[]
    for i,d in enumerate(domains,1):
        opts=DOCS[d]
        corpus.append({"id":f"V3-D{i:02d}","domain":d,"text":opts[int(rng.integers(0,len(opts)))]})
    queries=[]; qn=1
    for d in domains:
        order=rng.permutation(len(QUERIES[d]))
        for oi in order[:2]:
            queries.append({"id":f"V3-Q{qn:02d}","expected":d,"text":QUERIES[d][int(oi)]}); qn+=1
    rng.shuffle(queries)

    holdout={"schema":"CEREBRON_RDX_SEMANTIC_INDEPENDENT_HOLDOUT_V3","run_id":int(os.environ["GITHUB_RUN_ID"]),
             "classification":"INDEPENDENT_PRIVATE_RUNTIME_GENERATED_AFTER_POLICY_SELECTION",
             "policy":POLICY,"corpus":corpus,"queries":queries}
    hraw=canonical(holdout); hsha=hashlib.sha256(hraw).hexdigest()
    with tempfile.NamedTemporaryFile("wb",delete=False) as tf: tf.write(hraw); src=tf.name
    hpath=f"rdx/semantic-holdout-v3/run-{os.environ['GITHUB_RUN_ID']}/holdout.json"
    api.upload_file(path_or_fileobj=src,path_in_repo=hpath,repo_id=repo,repo_type="model",
                    commit_message=f"RDX semantic independent holdout V3 {os.environ['GITHUB_RUN_ID']}")
    dst=pathlib.Path(hf_hub_download(repo_id=repo,filename=hpath,repo_type="model",token=token,force_download=True))
    if hashlib.sha256(dst.read_bytes()).hexdigest()!=hsha: raise SystemExit("HOLDOUT_READBACK_SHA_FAIL")

    model=SentenceTransformer(MODEL_ID,revision=MODEL_REVISION,device="cpu")
    ce=model.encode([x["text"] for x in corpus],normalize_embeddings=True,convert_to_numpy=True)
    qe=model.encode([x["text"] for x in queries],normalize_embeddings=True,convert_to_numpy=True)
    scores=[np.dot(ce,q) for q in qe]
    metrics=evaluate(scores,queries,corpus)

    critical={"cold_benchmark","evidence_provenance","tenant_privacy","licensing_rights"}
    critical_pass=all(metrics["per_domain"][d]["correct"]==metrics["per_domain"][d]["total"] for d in critical)
    decision="INDEPENDENT_HOLDOUT_PASS_SEMANTIC_BASELINE" if (
        metrics["top1_accuracy"]>=0.90 and metrics["mrr"]>=0.95 and critical_pass
    ) else "INDEPENDENT_HOLDOUT_HOLD_SEMANTIC_BASELINE"

    private={"schema":"CEREBRON_RDX_SEMANTIC_INDEPENDENT_HOLDOUT_V3_PRIVATE_RESULT",
             "run_id":int(os.environ["GITHUB_RUN_ID"]),"holdout_sha256":hsha,
             "metrics":metrics,"critical_domains_pass":critical_pass,"decision":decision}
    praw=canonical(private); psha=hashlib.sha256(praw).hexdigest()
    with tempfile.NamedTemporaryFile("wb",delete=False) as tf: tf.write(praw); psrc=tf.name
    ppath=f"rdx/semantic-holdout-v3/run-{os.environ['GITHUB_RUN_ID']}/private-result.json"
    api.upload_file(path_or_fileobj=psrc,path_in_repo=ppath,repo_id=repo,repo_type="model",
                    commit_message=f"RDX semantic independent result V3 {os.environ['GITHUB_RUN_ID']}")
    pdst=pathlib.Path(hf_hub_download(repo_id=repo,filename=ppath,repo_type="model",token=token,force_download=True))
    if hashlib.sha256(pdst.read_bytes()).hexdigest()!=psha: raise SystemExit("PRIVATE_RESULT_READBACK_SHA_FAIL")

    receipt={
      "schema":"CEREBRON_RDX_SEMANTIC_INDEPENDENT_HOLDOUT_V3_RECEIPT",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "status":"PASS" if decision.startswith("INDEPENDENT_HOLDOUT_PASS") else "HOLD",
      "source_farm_id":152,"linked_memory_farm_id":115,
      "policy":POLICY,
      "policy_selected_after_fresh_holdout_run":SOURCE_SELECTION_RUN,
      "source_selection_receipt_sha256":SOURCE_SELECTION_RECEIPT,
      "embedding_model_id":MODEL_ID,"embedding_model_revision":MODEL_REVISION,
      "holdout_classification":"INDEPENDENT_PRIVATE_RUNTIME_GENERATED_AFTER_POLICY_SELECTION",
      "holdout_exact_prompts_public":False,"holdout_generator_family_public":True,
      "holdout_sha256":hsha,"holdout_private_path":hpath,
      "private_result_sha256":psha,"private_result_path":ppath,
      "corpus_size":len(corpus),"query_count":len(queries),
      "top1_correct":metrics["top1_correct"],"top1_accuracy":metrics["top1_accuracy"],
      "mrr":metrics["mrr"],"critical_domains_pass":critical_pass,
      "decision":decision,
      "training":"NOT_EXECUTED","weights_changed":False,
      "claim_ceiling":"INDEPENDENT_SYNTHETIC_PRIVATE_SEMANTIC_RETRIEVAL_VALIDATION_ONLY_NOT_PRODUCTION_SCALE_NOT_F115_FULL_RUNTIME"
    }
    receipt["receipt_sha256"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    out=pathlib.Path("receipts/rdx/rdx-semantic-retrieval-independent-holdout-v3.json")
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
