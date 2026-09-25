from __future__ import annotations
import hashlib,json,os,pathlib,time
from collections import defaultdict
import numpy as np
from huggingface_hub import HfApi
from sentence_transformers import SentenceTransformer
from rdx_semantic_retrieval_independent_holdout_v3 import DOCS,QUERIES

CANDIDATES=[
  "sentence-transformers/all-MiniLM-L6-v2",
  "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]
FR_QUERIES={
"source_freshness":"Comment savoir si une source technique utilisée pour une réponse actuelle est devenue obsolète ?",
"claim_ceiling":"Quelle règle empêche de présenter une simulation comme une preuve plus forte que ce qu'elle démontre réellement ?",
"dimensional_consistency":"Quel contrôle détecte une équation dont les unités physiques ne sont pas cohérentes ?",
"failure_modes":"Quelle analyse recense les façons dont une conception peut tomber en panne, leurs effets et leurs mitigations ?",
"dependency_graph":"Comment représenter les dépendances entre données, outils, hypothèses et résultats d'une mission ?",
"licensing_rights":"Quel contrôle vérifie qu'un contenu externe peut légalement entrer dans un jeu de données d'entraînement ?",
"evidence_provenance":"Comment un auditeur peut-il remonter d'un résultat vers ses sources, tests, sorties et limitations ?",
"cold_benchmark":"Comment empêcher les questions d'un benchmark froid de contaminer les données d'entraînement ?",
"rollback":"Quel mécanisme permet de revenir aux poids ou à l'adapter précédent après une régression ?",
"tenant_privacy":"Comment empêcher les recherches privées d'un client d'entrer automatiquement dans l'entraînement partagé ?",
"dedup_lineage":"Comment éviter que plusieurs copies issues de la même recherche soient comptées comme preuves indépendantes ?",
"semantic_retrieval":"Comment retrouver une connaissance pertinente même si la question utilise des mots différents ?",
"replayability":"Que faut-il conserver pour pouvoir reproduire exactement une simulation ou un calcul plus tard ?",
"gold_promotion":"Quels contrôles doivent passer avant qu'une connaissance soit promue en M4 GOLD ?",
"memory_freeze":"Quel mécanisme bloque les écritures et gèle la mémoire quand les limites de stockage deviennent dangereuses ?",
"tool_routing":"Comment choisir uniquement les modèles et outils nécessaires à une mission au lieu de tout appeler ?",
"contradiction_tracking":"Comment conserver deux résultats contradictoires sans masquer le désaccord par un vote ?",
"versioning":"Comment corriger un objet de recherche sans effacer son historique ni sa provenance ?",
}
CRITICAL={"cold_benchmark","evidence_provenance","tenant_privacy","licensing_rights"}

def eval_scores(scores_by_query,queries,corpus):
    correct=0; rr=[]; per=defaultdict(lambda:{"correct":0,"total":0}); rows=[]
    for q,scores in zip(queries,scores_by_query):
        order=np.argsort(-scores)
        ranked=[corpus[int(i)] for i in order]
        rank=next(i+1 for i,x in enumerate(ranked) if x["domain"]==q["expected"])
        ok=rank==1
        correct+=int(ok); rr.append(1.0/rank)
        per[q["expected"]]["total"]+=1; per[q["expected"]]["correct"]+=int(ok)
        rows.append({"id":q["id"],"lang":q["lang"],"expected":q["expected"],"top1":ranked[0]["domain"],"rank":rank,"ok":ok})
    return {"top1_correct":correct,"top1_accuracy":correct/len(queries),"mrr":sum(rr)/len(rr),"per_domain":dict(sorted(per.items())),"rows":rows}

def main():
    api=HfApi(token=os.environ.get("HF_TOKEN") or None)
    domains=sorted(DOCS)
    corpus=[{"id":f"DEV-D{i:02d}","domain":d,"text":DOCS[d][0]} for i,d in enumerate(domains,1)]
    en_queries=[]; fr_queries=[]
    for i,d in enumerate(domains,1):
        en_queries.append({"id":f"DEV-EN-Q{i:02d}","lang":"en","expected":d,"text":QUERIES[d][0]})
        fr_queries.append({"id":f"DEV-FR-Q{i:02d}","lang":"fr","expected":d,"text":FR_QUERIES[d]})
    all_queries=en_queries+fr_queries

    results={}
    for mid in CANDIDATES:
        info=api.model_info(mid)
        rev=info.sha
        t0=time.time()
        model=SentenceTransformer(mid,revision=rev,device="cpu")
        ce=model.encode([x["text"] for x in corpus],normalize_embeddings=True,convert_to_numpy=True)
        qe=model.encode([x["text"] for x in all_queries],normalize_embeddings=True,convert_to_numpy=True)
        scores=[np.dot(ce,q) for q in qe]
        overall=eval_scores(scores,all_queries,corpus)
        en=eval_scores(scores[:len(en_queries)],en_queries,corpus)
        fr=eval_scores(scores[len(en_queries):],fr_queries,corpus)
        critical_pass=all(overall["per_domain"][d]["correct"]==overall["per_domain"][d]["total"] for d in CRITICAL)
        results[mid]={
          "model_id":mid,"revision":rev,"elapsed_s":round(time.time()-t0,3),
          "overall":overall,"en":en,"fr":fr,"critical_domains_pass":critical_pass
        }

    base=results[CANDIDATES[0]]
    multi=results[CANDIDATES[1]]
    fr_gain=multi["fr"]["top1_accuracy"]-base["fr"]["top1_accuracy"]
    overall_gain=multi["overall"]["top1_accuracy"]-base["overall"]["top1_accuracy"]
    en_regression=base["en"]["top1_accuracy"]-multi["en"]["top1_accuracy"]
    select=(
      fr_gain>0
      and overall_gain>=0
      and en_regression<=0.0556
      and multi["critical_domains_pass"]
      and multi["overall"]["mrr"]>=base["overall"]["mrr"]
    )
    decision="DEV_SELECT_MULTILINGUAL_FOR_FRESH_BILINGUAL_HOLDOUT" if select else "DEV_HOLD_BASELINE_NO_ROBUST_MULTILINGUAL_GAIN"
    out={
      "schema":"CEREBRON_RDX_SEMANTIC_MULTILINGUAL_ABLATION_DEV_V4",
      "run_id":int(os.environ["GITHUB_RUN_ID"]),
      "classification":"PUBLIC_DEV_ABLATION_NOT_COLD",
      "source_independent_v3_run_id":36161829258,
      "source_independent_v3_receipt_sha256":"4383fe6f1eb2894d68433004101a0fdb6d0449b67f1e540baa3f83bd90487516",
      "corpus_size":len(corpus),"query_count":len(all_queries),
      "query_languages":{"en":len(en_queries),"fr":len(fr_queries)},
      "candidates":results,
      "baseline_model":CANDIDATES[0],
      "multilingual_model":CANDIDATES[1],
      "fr_top1_gain":fr_gain,
      "overall_top1_gain":overall_gain,
      "en_top1_regression":en_regression,
      "decision":decision,
      "fresh_holdout_consumed":False,
      "training":"NOT_EXECUTED","weights_changed":False,
      "claim_ceiling":"PUBLIC_BILINGUAL_DEV_RETRIEVER_ABLATION_ONLY_NO_PRODUCTION_RAG_CLAIM"
    }
    out["receipt_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    p=pathlib.Path("receipts/rdx/rdx-semantic-multilingual-ablation-dev-v4.json")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="candidates"},sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
