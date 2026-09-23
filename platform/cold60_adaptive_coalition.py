from __future__ import annotations

import json
import pathlib
import time

from cold60_single_model import TASKS, DOMAINS, DATASET_SHA, canonical_sha, evaluate
from coalition import execute

def main():
    started=time.perf_counter()
    domain_scores={d:{"passed":0,"total":0} for d in DOMAINS}
    results=[]
    coalition_sizes=[]
    independent_counts=[]
    for task in TASKS:
        response=execute(task["prompt"])
        answer=response.get("answer") or ""
        passed,normalized=evaluate(answer,task["evaluator"])
        domain_scores[task["domain"]]["total"]+=1
        domain_scores[task["domain"]]["passed"]+=int(passed)
        plan=response["plan"]
        coalition_sizes.append(len(plan["selected_units"]))
        independent_counts.append(plan["independent_model_count"])
        results.append({
            "id":task["id"],
            "domain":task["domain"],
            "pass":passed,
            "expected":task["evaluator"]["expected"],
            "output":answer,
            "normalized":normalized,
            "status":response["status"],
            "selected_units":plan["selected_units"],
            "independent_model_count":plan["independent_model_count"],
            "shared_dependencies":plan["shared_dependencies"],
            "claim_ceiling":response["claim_ceiling"],
        })
    score=sum(int(x["pass"]) for x in results)
    out={
        "schema":"CEREBRON_COLD_60_RESULT_V1",
        "mode":"ADAPTIVE_COALITION",
        "coalition_semantics":"MINIMAL_V2_NO_UNSELECTED_MEMORY_BASE_GENERATOR_SEPARATE",
        "dataset_schema":"CEREBRON_COLD_60_V1",
        "dataset_sha":DATASET_SHA,
        "memory_class":"M6_COLD_BENCHMARK",
        "deny_training":True,
        "score":score,
        "max_score":60,
        "accuracy":score/60,
        "domain_scores":domain_scores,
        "average_logical_coalition_size":sum(coalition_sizes)/len(coalition_sizes),
        "max_logical_coalition_size":max(coalition_sizes),
        "max_independent_model_count":max(independent_counts),
        "results":results,
        "elapsed_s":round(time.perf_counter()-started,3),
        "limitations":[
            "model specialists share Qwen/Qwen2.5-0.5B-Instruct and are correlated",
            "router, memory retrieval, deterministic Red Team and fusion are not independent neural models",
            "research tasks use provided sources rather than live web access",
            "this benchmark measures task accuracy, not general intelligence",
        ],
    }
    out["result_sha256"]=canonical_sha(out)
    target=pathlib.Path("platform/artifacts/cold60-adaptive-coalition-v1.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":out["schema"],
        "mode":out["mode"],
        "dataset_sha":out["dataset_sha"],
        "score":out["score"],
        "max_score":out["max_score"],
        "accuracy":out["accuracy"],
        "domain_scores":out["domain_scores"],
        "average_logical_coalition_size":out["average_logical_coalition_size"],
        "max_logical_coalition_size":out["max_logical_coalition_size"],
        "max_independent_model_count":out["max_independent_model_count"],
        "elapsed_s":out["elapsed_s"],
        "result_sha256":out["result_sha256"],
    },ensure_ascii=False))

if __name__=="__main__":
    main()
