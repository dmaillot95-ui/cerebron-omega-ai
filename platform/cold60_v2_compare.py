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


DOMAINS = ("math", "code", "engineering", "research_grounded", "planning", "error_detection")


def canonical_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def clean_text(value: str) -> str:
    clean = str(value).strip().lower()
    if clean.endswith("."):
        clean = clean[:-1].strip()
    if len(clean) >= 2 and clean[0] == clean[-1] and clean[0] in ('"', "'"):
        clean = clean[1:-1]
    return clean


def evaluate(output: str, evaluator: dict) -> tuple[bool, str]:
    clean = clean_text(output)
    if evaluator["type"] == "text":
        return clean == str(evaluator["expected"]).lower(), clean
    if evaluator["type"] == "numeric":
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", clean) is None:
            return False, clean
        value = float(clean)
        tolerance = max(float(evaluator.get("tolerance", 0.0)), 1e-9)
        return abs(value - float(evaluator["expected"])) <= tolerance, clean
    raise ValueError("UNKNOWN_EVALUATOR")


def add(tasks, task_id, domain, prompt, kind, expected, tolerance=0.0):
    tasks.append({
        "id": task_id,
        "domain": domain,
        "prompt": prompt,
        "evaluator": {"type": kind, "expected": expected, "tolerance": tolerance},
    })


def generate_tasks(seed: int) -> list[dict]:
    rng = random.Random(seed)
    tasks = []

    # MATH — generated numeric variants, not the visible V1 instances.
    a, b = rng.randint(11, 39), rng.randint(11, 39)
    add(tasks, "M01", "math", f"Return only the number. Compute: {a}*{b}", "numeric", a*b)
    a, b, c = rng.randint(40, 160), rng.randint(2, 12), rng.randint(3, 20)
    add(tasks, "M02", "math", f"Return only the number. Compute: ({a}/{b})+{c}", "numeric", a/b+c, 1e-9)
    coef, x, offset = rng.randint(2, 9), rng.randint(2, 15), rng.randint(1, 12)
    rhs = coef*x + offset
    add(tasks, "M03", "math", f"Return only x as a number. Solve for x: {coef}*x+{offset}={rhs}", "numeric", x)
    g = rng.randint(2, 15); p, q = g*rng.randint(3, 10), g*rng.randint(11, 18)
    add(tasks, "M04", "math", f"Return only the number. What is gcd({p},{q})?", "numeric", math.gcd(p,q))
    pct, n = rng.choice([5,10,12.5,20,25,40]), rng.choice([80,120,160,200,240,320])
    add(tasks, "M05", "math", f"Return only the number. What is {pct} percent of {n}?", "numeric", pct*n/100, 1e-9)
    num, den = rng.randint(1, 8), rng.choice([2,4,5,8,10,20])
    add(tasks, "M06", "math", f"Return only the decimal number. Convert {num}/{den} to decimal.", "numeric", num/den, 1e-9)
    ang1, ang2 = rng.randint(20, 70), rng.randint(20, 70)
    while ang1 + ang2 >= 160:
        ang2 = rng.randint(20, 70)
    add(tasks, "M07", "math", f"Return only the number of degrees. A triangle has angles {ang1} and {ang2} degrees. What is the third angle?", "numeric", 180-ang1-ang2)
    vals = [rng.randint(2, 40) for _ in range(6)]
    add(tasks, "M08", "math", "Return only the number. What is the arithmetic mean of " + ",".join(map(str,vals)) + "?", "numeric", sum(vals)/len(vals), 1e-9)
    start = rng.randint(1, 8); d = rng.randint(2, 9)
    seq = [start + i*d for i in range(5)]
    add(tasks, "M09", "math", "Return only the next number: " + ", ".join(map(str,seq)) + ", ?", "numeric", seq[-1]+d)
    base, exp = rng.randint(2, 5), rng.randint(3, 7)
    add(tasks, "M10", "math", f"Return only the number. Compute: {base}^{exp}", "numeric", base**exp)

    # CODE — restricted pure expressions suitable for a sandboxed interpreter.
    n = rng.randint(5, 12)
    add(tasks, "C01", "code", f"Return only the Python result: sum(range(1,{n}))", "numeric", sum(range(1,n)))
    arr = [rng.randint(0,9) for _ in range(5)]
    add(tasks, "C02", "code", f"Return only the Python result: len({arr})", "numeric", len(arr))
    word = rng.choice(["cerebron","spiralion","etherion","saphea"])
    add(tasks, "C03", "code", f"Return only the Python result: '{word}'[::-1]", "text", word[::-1])
    arr = [rng.randint(1,30) for _ in range(6)]
    add(tasks, "C04", "code", f"Return only the Python result: max({arr})", "numeric", max(arr))
    arr = [rng.randint(1,30) for _ in range(5)]
    add(tasks, "C05", "code", f"Return only the Python result: sorted({arr})[2]", "numeric", sorted(arr)[2])
    arr = [1,1,2,3,3,rng.randint(4,8)]
    add(tasks, "C06", "code", f"Return only the Python result: len(set({arr}))", "numeric", len(set(arr)))
    x, y = rng.randint(10,30), rng.randint(2,9)
    add(tasks, "C07", "code", f"Return only the Python result: {x}//{y}+{x}%{y}", "numeric", x//y+x%y)
    chars = rng.sample(list("abcdef"), 3)
    add(tasks, "C08", "code", "Return only the Python result: ','.join(" + repr(chars) + ")", "text", ",".join(chars))
    start, stop, step = 2, rng.randint(10,18), rng.choice([2,3,4])
    expected = list(range(start, stop, step))
    add(tasks, "C09", "code", f"Return only the Python result: list(range({start},{stop},{step}))", "text", ",".join(map(str,expected)))
    x, y = rng.randint(-20,-2), rng.randint(1,12)
    add(tasks, "C10", "code", f"Return only the Python result: abs({x})+{y}", "numeric", abs(x)+y)

    # ENGINEERING — formula-tagged computations, random parameters.
    m, acc = rng.randint(5,30), rng.choice([1.5,2.5,3.5,4.0])
    add(tasks,"P01","engineering",f"Using F=ma; m={m}; a={acc}. Return only F.","numeric",m*acc,1e-9)
    force, vel = rng.randint(20,120), rng.choice([0.5,1.5,2.0,2.5])
    add(tasks,"P02","engineering",f"Using P=Fv; F={force}; v={vel}. Return only P.","numeric",force*vel,1e-9)
    power, seconds = rng.randint(100,800), rng.randint(10,180)
    add(tasks,"P03","engineering",f"Using E=Pt; P={power}; t={seconds}. Return only E.","numeric",power*seconds,1e-9)
    mass, volume = rng.choice([2.7,7.8,10.5]), rng.choice([0.001,0.002,0.005])
    add(tasks,"P04","engineering",f"Using rho=m/V; m={mass}; V={volume}. Return only rho.","numeric",mass/volume,1e-6)
    distance, seconds = rng.randint(50,300), rng.randint(5,30)
    add(tasks,"P05","engineering",f"Using v=d/t; d={distance}; t={seconds}. Return only v.","numeric",distance/seconds,1e-9)
    current, resistance = rng.choice([1.2,2.4,3.5]), rng.choice([2,4,5,8])
    add(tasks,"P06","engineering",f"Using V=IR; I={current}; R={resistance}. Return only V.","numeric",current*resistance,1e-9)
    mass, vel = rng.randint(2,20), rng.randint(2,8)
    add(tasks,"P07","engineering",f"Using KE=0.5*m*v^2; m={mass}; v={vel}. Return only KE.","numeric",0.5*mass*vel**2,1e-9)
    mass, g, h = rng.randint(2,12), 9.81, rng.randint(1,8)
    add(tasks,"P08","engineering",f"Using PE=mgh; m={mass}; g={g}; h={h}. Return only PE.","numeric",mass*g*h,1e-6)
    period = rng.choice([0.01,0.02,0.04,0.05,0.1])
    add(tasks,"P09","engineering",f"Using f=1/T; T={period}. Return only f.","numeric",1/period,1e-9)
    pin = rng.choice([500,800,1000,1200]); eta = rng.choice([60,70,75,80,90]); pout = pin*eta/100
    add(tasks,"P10","engineering",f"Using eta=100*Pout/Pin; Pout={pout}; Pin={pin}. Return only eta.","numeric",eta,1e-9)

    # RESEARCH GROUNDED — generated key/value source extraction.
    for i in range(10):
        keys = ["alpha","beta","gamma"]
        values = [str(rng.randint(10,999)) if i%2==0 else f"{rng.random()*10:.3f}" for _ in keys]
        target = rng.choice(keys)
        source = "; ".join(f"{k}={v}" for k,v in zip(keys,values))
        add(tasks,f"R{i+1:02d}","research_grounded",
            f"SOURCE: {source}. Using only the source, return only {target}.",
            "text", values[keys.index(target)])

    # PLANNING — generated permutations and constraints with a unique valid option.
    import itertools
    names = ["K","L","M"]
    perms = list(itertools.permutations(names))
    for i in range(10):
        correct = list(rng.choice(perms))
        first, second, last = correct
        constraints = [f"{first} first", f"{second} before {last}"]
        wrong = [list(p) for p in perms if list(p) != correct]
        rng.shuffle(wrong)
        options = [correct, wrong[0], wrong[1]]
        rng.shuffle(options)
        labels = ["A","B","C"]
        correct_label = labels[options.index(correct)].lower()
        option_text = "; ".join(f"{lab}=" + ",".join(seq) for lab,seq in zip(labels,options))
        add(tasks,f"L{i+1:02d}","planning",
            f"Return only A, B, or C. Constraints: {'; '.join(constraints)}. Options: {option_text}.",
            "text", correct_label)

    # ERROR DETECTION — generated arithmetic claims, exactly one false.
    labels = ["A","B","C"]
    for i in range(10):
        claims=[]; false_idx=rng.randrange(3)
        for j,label in enumerate(labels):
            x,y=rng.randint(2,20),rng.randint(2,12)
            op=rng.choice(["+","-","*"])
            truth = x+y if op=="+" else x-y if op=="-" else x*y
            shown = truth + (rng.choice([-3,-2,-1,1,2,3]) if j==false_idx else 0)
            claims.append(f"{label}: {x}{op}{y}={shown}")
        add(tasks,f"E{i+1:02d}","error_detection",
            "Return only the false letter. " + "; ".join(claims) + ";",
            "text", labels[false_idx].lower())

    assert len(tasks) == 60
    assert all(sum(t["domain"]==d for t in tasks)==10 for d in DOMAINS)
    return tasks


def run_mode(tasks: list[dict], mode: str) -> dict:
    scores = {d: {"passed":0,"total":0} for d in DOMAINS}
    rows=[]
    for task in tasks:
        if mode == "SINGLE_MODEL_NO_TOOLS":
            response = generate(task["prompt"], max_new_tokens=32)
            answer = response["generation"]
            meta = {"output_sha": response["output_sha"], "execution_mode": "MODEL"}
        elif mode == "ADAPTIVE_COALITION_TOOLS":
            response = adaptive_execute(task["prompt"])
            answer = response.get("answer") or ""
            meta = {
                "execution_mode": response.get("execution_mode"),
                "selected_units": response.get("plan",{}).get("selected_units",[]),
                "independent_model_count": response.get("plan",{}).get("independent_model_count",0),
                "claim_ceiling": response.get("claim_ceiling"),
            }
        else:
            raise ValueError(mode)
        passed, normalized = evaluate(answer, task["evaluator"])
        scores[task["domain"]]["total"] += 1
        scores[task["domain"]]["passed"] += int(passed)
        rows.append({
            "id":task["id"],"domain":task["domain"],"pass":passed,
            "expected":task["evaluator"]["expected"],"output":answer,"normalized":normalized,**meta,
        })
    total=sum(r["pass"] for r in rows)
    return {"mode":mode,"score":total,"max_score":60,"accuracy":total/60,"domain_scores":scores,"results":rows}


def main():
    seed=int(os.getenv("CEREBRON_COLD_SEED","20260923"))
    started=time.perf_counter()
    tasks=generate_tasks(seed)
    dataset={
        "schema":"CEREBRON_COLD_60_V2_RUNTIME_SEEDED",
        "memory_class":"M6_COLD_BENCHMARK",
        "deny_training":True,
        "seed":seed,
        "domains":list(DOMAINS),
        "tasks":tasks,
    }
    dataset_sha=canonical_sha(dataset)
    base=run_mode(tasks,"SINGLE_MODEL_NO_TOOLS")
    adaptive=run_mode(tasks,"ADAPTIVE_COALITION_TOOLS")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"] > base["domain_scores"][d]["passed"]]
    out={
        "schema":"CEREBRON_COLD_60_V2_COMPARISON",
        "dataset_sha":dataset_sha,
        "seed":seed,
        "model_id":MODEL_ID,
        "revision":REVISION,
        "baseline":base,
        "adaptive":adaptive,
        "domains_improved":improved,
        "domains_improved_count":len(improved),
        "criterion_4_of_6":len(improved)>=4,
        "elapsed_s":round(time.perf_counter()-started,3),
        "limitations":[
            "structured deterministic task family; not a general intelligence metric",
            "runtime seed prevents pre-seeing exact numeric/source instances but task templates are known",
            "deterministic tools are capabilities, not independent neural agents",
            "no physical validation or external-world autonomy is measured",
        ],
    }
    out["result_sha256"]=canonical_sha(out)
    root=pathlib.Path("platform/artifacts");root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-v2-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (root/"cold60-v2-comparison.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":out["schema"],"dataset_sha":dataset_sha,"seed":seed,
        "baseline_score":base["score"],"adaptive_score":adaptive["score"],
        "baseline_domains":base["domain_scores"],"adaptive_domains":adaptive["domain_scores"],
        "domains_improved":improved,"criterion_4_of_6":out["criterion_4_of_6"],
        "elapsed_s":out["elapsed_s"],"result_sha256":out["result_sha256"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
