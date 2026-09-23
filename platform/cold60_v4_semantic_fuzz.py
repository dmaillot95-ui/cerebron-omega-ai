from __future__ import annotations

import hashlib, json, math, os, pathlib, random, re, time
from coalition_tools import execute as adaptive_execute
from generative_backend import MODEL_ID, REVISION, generate

DOMAINS=("math","code","engineering","research_grounded","planning","error_detection")

def canon(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def clean(v):
    x=str(v).strip().lower().rstrip(".").strip()
    if len(x)>=2 and x[0]==x[-1] and x[0] in "'\"": x=x[1:-1]
    return x

def evaluate(output,ev):
    x=clean(output)
    if ev["type"]=="text": return x==str(ev["expected"]).lower(),x
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?",x) is None: return False,x
    return abs(float(x)-float(ev["expected"]))<=max(float(ev.get("tol",0)),1e-8),x

def add(out,i,d,p,t,e,tol=0):
    out.append({"id":i,"domain":d,"prompt":p,"evaluator":{"type":t,"expected":e,"tol":tol}})

def build(seed):
    r=random.Random(seed); out=[]

    # math
    a,b=r.randint(11,40),r.randint(11,40); add(out,"M01","math",f"Calculate: {a}×{b}","numeric",a*b)
    a,b,c=r.randint(40,160),r.randint(2,12),r.randint(2,20); add(out,"M02","math",f"Evaluate: {a}/{b}+{c}","numeric",a/b+c,1e-8)
    k,x,b=r.randint(2,9),r.randint(2,16),r.randint(1,12); rhs=k*x-b; add(out,"M03","math",f"Find x: {k}x-{b}={rhs}. Number only.","numeric",x)
    g=r.randint(2,15); p,q=g*r.randint(3,10),g*r.randint(11,18); add(out,"M04","math",f"GCD of {p}, {q}. Digits only.","numeric",math.gcd(p,q))
    pct=r.choice([5,10,12.5,20,25,40]); n=r.choice([80,120,160,200,240,320]); add(out,"M05","math",f"What is {pct} percent of {n}? Number only.","numeric",pct*n/100,1e-8)
    num,den=r.randint(1,8),r.choice([2,4,5,8,10,20]); add(out,"M06","math",f"Decimal form for {num}/{den}? Number only.","numeric",num/den,1e-8)
    u,v=r.randint(20,70),r.randint(20,70)
    while u+v>=160: v=r.randint(20,70)
    add(out,"M07","math",f"In a triangle, two angles are {u}° and {v}°. Third angle? Number only.","numeric",180-u-v)
    vals=[r.randint(2,40) for _ in range(6)]; add(out,"M08","math","Average of: "+", ".join(map(str,vals))+". Number only.","numeric",sum(vals)/len(vals),1e-8)
    st,d=r.randint(1,8),r.randint(2,9); seq=[st+i*d for i in range(5)]; add(out,"M09","math","Sequence "+", ".join(map(str,seq))+". Next term? Number only.","numeric",seq[-1]+d)
    base,exp=r.randint(2,5),r.randint(3,7); add(out,"M10","math",f"{base} to the {exp} power. Number only.","numeric",base**exp)

    # code
    exprs=[]
    n=r.randint(6,14); exprs.append((f"sum(range(1,{n}))",sum(range(1,n))))
    arr=[r.randint(0,9) for _ in range(5)]; exprs.append((f"len({arr})",len(arr)))
    word=r.choice(["aelys","elyra","saphea","hyperion"]); exprs.append((repr(word)+"[::-1]",word[::-1]))
    arr=[r.randint(1,30) for _ in range(6)]; exprs.append((f"max({arr})",max(arr)))
    arr=[r.randint(1,15) for _ in range(5)]; exprs.append((f"sorted({arr})[2]",sorted(arr)[2]))
    a,b=r.randint(3,12),r.randint(3,12); exprs.append((f"{a}**2+{b}**2",a*a+b*b))
    arr=[r.randint(1,8) for _ in range(4)]; exprs.append((f"sum({arr})",sum(arr)))
    arr=[r.randint(1,20) for _ in range(6)]; exprs.append((f"min({arr})",min(arr)))
    a,b=r.randint(10,50),r.randint(2,9); exprs.append((f"{a}//{b}",a//b))
    a,b=r.randint(10,50),r.randint(2,9); exprs.append((f"{a}%{b}",a%b))
    markers=["Python evaluate for","Restricted evaluator","Safe Python expression"]
    for i,(expr,ans) in enumerate(exprs):
        marker=markers[i%len(markers)]
        add(out,f"C{i+1:02d}","code",f"{marker}: {expr}. Return only its value.","text" if isinstance(ans,str) else "numeric",ans)

    # engineering
    m,a=r.randint(10,90),r.uniform(.5,4); add(out,"G01","engineering",f"A mass of {m} kg accelerates at {a:.3f} m/s^2. Force in N? Number only.","numeric",m*a,1e-3)
    f,v=r.randint(20,150),r.uniform(.5,4); add(out,"G02","engineering",f"A force of {f} N acts while moving at {v:.3f} m/s. Power in W? Number only.","numeric",f*v,1e-3)
    power,t=r.randint(50,500),r.randint(5,60); add(out,"G03","engineering",f"A device draws {power} W for {t} seconds. Energy in J? Number only.","numeric",power*t)
    mass,vol=r.randint(10,100),r.uniform(.5,5); add(out,"G04","engineering",f"Mass is {mass} kg; volume is {vol:.3f} m^3. Density kg/m^3? Number only.","numeric",mass/vol,1e-3)
    d,t=r.randint(20,300),r.randint(5,60); add(out,"G05","engineering",f"Travel {d} m in {t} s. Speed m/s? Number only.","numeric",d/t,1e-3)
    cur,res=r.uniform(.5,8),r.uniform(1,20); add(out,"G06","engineering",f"Current is {cur:.3f} A through {res:.3f} ohm. Voltage? Number only.","numeric",cur*res,1e-3)
    mass,v=r.randint(5,50),r.uniform(.5,5); add(out,"G07","engineering",f"A mass of {mass} kg moves at {v:.3f} m/s. Kinetic energy J? Number only.","numeric",.5*mass*v*v,1e-3)
    mass,h=r.randint(2,30),r.uniform(1,10); add(out,"G08","engineering",f"A mass of {mass} kg is lifted {h:.3f} m under gravity 9.81. Potential energy J? Number only.","numeric",mass*9.81*h,1e-3)
    period=r.choice([.1,.2,.25,.5,2]); add(out,"G09","engineering",f"An event repeats every {period} seconds. Frequency Hz? Number only.","numeric",1/period,1e-8)
    pin=r.randint(100,500); pout=r.randint(50,pin); add(out,"G10","engineering",f"Input power is {pin} W; useful output power is {pout} W. Efficiency percent? Number only.","numeric",100*pout/pin,1e-3)

    # research
    keys=["alpha","beta","gamma","delta"]
    for i in range(10):
        vals={k:round(r.uniform(.1,9.9),3) for k in keys}; target=r.choice(keys)
        facts="; ".join(f"{k}={v}" for k,v in vals.items())
        add(out,f"R{i+1:02d}","research_grounded",f"Facts: {facts}. Query: {target}. Use only the facts; return its value.","numeric",vals[target],1e-9)

    # planning
    for i in range(10):
        seq=["J","K","L","M"]; r.shuffle(seq); correct=seq[:]
        wrong1=correct[:]; wrong1[0],wrong1[1]=wrong1[1],wrong1[0]
        wrong2=correct[:]; wrong2[1],wrong2[2]=wrong2[2],wrong2[1]
        opts=[correct,wrong1,wrong2]; r.shuffle(opts)
        labels=["1","2","3"]; answer=labels[opts.index(correct)]
        rendered=" / ".join(f"{lab}) {' > '.join(s)}" for lab,s in zip(labels,opts))
        rules=f"{correct[0]} must be first; {correct[1]} must come before {correct[2]}; {correct[3]} must be last"
        add(out,f"P{i+1:02d}","planning",f"Rules: {rules}. Choices: {rendered}. Reply only 1, 2, or 3.","text",answer)

    # error detection
    for i in range(10):
        labels=["1","2","3"]; bad=r.randrange(3); claims=[]
        for j,label in enumerate(labels):
            x,y=r.randint(2,20),r.randint(2,12); op=r.choice(["+","-","*"])
            truth=x+y if op=="+" else x-y if op=="-" else x*y
            shown=truth+(r.choice([-3,-2,-1,1,2,3]) if j==bad else 0)
            claims.append(f"{label}) {x}{op}{y}={shown}")
        add(out,f"E{i+1:02d}","error_detection","One equation is incorrect. "+"; ".join(claims)+". Reply only 1, 2, or 3.","text",labels[bad])

    assert len(out)==60 and all(sum(t["domain"]==d for t in out)==10 for d in DOMAINS)
    return out

def run(ts,mode):
    scores={d:{"passed":0,"total":0} for d in DOMAINS}; rows=[]; hits=0
    for t in ts:
        if mode=="SINGLE_MODEL":
            r=generate(t["prompt"],max_new_tokens=32); ans=r["generation"]; emode="MODEL"
        else:
            r=adaptive_execute(t["prompt"]); ans=r.get("answer") or ""; emode=r.get("execution_mode"); hits+=int(emode=="DETERMINISTIC_SPECIALIST_TOOL")
        ok,norm=evaluate(ans,t["evaluator"]); scores[t["domain"]]["total"]+=1; scores[t["domain"]]["passed"]+=int(ok)
        rows.append({"id":t["id"],"domain":t["domain"],"pass":ok,"expected":t["evaluator"]["expected"],"output":ans,"normalized":norm,"execution_mode":emode})
    score=sum(int(x["pass"]) for x in rows)
    return {"mode":mode,"score":score,"max_score":60,"accuracy":score/60,"domain_scores":scores,"tool_hits":hits,"results":rows}

def main():
    seed=int(os.getenv("CEREBRON_V4_SEED","20260923")); started=time.perf_counter(); ts=build(seed)
    dataset={"schema":"CEREBRON_COLD60_V4_SEMANTIC_FUZZ","memory_class":"M6_COLD_BENCHMARK","deny_training":True,"seed":seed,"tasks":ts}
    base=run(ts,"SINGLE_MODEL"); adaptive=run(ts,"ADAPTIVE")
    improved=[d for d in DOMAINS if adaptive["domain_scores"][d]["passed"]>base["domain_scores"][d]["passed"]]
    out={"schema":"CEREBRON_COLD60_V4_SEMANTIC_FUZZ_RESULT","dataset_sha":canon(dataset),"seed":seed,"model_id":MODEL_ID,"revision":REVISION,
         "baseline":base,"adaptive":adaptive,"domains_improved":improved,"domains_improved_count":len(improved),"criterion_4_of_6":len(improved)>=4,
         "limitations":["fresh internal runtime-seeded semantic fuzz; not external independent evaluation","templates authored internally","deny_training=true","same Qwen base may serve fallback roles"],
         "elapsed_s":round(time.perf_counter()-started,3)}
    out["result_sha256"]=canon(out)
    root=pathlib.Path("platform/artifacts"); root.mkdir(parents=True,exist_ok=True)
    (root/"cold60-v4-dataset.json").write_text(json.dumps(dataset,ensure_ascii=False,indent=2)+"\n")
    (root/"cold60-v4-result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"schema":out["schema"],"seed":seed,"baseline_score":base["score"],"adaptive_score":adaptive["score"],"tool_hits":adaptive["tool_hits"],"domains_improved":improved,"criterion_4_of_6":out["criterion_4_of_6"],"result_sha256":out["result_sha256"]},ensure_ascii=False))

if __name__=="__main__": main()
