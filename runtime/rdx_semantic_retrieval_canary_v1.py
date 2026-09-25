from __future__ import annotations
import hashlib, json, os, pathlib, tempfile
from typing import Any
import numpy as np
from huggingface_hub import HfApi, hf_hub_download
from sentence_transformers import SentenceTransformer

HF_REPO=os.environ["HF_REPO"]
HF_TOKEN=os.environ.get("HF_TOKEN","")
MODEL_ID=os.environ.get("EMBED_MODEL","sentence-transformers/all-MiniLM-L6-v2")

CORPUS=[
 {"id":"RDX-SEM-001","domain":"orbital_assembly","text":"Orbital assembly robots can reduce propellant use by anchoring magnetically or mechanically to structural interfaces before applying construction forces."},
 {"id":"RDX-SEM-002","domain":"m6_isolation","text":"M6 is a sealed cold benchmark and must never be used as a training source, including paraphrases or corrections derived from its hidden prompts."},
 {"id":"RDX-SEM-003","domain":"provenance","text":"Every important RDX claim should retain canonical links from claim to source, test, result, confidence and limitation."},
 {"id":"RDX-SEM-004","domain":"dedup","text":"Knowledge fusion must detect duplicate or shared-lineage research before counting items as independent evidence."},
 {"id":"RDX-SEM-005","domain":"memory_governor","text":"The memory governor monitors storage thresholds and can drain, freeze or make memory read-only when capacity limits are reached."},
 {"id":"RDX-SEM-006","domain":"semantic_retrieval","text":"Vector semantic memory retrieves technically related knowledge by embedding meaning rather than relying only on exact keyword matches."},
 {"id":"RDX-SEM-007","domain":"simulation_replay","text":"A replayable simulation record includes versioned configuration, seeds, inputs, outputs and hashes so the run can be reproduced."},
 {"id":"RDX-SEM-008","domain":"gold","text":"Only audited and rights-cleared knowledge that passes provenance, deduplication, F72 and AFAH may be promoted to M4 GOLD for training datasets."},
 {"id":"RDX-SEM-009","domain":"rollback","text":"A neural training campaign must preserve a rollback checkpoint and compare post-training cold benchmarks against the previous model."},
 {"id":"RDX-SEM-010","domain":"tenant_privacy","text":"Private client research remains tenant-scoped and is denied from shared training unless explicit contractual rights authorize it."},
 {"id":"RDX-SEM-011","domain":"tool_routing","text":"NEXUS connects knowledge dependencies and chooses the minimum relevant tools or specialist models needed for a mission."},
 {"id":"RDX-SEM-012","domain":"evidence_gate","text":"Evidence gates fail closed: workflow success alone does not justify promotion when scientific evidence or reproduction is missing."}
]
QUERIES=[
 {"id":"Q1","text":"How can a robot hold onto an orbital structure so it does not waste thruster fuel while building?","expected":"orbital_assembly"},
 {"id":"Q2","text":"What stops hidden evaluation questions from leaking into model training?","expected":"m6_isolation"},
 {"id":"Q3","text":"How do I trace a technical assertion back to its evidence and test result?","expected":"provenance"},
 {"id":"Q4","text":"How should repeated research with the same ancestry be prevented from looking like multiple proofs?","expected":"dedup"},
 {"id":"Q5","text":"What mechanism freezes memory when storage limits become dangerous?","expected":"memory_governor"},
 {"id":"Q6","text":"How can the encyclopedia find related engineering knowledge even when the wording is different?","expected":"semantic_retrieval"},
 {"id":"Q7","text":"What information is required to reproduce a simulation later?","expected":"simulation_replay"},
 {"id":"Q8","text":"When can validated research become training-quality GOLD data?","expected":"gold"},
 {"id":"Q9","text":"How do we recover if a new adapter makes the model worse?","expected":"rollback"},
 {"id":"Q10","text":"Can confidential customer research automatically train the shared models?","expected":"tenant_privacy"}
]

def canonical(x:Any)->bytes:
    return (json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()

def main()->int:
    if not HF_TOKEN:
        raise SystemExit("HF_TOKEN_MISSING")
    api=HfApi(token=HF_TOKEN)
    info=api.repo_info(repo_id=HF_REPO,repo_type="model")
    if not bool(getattr(info,"private",False)):
        raise SystemExit("HF_REPO_NOT_PRIVATE")

    rows=[]
    for item in CORPUS:
        obj={
          "schema":"RDX_ATOMIC_RECORD_V1",
          "rdx_id":"RDX-SEMANTIC-CANARY-V1",
          "object_id":item["id"],
          "object_type":"CLAIM",
          "domain":item["domain"],
          "content":item["text"],
          "provenance":{"origin":"CEREBRON_OWNED_SYNTHETIC","producer":"F152","source_ids":[f"SRC-{item['id']}"]},
          "rights":{"class":"OWNED","shared_training_allowed":False},
          "validated":True,"dedup_pass":True,"license_origin_pass":True,
          "m6_contamination":False,"memory_class":["M1","M7"],"training_eligible":False
        }
        raw=canonical(obj); sha=hashlib.sha256(raw).hexdigest()
        path=f"RDX_SHARED/M1/semantic-canary-v1/{sha}.json"
        with tempfile.NamedTemporaryFile("wb",delete=False) as tf:
            tf.write(raw); src=tf.name
        api.upload_file(path_or_fileobj=src,path_in_repo=path,repo_id=HF_REPO,repo_type="model",
                        commit_message=f"RDX semantic canary {item['id']}")
        dst=pathlib.Path(hf_hub_download(repo_id=HF_REPO,filename=path,repo_type="model",token=HF_TOKEN,force_download=True))
        if hashlib.sha256(dst.read_bytes()).hexdigest()!=sha:
            raise SystemExit(f"READBACK_SHA_FAIL:{item['id']}")
        rows.append({"id":item["id"],"domain":item["domain"],"sha256":sha,"path":path,"text":item["text"]})

    model_info=HfApi().model_info(MODEL_ID)
    revision=model_info.sha
    model=SentenceTransformer(MODEL_ID,revision=revision,device="cpu")
    corpus_emb=model.encode([x["text"] for x in rows],normalize_embeddings=True,convert_to_numpy=True)
    query_emb=model.encode([x["text"] for x in QUERIES],normalize_embeddings=True,convert_to_numpy=True)

    results=[]; top1_correct=0; reciprocal=[]
    for q,qe in zip(QUERIES,query_emb):
        sims=np.dot(corpus_emb,qe)
        order=np.argsort(-sims)
        ranked=[rows[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        top=ranked[0]
        ok=top["domain"]==q["expected"]
        top1_correct+=int(ok); reciprocal.append(1.0/rank)
        results.append({
          "query_id":q["id"],"expected_domain":q["expected"],
          "top1_domain":top["domain"],"top1_object_id":top["id"],
          "top1_score":round(float(sims[int(order[0])]),6),
          "expected_rank":rank,"top1_correct":ok
        })

    top1_accuracy=top1_correct/len(QUERIES)
    mrr=sum(reciprocal)/len(reciprocal)
    status="PASS" if top1_accuracy>=0.9 and mrr>=0.9 else "FAIL"
    corpus_manifest_sha=hashlib.sha256(canonical([
      {"id":x["id"],"domain":x["domain"],"sha256":x["sha256"]} for x in rows
    ])).hexdigest()

    receipt={
      "schema":"CEREBRON_RDX_SEMANTIC_RETRIEVAL_CANARY_V1",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "status":status,
      "source_farm_id":152,
      "linked_memory_farm_id":115,
      "repo":HF_REPO,"repo_private":True,
      "embedding_model_id":MODEL_ID,"embedding_model_revision":revision,
      "corpus_size":len(rows),"query_count":len(QUERIES),
      "corpus_manifest_sha256":corpus_manifest_sha,
      "authenticated_write_read_sha":"PASS",
      "top1_correct":top1_correct,"top1_accuracy":top1_accuracy,
      "mean_reciprocal_rank":mrr,
      "results":results,
      "training":"NOT_EXECUTED",
      "weights_changed":False,
      "claim_ceiling":"SYNTHETIC_PRIVATE_RDX_SEMANTIC_RETRIEVAL_CANARY_ONLY_NOT_PRODUCTION_SCALE_NOT_F115_FULL_RUNTIME"
    }
    receipt["receipt_sha256"]=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    out=pathlib.Path("receipts/rdx/rdx-semantic-retrieval-canary-v1.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0 if status=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
