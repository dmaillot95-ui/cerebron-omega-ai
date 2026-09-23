from __future__ import annotations

import hashlib
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


def canon(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def norm(x):
    s=str(x).strip().lower()
    s=re.sub(r"^[\"']|[\"']$","",s)
    s=s.rstrip(".").strip()
    return s


def evaluate(output,e):
    s=norm(output)
    if e["type"]=="text":
        return s==str(e["expected"]).lower(),s
    if e["type"]=="numeric":
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?",s) is None:
            return False,s
        return abs(float(s)-float(e["expected"]))<=max(float(e.get("tolerance",0)),1e-9),s
    raise ValueError("bad evaluator")


def add(tasks,i,d,p,t,e,tol=0):
    tasks.append({"id":i,"domain":d,"prompt":p,"evaluator":{"type":t,"expected":e,"tolerance":tol}})


def tasks(seed):
    r=random.Random(seed)
    out=[]

    # MATH: semantically similar to V2 but deliberately avoids the V2 parser phrases.
    for i in range(10):
        if i==0:
            a,b=r.randint(12,39),r.randint(12,39); ans=a*b
            p=f"Multiply {a} by {b}. Reply with the numeric answer and nothing else."
        elif i==1:
            a,b,c=r.randint(40,150),r.randint(2,10),r.randint(3,20); ans=a/b+c
            p=f"Find the value of {a} divided by {b}, then add {c}. Give just the number."
        elif i==2:
            k,x,b=r.randint(2,9),r.randint(2,15),r.randint(1,12); rhs=k*x+b; ans=x
            p=f"Which number x satisfies {k}x + {b} = {rhs}? Output x only."
        elif i==3:
            g=r.randint(2,12); a,b=g*r.randint(4,10),g*r.randint(11,18); ans=math.gcd(a,b)
            p=f"Give only the greatest common divisor of {a} and {b}."
        elif i==4:
            pct=r.choice([5,10,12.5,20,25,40]); n=r.choice([80,120,160,200,240,320]); ans=pct*n/100
            p=f"Only the numeric value: {pct}% of {n}."
        elif i==5:
            a,b=r.randint(1,8),r.choice([2,4,5,8,10,20]); ans=a/b
            p=f"Write {a}/{b} as a decimal. Return the decimal only."
        elif i==6:
            a,b=r.randint(20,70),r.randint(20,70)
            while a+b>=160:b=r.randint(20,70)
            ans=180-a-b
            p=f"Two angles of a triangle are {a}° and {b}°. Give only the third angle number."
        elif i==7:
            vals=[r.randint(2,40) for _ in range(6)]; ans=sum(vals)/len(vals)
            p="Give only the arithmetic average of these six values: "+", ".join(map(str,vals))
        elif i==8:
            s,d=r.randint(1,8),r.randint(2,9); vals=[s+j*d for j in range(5)]; ans=vals[-1]+d
            p="Continue this arithmetic pattern and output only the next term: "+", ".join(map(str,vals))
        else:
            a,b=r.randint(2,5),r.randint(3,7); ans=a**b
            p=f"Evaluate {a} raised to the power {b}. Numeric answer only."
        add(out,f"M{i+1:02d}","math",p,"numeric",ans,1e-9)

    # CODE: avoids the literal marker "Python result:" used by the bounded parser.
    expressions=[]
    n=r.randint(6,13); expressions.append((f"sum(range(1,{n}))",sum(range(1,n))))
    arr=[r.randint(0,9) for _ in range(5)]; expressions.append((f"len({arr})",len(arr)))
    word=r.choice(["cerebron","spiralion","etherion","saphea"]); expressions.append((repr(word)+"[::-1]",word[::-1]))
    arr=[r.randint(1,30) for _ in range(6)]; expressions.append((f"max({arr})",max(arr)))
    arr=[r.randint(1,15) for _ in range(5)]; expressions.append((f"sorted({arr})[2]",sorted(arr)[2]))
    a,b=r.randint(3,12),r.randint(3,12); expressions.append((f"{a}**2+{b}**2",a*a+b*b))
    arr=[r.randint(1,8) for _ in range(4)]; expressions.append((f"sum({arr})",sum(arr)))
    arr=[r.randint(1,20) for _ in range(6)]; expressions.append((f"min({arr})",min(arr)))
    a,b=r.randint(10,50),r.randint(2,9); expressions.append((f"{a}//{b}",a//b))
    a,b=r.randint(10,50),r.randint(2,9); expressions.append((f"{a}%{b}",a%b))
    for i,(expr,ans) in enumerate(expressions):
        typ="text" if isinstance(ans,str) else "numeric"
        add(out,f"C{i+1:02d}","code",f"Evaluate this safe Python expression: {expr}. Respond only with its value.",typ,ans)

    # ENGINEERING: no equation tags such as F=ma/P=Fv for parser matching.
    for i in range(10):
        if i==0:
            m,a=r.randint(10,90),r.uniform(.5,4); ans=m*a; p=f"A {m} kg body accelerates at {a:.3f} m/s^2. What force in newtons? Number only."
        elif i==1:
            f,v=r.randint(20,150),r.uniform(.5,4); ans=f*v; p=f"A force of {f} N acts while moving at {v:.3f} m/s. Mechanical power in watts? Number only."
        elif i==2:
            power,t=r.randint(50,500),r.randint(5,60); ans=power*t; p=f"A device draws {power} W for {t} seconds. Energy in joules? Number only."
        elif i==3:
            mass,vol=r.randint(10,100),r.uniform(.5,5); ans=mass/vol; p=f"Mass is {mass} kg and volume is {vol:.3f} m^3. Density kg/m^3? Number only."
        elif i==4:
            d,t=r.randint(20,300),r.randint(5,60); ans=d/t; p=f"Travel {d} m in {t} s. Average speed m/s? Number only."
        elif i==5:
            cur,res=r.uniform(.5,8),r.uniform(1,20); ans=cur*res; p=f"Current is {cur:.3f} A through {res:.3f} ohm. Voltage? Number only."
        elif i==6:
            m,v=r.randint(5,50),r.uniform(.5,5); ans=.5*m*v*v; p=f"A {m} kg mass moves at {v:.3f} m/s. Kinetic energy in joules? Number only."
        elif i==7:
            m,g,h=r.randint(2,30),9.81,r.uniform(1,10); ans=m*g*h; p=f"A {m} kg mass is lifted {h:.3f} m under gravity 9.81 m/s^2. Potential energy J? Number only."
        elif i==8:
            t=r.choice([.1,.2,.25,.5,2]); ans=1/t; p=f"A periodic event repeats every {t} seconds. Frequency in hertz? Number only."
        else:
            pin=r.randint(100,500); pout=r.randint(50,pin); ans=100*pout/pin; p=f"Input power is {pin} W and useful output is {pout} W. Efficiency percent? Number only."
        add(out,f"G{i+1:02d}","engineering",p,"numeric",ans,1e-3)

    # RESEARCH: alternate source syntax, no SOURCE:/Using only the source markers.
    keys=["alpha","beta","gamma","delta"]
    for i in range(10):
        vals={k:round(r.uniform(.1,9.9),3) for k in keys}
        target=r.choice(keys)
        ref=" | ".join(f"{k}: {v}" for k,v in vals.items())
        p=f"Reference data — {ref}. Based solely on that reference, provide the value for {target}; output only the value."
        add(out,f"R{i+1:02d}","research_grounded",p,"numeric",vals[target],1e-9)

    # PLANNING: alternate headings and wording to avoid Constraints:/Options: parser markers.
    for i in range(10):
        items=["J","K","L","M"]
        r.shuffle(items)
        correct=items[:]
        # rule set uniquely identifies one of three presented sequences
        choices=[correct[:],correct[:],correct[:]]
        r.shuffle(choices[1]); r.shuffle(choices[2])
        while choices[1]==correct: r.shuffle(choices[1])
        while choices[2]==correct or choices[2]==choices[1]: r.shuffle(choices[2])
        labels=["X","Y","Z"]; paired=list(zip(labels,choices)); r.shuffle(paired)
        correct_label=next(l for l,s in paired if s==correct)
        rules=f"{correct[0]} must be first; {correct[1]} must come before {correct[2]}; {correct[3]} must be last"
        opts=" / ".join(f"{l}: {' > '.join(s)}" for l,s in paired)
        p=f"Scheduling rules — {rules}. Candidate orders — {opts}. Which candidate obeys all rules? Reply only X, Y, or Z."
        add(out,f"P{i+1:02d}","planning",p,"text",correct_label.lower())

    # ERROR DETECTION: labels X/Y/Z and the word "wrong", not the parser's ABC/false pattern.
    for i in range(10):
        labels=["X","Y","Z"]; bad=r.randrange(3); claims=[]
        for j,l in enumerate(labels):
            a,b=r.randint(2,20),r.randint(2,12); op=r.choice(["+","-","*"])
            truth=a+b if op=="+" else a-b if op=="-" else a*b
            shown=truth+(r.choice([-3,-2,-1,1,2,3]) if j==bad else 0)
            claims.append(f"{l}) {a}{op}{b}={shown}")
        p="Exactly one statement is wrong. "+ "; ".join(claims)+". Reply only with X, Y, or Z."
        add(out,f"E{i+1:02d}","error_detection",p,"text",labels[bad].lower())

    assert len(out)==60
    return out


def run_mode(ts,mode):
    rows=[]; scores={d:{"passed":0,"total":0} for d in DOMAINS}; tool_handled=0
    for t in ts:
        if mode=="SINGLE_MODEL":
            resp=generate(t["prompt"],max_new_tokens=32); ans=resp["generation"]; execmode="MODEL"
        else:
            resp=adaptive_execute(t["prompt"]); ans=resp.get("answer") or ""; execmode=resp.get("execution_mode")
            if execmode=="DETERMINISTIC_SPECIALIST_TOOL": tool_handled+=1
        passed,normalized=evaluate(ans,t["evaluator"])
        scores[t["domain"]]["total"]+=1; scores[t["domain"]]["passed"]+=int(passed)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":passed,"expected":t["evaluator"]["expected"],"output":ans,"normalized":normalized,"execution_mode":execmode})
    return {"mode":mode,"score":sum(x["pass"] for x in rows),"max_score":60,"domain_scores":scores,"tool_handled_count":tool_handled,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_TRANSFER_SEED","20260923"))
    started=time.perf_counter()
    ts=tasks(seed)
    dataset={"schema":"CEREBRON_COLD60_V3_TRANSFER","memory_class":"M6_COLD_BENCHMARK","deny_training":True,"seed":seed,"tasks":ts}
    base=run_mode(ts,"SINGLE_MODEL")
    adaptive=run_mode(ts,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    out={
        "schema":"CEREBRON_COLD60_V3_TRANSFER_RESULT",
        "dataset_sha":canon(dataset),
        "model_id":MODEL_ID,
        "revision":REVISION,
        "baseline":base,
        "adaptive":adaptive,
        "domains_improved":improved,
        "domains_improved_count":len(improved),
        "criterion_4_of_6":len(improved)>=4,
        "v2_reference_adaptive_accuracy":1.0,
        "v3_adaptive_accuracy":adaptive["score"]/60,
        "transfer_gap_from_v2":1.0-adaptive["score"]/60,
        "red_team_question":"Does V2 60/60 survive semantically similar but parser-unseen prompt forms?",
        "limitations":[
            "still synthetic structured tasks",
            "transfer set is deliberately adversarial to V2 parser markers",
            "same Qwen base model underlies model fallback roles",
            "not a general intelligence benchmark",
        ],
        "elapsed_s":round(time.perf_counter()-started,3),
    }
    out["result_sha256"]=canon(out)
    root=pathlib.Path("platform/artifacts"); root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-v3-transfer-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-v3-transfer-result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "schema":out["schema"],
        "seed":seed,
        "baseline_score":base["score"],
        "adaptive_score":adaptive["score"],
        "tool_handled_count":adaptive["tool_handled_count"],
        "domains_improved":improved,
        "criterion_4_of_6":out["criterion_4_of_6"],
        "transfer_gap_from_v2":out["transfer_gap_from_v2"],
        "result_sha256":out["result_sha256"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
