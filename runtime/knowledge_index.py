import argparse, hashlib, json, math, pathlib, re, sys
ROOT=pathlib.Path("memory_index"); ROOT.mkdir(exist_ok=True)
DB=ROOT/"encyclopedic_index.jsonl"; OUT=pathlib.Path("artifacts/knowledge_record.json")

def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def tokens(s): return re.findall(r"[a-z0-9_]+",s.lower())
def vector(text,d=64):
    v=[0.0]*d
    for t in tokens(text):
        h=int(hashlib.sha256(t.encode()).hexdigest(),16); i=h%d; v[i]+=1 if (h>>8)&1 else -1
    n=math.sqrt(sum(x*x for x in v)) or 1.0
    return [round(x/n,6) for x in v]
def glyph(domain,concept,sha): return f"Ω⟦{domain.upper()}:{concept.upper()}:{sha[:8]}⟧"
def existing():
    if not DB.exists(): return []
    return [json.loads(x) for x in DB.read_text().splitlines() if x.strip()]

ap=argparse.ArgumentParser()
ap.add_argument("--domain",required=True); ap.add_argument("--book",required=True); ap.add_argument("--chapter",required=True)
ap.add_argument("--concept",required=True); ap.add_argument("--stable-id",required=True)
ap.add_argument("--summary",required=True); ap.add_argument("--source",required=True)
ap.add_argument("--epistemic",choices=["OPEN","SIMULATED","TESTED","VALIDATED","REFUTED"],default="OPEN")
ap.add_argument("--dependencies",default=""); ap.add_argument("--contradictions",default="")
a=ap.parse_args()
base={"stable_id":a.stable_id,"domain":a.domain,"book":a.book,"chapter":a.chapter,"concept":a.concept,"summary":a.summary,"source":a.source,"epistemic":a.epistemic,"dependencies":[x for x in a.dependencies.split(",") if x],"contradictions":[x for x in a.contradictions.split(",") if x]}
sha=hashlib.sha256(canon(base)).hexdigest(); rows=existing()
exact=next((r for r in rows if r["sha256"]==sha),None); sid=next((r for r in rows if r["stable_id"]==a.stable_id and r["sha256"]!=sha),None)
if exact:
    out={"status":"DEDUP_EXACT","record":exact}
elif sid:
    out={"status":"CONFLICT_STABLE_ID","existing_sha256":sid["sha256"],"candidate_sha256":sha,"stable_id":a.stable_id}
else:
    rec={**base,"sha256":sha,"glyph":glyph(a.domain,a.concept,sha),"vector64":vector(a.summary+" "+a.concept),"canonical_id":f"{a.domain.upper()}:M1:{sha}"}
    with DB.open("a") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    out={"status":"ADMITTED","record":rec}
OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(out,ensure_ascii=False)); sys.exit(3 if out["status"]=="CONFLICT_STABLE_ID" else 0)
