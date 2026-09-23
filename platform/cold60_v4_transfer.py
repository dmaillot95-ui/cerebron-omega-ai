from __future__ import annotations

import hashlib
import itertools
import json
import os
import pathlib
import random
import re
import time

from coalition_tools import execute as adaptive_execute
from generative_backend import MODEL_ID, REVISION, generate

DOMAINS=("math","code","engineering","research_grounded","planning","error_detection")


def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def clean(v):
    x=str(v).strip().lower()
    if x.endswith("."): x=x[:-1].strip()
    if len(x)>=2 and x[0]==x[-1] and x[0] in "'\"": x=x[1:-1]
    return x


def evaluate(output,ev):
    x=clean(output)
    if ev["type"]=="text":
        return x==str(ev["expected"]).lower(),x
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?",x) is None:
        return False,x
    return abs(float(x)-float(ev["expected"]))<=max(float(ev.get("tol",0)),1e-9),x


def task(tid,domain,prompt,kind,expected,tol=0):
    return {"id":tid,"domain":domain,"prompt":prompt,"evaluator":{"type":kind,"expected":expected,"tol":tol}}


def build(seed):
    r=random.Random(seed); out=[]

    for i in range(5):
        a,b=r.randint(14,57),r.randint(11,43)
        out.append(task(f"M{i+1:02d}","math",
            f"Output one numeral only: the product of {a} and {b}.","numeric",a*b))
    for i in range(5,10):
        a=r.randint(2,9); x=r.randint(2,22); b=r.randint(1,17); c=a*x+b
        out.append(task(f"M{i+1:02d}","math",
            f"For the equation {a}*x + {b} = {c}, determine x; output the numeral only.","numeric",x))

    for i in range(10):
        a,b=r.randint(2,30),r.randint(2,20)
        expr=f"({a}*3)+({b}-2)"
        expected=(a*3)+(b-2)
        out.append(task(f"C{i+1:02d}","code",
            f"Python expression is {expr}. Output only its final value.","numeric",expected))

    for i in range(5):
        m=r.randint(6,45); a=r.choice([1.25,1.5,2.0,2.75,3.5])
        out.append(task(f"P{i+1:02d}","engineering",
            f"An object's mass is {m} kg and its acceleration is {a} m/s^2. Give only the Newtonian force in N.",
            "numeric",m*a,1e-9))
    for i in range(5,10):
        f=r.randint(25,180); v=r.choice([0.5,0.75,1.25,1.75,2.25])
        out.append(task(f"P{i+1:02d}","engineering",
            f"Force is {f} N and speed is {v} m/s. Give only the mechanical power in watts.",
            "numeric",f*v,1e-9))

    for i in range(10):
        aa,bb,cc=[f"{r.uniform(0.2,12.0):.4f}" for _ in range(3)]
        key,val=r.choice([("alpha",aa),("beta",bb),("gamma",cc)])
        out.append(task(f"R{i+1:02d}","research_grounded",
            f"FACTS: alpha:{aa}; beta:{bb}; gamma:{cc}. According to FACTS, report {key}.",
            "text",val))

    perms=list(itertools.permutations(["K","L","M"]))
    for i in range(10):
        correct=list(r.choice(perms))
        first,second,last=correct
        wrong=[list(p) for p in perms if list(p)!=correct];r.shuffle(wrong)
        opts=[correct,wrong[0],wrong[1]];r.shuffle(opts)
        labels=["A","B","C"]; ans=labels[opts.index(correct)].lower()
        rendered=" | ".join(f"{lab}: {' > '.join(seq)}" for lab,seq in zip(labels,opts))
        out.append(task(f"L{i+1:02d}","planning",
            f"Choose only A, B, or C. {first} must be first; {second} must occur before {last}. Proposals {rendered}",
            "text",ans))

    for i in range(10):
        labels=["A","B","C"]; wrong=r.randrange(3); claims=[]
        for j,lab in enumerate(labels):
            x,y=r.randint(3,25),r.randint(2,12); op=r.choice(["+","-","*"])
            truth=x+y if op=="+" else x-y if op=="-" else x*y
            shown=truth+(r.choice([-4,-2,-1,1,2,4]) if j==wrong else 0)
            claims.append(f"{lab}) {x}{op}{y}={shown}")
        out.append(task(f"E{i+1:02d}","error_detection",
            "Identify the incorrect claim and output only its letter. "+"; ".join(claims),
            "text",labels[wrong].lower()))

    assert len(out)==60
    assert all(sum(t["domain"]==d for t in out)==10 for d in DOMAINS)
    return out


def run(tasks,mode):
    scores={d:{"passed":0,"total":0} for d in DOMAINS}; rows=[]; tool_hits=0
    for t in tasks:
        if mode=="SINGLE_MODEL":
            resp=generate(t["prompt"],max_new_tokens=32);answer=resp["generation"];emode="MODEL"
        else:
            resp=adaptive_execute(t["prompt"]);answer=resp.get("answer") or "";emode=resp.get("execution_mode")
            tool_hits += int(emode=="DETERMINISTIC_SPECIALIST_TOOL")
        ok,norm=evaluate(answer,t["evaluator"])
        scores[t["domain"]]["total"]+=1;scores[t["domain"]]["passed"]+=int(ok)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":ok,"expected":t["evaluator"]["expected"],
                     "output":answer,"normalized":norm,"execution_mode":emode})
    score=sum(int(x["pass"]) for x in rows)
    return {"mode":mode,"score":score,"accuracy":score/60,"domain_scores":scores,"tool_hits":tool_hits,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_TRANSFER_V4_SEED","2026092304"))
    tasks=build(seed)
    dataset={"schema":"CEREBRON_COLD60_V4_TRANSFER","seed":seed,"memory_class":"M6_COLD_BENCHMARK",
             "deny_training":True,"created_after_v3_failure":True,"tasks":tasks}
    started=time.perf_counter()
    base=run(tasks,"SINGLE_MODEL")
    adaptive=run(tasks,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    result={
        "schema":"CEREBRON_COLD60_V4_TRANSFER_RESULT",
        "dataset_sha":canon(dataset),"seed":seed,"model_id":MODEL_ID,"revision":REVISION,
        "baseline":base,"adaptive":adaptive,
        "domains_improved":improved,"domains_improved_count":len(improved),
        "criterion_4_of_6":len(improved)>=4,
        "tool_transfer_gate":adaptive["tool_hits"]>=48,
        "elapsed_s":round(time.perf_counter()-started,3),
        "limitations":[
            "synthetic structured transfer benchmark, not general intelligence",
            "new runtime instances and prompt forms created after V3 failure",
            "deterministic tools are capabilities, not independent neural agents",
            "same repository author; not external evaluation",
        ],
    }
    result["result_sha256"]=canon(result)
    root=pathlib.Path("platform/artifacts");root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-v4-transfer-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-v4-transfer-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "seed":seed,"dataset_sha":result["dataset_sha"],"baseline_score":base["score"],
        "adaptive_score":adaptive["score"],"tool_hits":adaptive["tool_hits"],
        "domains_improved":improved,"criterion_4_of_6":result["criterion_4_of_6"],
        "tool_transfer_gate":result["tool_transfer_gate"],"result_sha256":result["result_sha256"],
    }))
    raise SystemExit(0 if result["criterion_4_of_6"] and result["tool_transfer_gate"] else 1)


if __name__=="__main__":
    main()
