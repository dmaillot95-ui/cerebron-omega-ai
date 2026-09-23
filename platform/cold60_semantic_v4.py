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

    # Math — surface forms not used in the semantic-dispatch unit tests.
    for i in range(3):
        a,b=r.randint(12,48),r.randint(12,48)
        forms=[
            f"Return just the result: {a} times {b}.",
            f"Find the product of {a} with {b}; output one number.",
            f"Multiply {a} by {b} and respond with the numeric answer only.",
        ]
        add(rows,f"M{i+1:02d}","math",forms[i], "numeric",a*b)
    for i in range(3,6):
        a=r.randint(2,9); x=r.randint(2,18); b=r.randint(1,15); rhs=a*x+b
        add(rows,f"M{i+1:02d}","math",f"Determine x from {a}x + {b} = {rhs}. Number only.","numeric",x)
    for i in range(6,8):
        g=r.randint(2,12); a=g*r.randint(3,9); b=g*r.randint(10,16)
        add(rows,f"M{i+1:02d}","math",f"Give the greatest common divisor of {a} and {b}, with no explanation.","numeric",math.gcd(a,b))
    for i in range(8,10):
        pct=r.choice([5,10,20,25,40]); n=r.choice([80,120,160,200,240])
        add(rows,f"M{i+1:02d}","math",f"How much is {pct}% of {n}? Reply with one number.","numeric",pct*n/100,1e-9)

    # Code — alternate instruction order, pure restricted expressions.
    for i in range(10):
        a,b=r.randint(2,20),r.randint(2,15)
        expr=r.choice([
            f"({a}+{b})*3",
            f"abs(-{a})+{b}",
            f"max([{a},{b},{a+b}])",
            f"sorted([{a+b},{a},{b}])[1]",
        ])
        expected=eval(expr,{"__builtins__":{}},{"abs":abs,"max":max,"sorted":sorted})
        prompt=r.choice([
            f"Compute this Python expression: {expr}. Return only its value.",
            f"What is the value of the Python expression: {expr}? Answer only with the result.",
            f"Python expression: {expr}. Give the result only.",
        ])
        add(rows,f"C{i+1:02d}","code",prompt,"numeric",expected)

    # Engineering — symbolic and prose mixes.
    engineering=[]
    for _ in range(2):
        m=r.randint(4,30); a=r.choice([1.5,2.0,2.5,3.5])
        engineering.append((f"A system has mass {m} kg and acceleration {a} m/s^2. Force equals mass times acceleration. Return force only.",m*a))
    for _ in range(2):
        f=r.randint(25,140); v=r.choice([0.5,1.0,1.5,2.5])
        engineering.append((f"Mechanical power equals force times velocity. Force {f} N, velocity {v} m/s. Give watts only.",f*v))
    for _ in range(2):
        p=r.randint(100,700); t=r.randint(10,120)
        engineering.append((f"Energy equals power times duration. Power {p} W and duration {t} seconds. Return joules only.",p*t))
    for _ in range(2):
        iamp=r.choice([1.2,2.0,2.5,3.0]); resistance=r.choice([2,4,5,8])
        engineering.append((f"Voltage follows V=I*R. Current {iamp} A and resistance {resistance} ohms. Return volts only.",iamp*resistance))
    for _ in range(2):
        period=r.choice([0.01,0.02,0.04,0.05,0.1])
        engineering.append((f"Frequency uses f=1/T. Period {period} s. Return hertz only.",1/period))
    for i,(prompt,ans) in enumerate(engineering,1):
        add(rows,f"P{i:02d}","engineering",prompt,"numeric",ans,1e-9)

    # Grounded retrieval — CONTEXT/FACTS and key:value notation.
    for i in range(10):
        vals={k:f"{r.uniform(0.1,9.9):.3f}" for k in ("alpha","beta","gamma")}
        target=r.choice(list(vals))
        prefix=r.choice(["CONTEXT","FACTS"])
        prompt=r.choice([
            f"{prefix}: alpha: {vals['alpha']}; beta: {vals['beta']}; gamma: {vals['gamma']}. According to this {prefix.lower()}, what is {target}? Return only the stored value.",
            f"{prefix}: alpha={vals['alpha']}; beta={vals['beta']}; gamma={vals['gamma']}. From this {prefix.lower()}, return only {target}.",
        ])
        add(rows,f"R{i+1:02d}","research_grounded",prompt,"text",vals[target])

    # Planning — semantic constraints with different option separators.
    perms=list(itertools.permutations(["K","L","M"]))
    for i in range(10):
        correct=list(r.choice(perms)); first,second,last=correct
        wrong=[list(p) for p in perms if list(p)!=correct]; r.shuffle(wrong)
        opts=[correct,wrong[0],wrong[1]]; r.shuffle(opts)
        labels=["A","B","C"]; ans=labels[opts.index(correct)].lower()
        if i%2==0:
            option_text="; ".join(f"{lab}=" + "/".join(seq) for lab,seq in zip(labels,opts))
            constraints=f"{first} is first; {second} precedes {last}"
        else:
            option_text=" | ".join(f"{lab}: " + " > ".join(seq) for lab,seq in zip(labels,opts))
            constraints=f"{first} must be first; {second} must come before {last}"
        add(rows,f"L{i+1:02d}","planning",f"Choose A, B, or C only. Constraints: {constraints}. Candidate sequence options: {option_text}.","text",ans)

    # Error detection — varied synonym, arithmetic claims.
    for i in range(10):
        labels=["A","B","C"]; bad=r.randrange(3); claims=[]
        for j,lab in enumerate(labels):
            x,y=r.randint(2,20),r.randint(2,12); op=r.choice(["+","-","*"])
            truth=x+y if op=="+" else x-y if op=="-" else x*y
            shown=truth+(r.choice([-3,-2,-1,1,2,3]) if j==bad else 0)
            sep=":" if i%2==0 else ")"
            claims.append(f"{lab}{sep} {x}{op}{y}={shown}")
        adjective=r.choice(["incorrect","invalid","wrong","false"])
        add(rows,f"E{i+1:02d}","error_detection",f"Identify the {adjective} arithmetic claim. Answer only with A, B, or C. "+"; ".join(claims), "text",labels[bad].lower())

    assert len(rows)==60
    assert all(sum(t["domain"]==d for t in rows)==10 for d in DOMAINS)
    return rows


def run(tasks,mode):
    scores={d:{"passed":0,"total":0} for d in DOMAINS}; rows=[]; tool_hits=0
    for t in tasks:
        if mode=="SINGLE_MODEL":
            resp=generate(t["prompt"],max_new_tokens=32); answer=resp["generation"]; emode="MODEL"
        else:
            resp=adaptive_execute(t["prompt"]); answer=resp.get("answer") or ""; emode=resp.get("execution_mode")
            tool_hits+=int(emode=="DETERMINISTIC_SPECIALIST_TOOL")
        ok,norm=evaluate(answer,t["evaluator"])
        scores[t["domain"]]["total"]+=1; scores[t["domain"]]["passed"]+=int(ok)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":ok,"expected":t["evaluator"]["expected"],"output":answer,"normalized":norm,"execution_mode":emode})
    score=sum(int(x["pass"]) for x in rows)
    return {"mode":mode,"score":score,"accuracy":score/60,"domain_scores":scores,"tool_hits":tool_hits,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_V4_SEED","2026092302"))
    tasks=build(seed)
    dataset={"schema":"CEREBRON_COLD_60_SEMANTIC_HOLDOUT_V4","seed":seed,"memory_class":"M6_COLD_BENCHMARK","deny_training":True,"tasks":tasks}
    started=time.perf_counter()
    base=run(tasks,"SINGLE_MODEL")
    adaptive=run(tasks,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    out={
      "schema":"CEREBRON_COLD_60_SEMANTIC_HOLDOUT_V4_RESULT",
      "dataset_sha":canon(dataset),"seed":seed,"model_id":MODEL_ID,"revision":REVISION,
      "baseline":base,"adaptive":adaptive,"domains_improved":improved,
      "domains_improved_count":len(improved),"criterion_4_of_6":len(improved)>=4,
      "semantic_transfer_tool_hit_rate":adaptive["tool_hits"]/60,
      "elapsed_s":round(time.perf_counter()-started,3),
      "limitations":[
        "semantic-dispatch implementation was frozen before this holdout benchmark file was created",
        "same developer authored implementation and holdout; not an external independent evaluation",
        "synthetic structured tasks; not a general intelligence metric",
        "exact instances are runtime-seeded and deny_training=true",
      ],
    }
    out["result_sha256"]=canon(out)
    root=pathlib.Path("platform/artifacts"); root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-semantic-v4-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-semantic-v4-result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
      "schema":out["schema"],"dataset_sha":out["dataset_sha"],"seed":seed,
      "baseline_score":base["score"],"adaptive_score":adaptive["score"],
      "tool_hits":adaptive["tool_hits"],"tool_hit_rate":out["semantic_transfer_tool_hit_rate"],
      "baseline_domains":base["domain_scores"],"adaptive_domains":adaptive["domain_scores"],
      "domains_improved":improved,"criterion_4_of_6":out["criterion_4_of_6"],
      "result_sha256":out["result_sha256"]
    },ensure_ascii=False))


if __name__=="__main__":
    main()
