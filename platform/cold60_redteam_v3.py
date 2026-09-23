from __future__ import annotations

import hashlib
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


def evaluate(output, ev):
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
    # Math: intentionally different language from V2 parser triggers.
    for i in range(5):
        a,b=r.randint(12,49),r.randint(12,49)
        out.append(task(f"M{i+1:02d}","math",f"Give just the numerical result of multiplying {a} by {b}.","numeric",a*b))
    for i in range(5,10):
        a=r.randint(2,9); x=r.randint(2,18); b=r.randint(1,15); c=a*x+b
        out.append(task(f"M{i+1:02d}","math",f"Find x in the equation {a}x + {b} = {c}. Reply with the number only.","numeric",x))

    # Code: alternative wording, still pure expressions.
    exprs=[]
    for _ in range(10):
        a,b=r.randint(2,25),r.randint(2,15)
        exprs.append((f"({a}+{b})*2",(a+b)*2))
    for i,(expr,val) in enumerate(exprs,1):
        out.append(task(f"C{i:02d}","code",f"Evaluate this Python expression and reply only with its result: {expr}","numeric",val))

    # Engineering: formula stated in prose rather than current tagged syntax.
    for i in range(5):
        m=r.randint(5,40); a=r.choice([1.5,2.0,2.5,3.0,4.0])
        out.append(task(f"P{i+1:02d}","engineering",f"A mass of {m} kg accelerates at {a} m/s^2. Using Newton's F=m*a relation, give only the force in N.","numeric",m*a,1e-9))
    for i in range(5,10):
        f=r.randint(20,150); v=r.choice([0.5,1.0,1.5,2.0,2.5])
        out.append(task(f"P{i+1:02d}","engineering",f"A force of {f} N acts along motion at {v} m/s. With mechanical power equal to force times speed, give only watts.","numeric",f*v,1e-9))

    # Grounded extraction: DATA instead of SOURCE and natural query.
    for i in range(10):
        aa,bb,cc=[f"{r.uniform(0.1,9.9):.3f}" for _ in range(3)]
        target=r.choice([("alpha",aa),("beta",bb),("gamma",cc)])
        out.append(task(f"R{i+1:02d}","research_grounded",
            f"DATA: alpha is {aa}; beta is {bb}; gamma is {cc}. Based strictly on DATA, answer with the value of {target[0]} and nothing else.",
            "text",target[1]))

    # Planning: natural constraints, options retain A/B/C but punctuation differs.
    import itertools
    perms=list(itertools.permutations(["K","L","M"]))
    for i in range(10):
        correct=list(r.choice(perms))
        first,second,last=correct
        wrong=[list(p) for p in perms if list(p)!=correct];r.shuffle(wrong)
        opts=[correct,wrong[0],wrong[1]];r.shuffle(opts)
        labels=["A","B","C"]; ans=labels[opts.index(correct)].lower()
        rendered=" | ".join(f"{lab}: {' > '.join(seq)}" for lab,seq in zip(labels,opts))
        out.append(task(f"L{i+1:02d}","planning",
            f"Choose only A, B, or C. {first} must be first, and {second} must occur before {last}. Candidate orders: {rendered}",
            "text",ans))

    # Error detection: "wrong" not "false", arithmetic equations.
    for i in range(10):
        labels=["A","B","C"]; wrong=r.randrange(3); claims=[]
        for j,lab in enumerate(labels):
            x,y=r.randint(2,20),r.randint(2,12); op=r.choice(["+","-","*"])
            truth=x+y if op=="+" else x-y if op=="-" else x*y
            shown=truth+(r.choice([-2,-1,1,2]) if j==wrong else 0)
            claims.append(f"{lab}) {x}{op}{y}={shown}")
        out.append(task(f"E{i+1:02d}","error_detection",
            "Which claim is wrong? Reply only with its letter. "+"; ".join(claims),
            "text",labels[wrong].lower()))
    assert len(out)==60
    return out


def run(tasks,mode):
    scores={d:{"passed":0,"total":0} for d in DOMAINS}; rows=[]; tool_hits=0
    for t in tasks:
        if mode=="SINGLE_MODEL":
            resp=generate(t["prompt"],max_new_tokens=32); answer=resp["generation"]; emode="MODEL"
        else:
            resp=adaptive_execute(t["prompt"]); answer=resp.get("answer") or ""; emode=resp.get("execution_mode")
            tool_hits += int(emode=="DETERMINISTIC_SPECIALIST_TOOL")
        ok,norm=evaluate(answer,t["evaluator"])
        scores[t["domain"]]["total"]+=1;scores[t["domain"]]["passed"]+=int(ok)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":ok,"expected":t["evaluator"]["expected"],"output":answer,"normalized":norm,"execution_mode":emode})
    score=sum(int(x["pass"]) for x in rows)
    return {"mode":mode,"score":score,"accuracy":score/60,"domain_scores":scores,"tool_hits":tool_hits,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_REDTEAM_SEED","2026092301"))
    tasks=build(seed)
    dataset={"schema":"CEREBRON_COLD_60_REDTEAM_V3","seed":seed,"memory_class":"M6_COLD_BENCHMARK","deny_training":True,"tasks":tasks}
    started=time.perf_counter()
    base=run(tasks,"SINGLE_MODEL")
    adaptive=run(tasks,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    out={
      "schema":"CEREBRON_COLD_60_REDTEAM_V3_RESULT",
      "dataset_sha":canon(dataset),
      "seed":seed,
      "model_id":MODEL_ID,
      "revision":REVISION,
      "baseline":base,
      "adaptive":adaptive,
      "domains_improved":improved,
      "domains_improved_count":len(improved),
      "criterion_4_of_6":len(improved)>=4,
      "red_team_question":"Does V2 performance transfer when prompt surface forms differ from specialist-tool trigger patterns?",
      "elapsed_s":round(time.perf_counter()-started,3),
      "limitations":[
        "runtime-seeded structured paraphrase holdout, not a general intelligence benchmark",
        "same benchmark author as system developer; not external independent evaluation",
        "exact instances are unseen before runtime, but task families remain synthetic",
        "tool fallback may use the same Qwen base model and is not independent evidence",
      ],
    }
    out["result_sha256"]=canon(out)
    root=pathlib.Path("platform/artifacts");root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-redteam-v3-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-redteam-v3-result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "schema":out["schema"],"dataset_sha":out["dataset_sha"],"seed":seed,
      "baseline_score":base["score"],"adaptive_score":adaptive["score"],
      "adaptive_tool_hits":adaptive["tool_hits"],"baseline_domains":base["domain_scores"],
      "adaptive_domains":adaptive["domain_scores"],"domains_improved":improved,
      "criterion_4_of_6":out["criterion_4_of_6"],"result_sha256":out["result_sha256"]
    },ensure_ascii=False))


if __name__=="__main__":
    main()
