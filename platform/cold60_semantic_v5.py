from __future__ import annotations

import hashlib
import itertools
import json
import math
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


def add(rows,tid,domain,prompt,kind,expected,tol=0):
    rows.append({"id":tid,"domain":domain,"prompt":prompt,"evaluator":{"type":kind,"expected":expected,"tol":tol}})


def build(seed):
    r=random.Random(seed); rows=[]

    # Math: new wording relative to V4.
    for i in range(4):
        a,b=r.randint(13,59),r.randint(9,41)
        prompt=r.choice([
            f"Give one numeral: {a} multiplied by {b}.",
            f"Calculate the product of {a} and {b}; numeral only.",
            f"{a} times {b} — output only the numeric result.",
        ])
        add(rows,f"M{i+1:02d}","math",prompt,"numeric",a*b)
    for i in range(4,7):
        a=r.randint(2,9); x=r.randint(3,21); b=r.randint(1,18); rhs=a*x+b
        add(rows,f"M{i+1:02d}","math",f"Solve x from {a}*x + {b} = {rhs}; give x only.","numeric",x)
    for i in range(7,9):
        g=r.randint(2,15); a=g*r.randint(3,8); b=g*r.randint(9,17)
        add(rows,f"M{i+1:02d}","math",f"GCD of {a}, {b}: output one integer.","numeric",math.gcd(a,b))
    pct=r.choice([5,10,12.5,20,25,40]); n=r.choice([80,120,160,200,240,320])
    add(rows,"M10","math",f"Return only the value of {pct}% of {n}.","numeric",pct*n/100,1e-9)

    # Code: no V4 instruction order.
    for i in range(10):
        a,b=r.randint(3,24),r.randint(2,18)
        expr=r.choice([
            f"({a}+{b})*2",
            f"abs(-{a})+{b}",
            f"max([{a},{b},{a+b}])",
            f"sorted([{a+b},{a},{b}])[1]",
        ])
        expected=eval(expr,{"__builtins__":{}},{"abs":abs,"max":max,"sorted":sorted})
        prompt=r.choice([
            f"Evaluate this Python expression = {expr}; output only the value.",
            f"Result of the Python expression: {expr}? Respond only with the result.",
            f"Python expression: {expr}; return the final value only.",
        ])
        add(rows,f"C{i+1:02d}","code",prompt,"numeric",expected)

    # Engineering: new phrasing.
    for i in range(5):
        m=r.randint(5,42); a=r.choice([1.25,1.75,2.25,3.0,3.75])
        add(rows,f"P{i+1:02d}","engineering",
            f"Mass {m} kg; acceleration {a} m/s^2. Compute force using mass times acceleration. One number only.",
            "numeric",m*a,1e-9)
    for i in range(5,10):
        f=r.randint(30,160); v=r.choice([0.5,0.75,1.25,1.5,2.25])
        add(rows,f"P{i+1:02d}","engineering",
            f"Force {f} N; velocity {v} m/s. Mechanical power is force times velocity. Return watts only.",
            "numeric",f*v,1e-9)

    # Grounded retrieval.
    for i in range(10):
        vals={k:f"{r.uniform(0.2,14.0):.4f}" for k in ("alpha","beta","gamma")}
        target=r.choice(list(vals))
        prompt=r.choice([
            f"DATA: alpha={vals['alpha']}; beta={vals['beta']}; gamma={vals['gamma']}. Using only DATA, give {target}.",
            f"CONTEXT: alpha: {vals['alpha']}; beta: {vals['beta']}; gamma: {vals['gamma']}. What is {target}? Answer only the stored value.",
        ])
        add(rows,f"R{i+1:02d}","research_grounded",prompt,"text",vals[target])

    # Planning: new option separators and wording.
    perms=list(itertools.permutations(["K","L","M"]))
    for i in range(10):
        correct=list(r.choice(perms)); first,second,last=correct
        wrong=[list(p) for p in perms if list(p)!=correct];r.shuffle(wrong)
        opts=[correct,wrong[0],wrong[1]];r.shuffle(opts)
        labels=["A","B","C"];ans=labels[opts.index(correct)].lower()
        if i%2:
            rendered="; ".join(f"{lab}: {'/'.join(seq)}" for lab,seq in zip(labels,opts))
        else:
            rendered=" | ".join(f"{lab}={'→'.join(seq)}" for lab,seq in zip(labels,opts))
        add(rows,f"L{i+1:02d}","planning",
            f"Select A, B, or C only. {first} is first and {second} must precede {last}. Candidate orders: {rendered}.",
            "text",ans)

    # Error detection: avoid the exact V4 sentence and separators.
    for i in range(10):
        labels=["A","B","C"];bad=r.randrange(3);claims=[]
        for j,lab in enumerate(labels):
            x,y=r.randint(3,22),r.randint(2,13);op=r.choice(["+","-","*"])
            truth=x+y if op=="+" else x-y if op=="-" else x*y
            shown=truth+(r.choice([-5,-3,-1,1,3,5]) if j==bad else 0)
            sep=":" if i%2 else ")"
            claims.append(f"{lab}{sep} {x}{op}{y}={shown}")
        add(rows,f"E{i+1:02d}","error_detection",
            "One arithmetic statement is incorrect. Return only its label. "+"; ".join(claims),
            "text",labels[bad].lower())

    assert len(rows)==60
    assert all(sum(t["domain"]==d for t in rows)==10 for d in DOMAINS)
    return rows


def run(tasks,mode):
    scores={d:{"passed":0,"total":0} for d in DOMAINS}; rows=[]; tool_hits=0
    for t in tasks:
        if mode=="SINGLE_MODEL":
            resp=generate(t["prompt"],max_new_tokens=32);answer=resp["generation"];emode="MODEL"
        else:
            resp=adaptive_execute(t["prompt"]);answer=resp.get("answer") or "";emode=resp.get("execution_mode")
            tool_hits+=int(emode=="DETERMINISTIC_SPECIALIST_TOOL")
        ok,norm=evaluate(answer,t["evaluator"])
        scores[t["domain"]]["total"]+=1;scores[t["domain"]]["passed"]+=int(ok)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":ok,"expected":t["evaluator"]["expected"],
                     "output":answer,"normalized":norm,"execution_mode":emode})
    score=sum(int(x["pass"]) for x in rows)
    return {"mode":mode,"score":score,"accuracy":score/60,"domain_scores":scores,"tool_hits":tool_hits,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_V5_SEED","2026092305"))
    tasks=build(seed)
    dataset={"schema":"CEREBRON_COLD60_SEMANTIC_HOLDOUT_V5","seed":seed,"memory_class":"M6_COLD_BENCHMARK",
             "deny_training":True,"created_after_v4_diagnosis":True,"tasks":tasks}
    started=time.perf_counter()
    base=run(tasks,"SINGLE_MODEL")
    adaptive=run(tasks,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    result={
        "schema":"CEREBRON_COLD60_SEMANTIC_HOLDOUT_V5_RESULT",
        "dataset_sha":canon(dataset),"seed":seed,"model_id":MODEL_ID,"revision":REVISION,
        "baseline":base,"adaptive":adaptive,"domains_improved":improved,
        "domains_improved_count":len(improved),"criterion_4_of_6":len(improved)>=4,
        "tool_hit_rate":adaptive["tool_hits"]/60,
        "tool_transfer_gate":adaptive["tool_hits"]>=48,
        "elapsed_s":round(time.perf_counter()-started,3),
        "limitations":[
            "post-fix runtime-seeded synthetic holdout; not external evaluation",
            "same developer authored system and holdout",
            "deterministic tool execution is not independent neural evidence",
            "deny_training=true",
        ],
    }
    result["result_sha256"]=canon(result)
    root=pathlib.Path("platform/artifacts");root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-semantic-v5-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-semantic-v5-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "seed":seed,"dataset_sha":result["dataset_sha"],"baseline_score":base["score"],
        "adaptive_score":adaptive["score"],"tool_hits":adaptive["tool_hits"],
        "domains_improved":improved,"criterion_4_of_6":result["criterion_4_of_6"],
        "tool_transfer_gate":result["tool_transfer_gate"],"result_sha256":result["result_sha256"],
    }))
    raise SystemExit(0 if result["criterion_4_of_6"] and result["tool_transfer_gate"] else 1)


if __name__=="__main__":
    main()
