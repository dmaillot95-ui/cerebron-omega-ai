
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time

from generative_backend import MODEL_ID, REVISION, generate

TASKS = []

def add(task_id, domain, prompt, kind, expected, tolerance=0.0):
    TASKS.append({
        "id": task_id,
        "domain": domain,
        "prompt": prompt,
        "evaluator": {"type": kind, "expected": expected, "tolerance": tolerance},
    })

add("M01","math","Return only the number. Compute 17*23.","numeric",391)
add("M02","math","Return only the number. Compute (144/12)+7.","numeric",19)
add("M03","math","Return only x as a number. Solve 3x+5=29.","numeric",8)
add("M04","math","Return only the number. What is gcd(84,126)?","numeric",42)
add("M05","math","Return only the next number: 2, 6, 12, 20, 30, ?","numeric",42)
add("M06","math","Return only the number. What is 15 percent of 240?","numeric",36)
add("M07","math","Return only the decimal number. Convert 7/8 to decimal.","numeric",0.875,1e-9)
add("M08","math","Return only the number of degrees. A triangle has angles 35 and 65 degrees. What is the third angle?","numeric",80)
add("M09","math","Return only the number. Compute 2^10.","numeric",1024)
add("M10","math","Return only the number. What is the arithmetic mean of 4,8,15,16,23,42?","numeric",18)

add("C01","code","Return only the Python result as a number: sum(i*i for i in range(4))","numeric",14)
add("C02","code","Return only the number: len([x for x in range(6) if x%2==0])","numeric",3)
add("C03","code","Return only the exact string result of Python: 'cerebron'[::-1]","text","norberec")
add("C04","code","Return only the Python result as a number: {'a':1}.get('b',5)","numeric",5)
add("C05","code","Return only the number: len(set([1,1,2,3,3]))","numeric",3)
add("C06","code","Return only the number: sorted([3,1,2])[1]","numeric",2)
add("C07","code","Return only TRUE or FALSE for Python: bool([]) or bool([0])","text","true")
add("C08","code","Return only the number: 10//3 + 10%3","numeric",4)
add("C09","code","Return only a,b,c with no quotes or spaces: ','.join(['a','b','c'])","text","a,b,c")
add("C10","code","Return only 2,5,8 with no brackets or spaces: list(range(2,9,3))","text","2,5,8")

add("P01","engineering","Return only the number in newtons. F=ma with m=12 kg and a=3.5 m/s^2.","numeric",42,1e-9)
add("P02","engineering","Return only the number in watts. Mechanical power P=Fv with F=80 N and v=2.5 m/s.","numeric",200,1e-9)
add("P03","engineering","Return only the number in joules. Energy E=Pt for P=500 W during 120 s.","numeric",60000,1e-9)
add("P04","engineering","Return only the number in kg/m^3. Density for mass 7.8 kg and volume 0.001 m^3.","numeric",7800,1e-6)
add("P05","engineering","Return only the number in m/s. Speed for 150 m traveled in 12 s.","numeric",12.5,1e-9)
add("P06","engineering","Return only the number in volts. V=IR with I=2.4 A and R=5 ohm.","numeric",12,1e-9)
add("P07","engineering","Return only the number in joules. Kinetic energy 0.5*m*v^2 for m=10 kg and v=4 m/s.","numeric",80,1e-9)
add("P08","engineering","Return only the number in joules. Potential energy mgh with m=5 kg, g=9.81 m/s^2, h=2 m.","numeric",98.1,1e-6)
add("P09","engineering","Return only the number in hertz. Frequency is 1/T for T=0.02 s.","numeric",50,1e-9)
add("P10","engineering","Return only the efficiency percent as a number. Output=800 W, input=1000 W.","numeric",80,1e-9)

add("R01","research_grounded","SOURCE: Engine A uses methane. Engine B uses hydrogen. Using only the source, return only Engine A's fuel.","text","methane")
add("R02","research_grounded","SOURCE: The launch window opens at 14:30 UTC and closes at 14:50 UTC. Using only the source, return only the opening time in HH:MM.","text","14:30")
add("R03","research_grounded","SOURCE: Sample K has mass 18.4 kg and volume 2.0 L. Using only the source, return only Sample K's mass as a number.","numeric",18.4,1e-9)
add("R04","research_grounded","SOURCE: The rover is rated at 48 V and maximum current 30 A. Using only the source, return only the rated voltage as a number.","numeric",48)
add("R05","research_grounded","SOURCE: V6 used 128 grains. V5 used 100 grains. Using only the source, return only the V6 grain count.","numeric",128)
add("R06","research_grounded","SOURCE: RED means rejected. GREEN means accepted. The sample status is GREEN. Using only the source, return only the outcome.","text","accepted")
add("R07","research_grounded","SOURCE: Source A is revision 3. Source B is revision 7. Using only the source, return only the higher revision number.","numeric",7)
add("R08","research_grounded","SOURCE: Artifact 42 digest is abc123. Artifact 43 digest is def456. Using only the source, return only Artifact 43's digest.","text","def456")
add("R09","research_grounded","SOURCE: Task X is owned by METRION. Task Y is owned by ASTRION. Using only the source, return only Task Y's owner.","text","astrion")
add("R10","research_grounded","SOURCE: alpha=0.25, beta=0.75, gamma=1.50. Using only the source, return only beta as a decimal number.","numeric",0.75,1e-9)

add("L01","planning","Return only A, B, or C. Constraints: A-task before B-task; C-task last. Options: A=B-task,A-task,C-task; B=A-task,B-task,C-task; C=A-task,C-task,B-task.","text","b")
add("L02","planning","Return only A, B, or C. Constraints: X first; Y before Z. Options: A=Y,X,Z; B=X,Z,Y; C=X,Y,Z.","text","c")
add("L03","planning","Return only A, B, or C. Constraints: P before Q; R after Q. Options: A=P,Q,R; B=Q,P,R; C=P,R,Q.","text","a")
add("L04","planning","Return only A, B, or C. Constraints: D last; A before C. Options: A=A,D,C; B=C,A,D; C=A,C,D.","text","c")
add("L05","planning","Return only A, B, or C. Constraints: K not first; L before K; M last. Options: A=L,M,K; B=L,K,M; C=K,L,M.","text","b")
add("L06","planning","Return only A, B, or C. Constraints: U first; W immediately after V. Options: A=U,V,W; B=V,W,U; C=U,W,V.","text","a")
add("L07","planning","Return only A, B, or C. Constraints: T before S; R first. Options: A=T,R,S; B=R,S,T; C=R,T,S.","text","c")
add("L08","planning","Return only A, B, or C. Constraints: J last; H before I. Options: A=H,J,I; B=H,I,J; C=I,H,J.","text","b")
add("L09","planning","Return only A, B, or C. Constraints: B-task first; A-task after C-task. Options: A=B-task,C-task,A-task; B=B-task,A-task,C-task; C=C-task,B-task,A-task.","text","a")
add("L10","planning","Return only A, B, or C. Constraints: E before F; G first. Options: A=G,F,E; B=E,G,F; C=G,E,F.","text","c")

add("E01","error_detection","Return only the letter of the false claim. A: 2+2=4. B: 3*3=9. C: 10/2=6.","text","c")
add("E02","error_detection","Return only the letter of the false claim. A: Earth has one natural moon. B: Water freezes at 0 C at about 1 atm. C: 1 km=100 m.","text","c")
add("E03","error_detection","Return only the letter of the false Python claim. A: len('abc')=3. B: 5//2=2. C: bool([])=True.","text","c")
add("E04","error_detection","Return only the letter of the false mechanics formula. A: F=ma. B: P=Fv for aligned constant force and velocity. C: kinetic energy=m*v^2.","text","c")
add("E05","error_detection","Return only the letter of the false claim. A: 7 is prime. B: 9 is prime. C: 11 is prime.","text","b")
add("E06","error_detection","Return only the letter of the false claim. A: 1 byte=8 bits. B: hexadecimal F equals decimal 15. C: binary 10 equals decimal 3.","text","c")
add("E07","error_detection","Return only the letter of the false claim. A: pi is approximately 3.14. B: sqrt(81)=8. C: 2^5=32.","text","b")
add("E08","error_detection","Return only the letter of the false claim. A: JSON objects use key-value pairs. B: HTTP 404 commonly means Not Found. C: SHA-256 outputs a 128-bit digest.","text","c")
add("E09","error_detection","Return only the letter of the false claim. A: Venus is a planet. B: The Sun is a planet. C: Mars is a planet.","text","b")
add("E10","error_detection","Return only the letter of the false claim. A: 60 seconds=1 minute. B: 1000 m=1 km. C: 1 hour=100 minutes.","text","c")

DOMAINS = ["math","code","engineering","research_grounded","planning","error_detection"]
assert len(TASKS) == 60
assert len({t["id"] for t in TASKS}) == 60
assert all(sum(t["domain"] == d for t in TASKS) == 10 for d in DOMAINS)

def canonical_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

DATASET = {
    "schema": "CEREBRON_COLD_60_V1",
    "memory_class": "M6_COLD_BENCHMARK",
    "deny_training": True,
    "frozen_after_first_run": True,
    "domains": DOMAINS,
    "tasks": TASKS,
}
DATASET_SHA = canonical_sha(DATASET)

def clean_text(value):
    clean = value.strip().lower()
    if clean.endswith("."):
        clean = clean[:-1].strip()
    if len(clean) >= 2 and clean[0] == clean[-1] and clean[0] in ('"', "'"):
        clean = clean[1:-1]
    return clean

def evaluate(output, evaluator):
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

def main():
    started = time.perf_counter()
    domain_scores = {d: {"passed": 0, "total": 0} for d in DOMAINS}
    results = []
    for task in TASKS:
        response = generate(task["prompt"], max_new_tokens=32)
        passed, normalized = evaluate(response["generation"], task["evaluator"])
        domain_scores[task["domain"]]["total"] += 1
        domain_scores[task["domain"]]["passed"] += int(passed)
        results.append({
            "id": task["id"],
            "domain": task["domain"],
            "pass": passed,
            "expected": task["evaluator"]["expected"],
            "output": response["generation"],
            "normalized": normalized,
            "output_sha": response["output_sha"],
        })
    score = sum(int(x["pass"]) for x in results)
    out = {
        "schema": "CEREBRON_COLD_60_RESULT_V1",
        "mode": "SINGLE_MODEL_NO_TOOLS",
        "dataset_schema": DATASET["schema"],
        "dataset_sha": DATASET_SHA,
        "memory_class": "M6_COLD_BENCHMARK",
        "deny_training": True,
        "model_id": MODEL_ID,
        "revision": REVISION,
        "score": score,
        "max_score": 60,
        "accuracy": score / 60,
        "domain_scores": domain_scores,
        "results": results,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "limitations": [
            "small deterministic benchmark, not a general intelligence metric",
            "research tasks use provided sources rather than live web access",
            "planning tasks are constrained-choice problems",
            "no external tools are available in this baseline",
        ],
    }
    out["result_sha256"] = canonical_sha(out)
    target = pathlib.Path("platform/artifacts/cold60-single-model-v1.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": out["schema"],
        "mode": out["mode"],
        "dataset_sha": out["dataset_sha"],
        "score": out["score"],
        "max_score": out["max_score"],
        "accuracy": out["accuracy"],
        "domain_scores": out["domain_scores"],
        "elapsed_s": out["elapsed_s"],
        "result_sha256": out["result_sha256"],
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
