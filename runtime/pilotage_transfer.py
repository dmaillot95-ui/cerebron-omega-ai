import argparse, hashlib, json, pathlib, datetime, sys
ROOT=pathlib.Path("agora");ROOT.mkdir(exist_ok=True)
DB=ROOT/"pilotage_registry.jsonl";OUT=pathlib.Path("artifacts/pilotage_decision.json")
AIS={"SAPHEA","SPIRALION","ETHERION","HYPERION","ASTRION","METRION"}
def rows():
    return [json.loads(x) for x in DB.read_text().splitlines() if x.strip()] if DB.exists() else []
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
ap=argparse.ArgumentParser()
ap.add_argument("--source",choices=sorted(AIS),required=True);ap.add_argument("--target",choices=sorted(AIS),required=True)
ap.add_argument("--domain",required=True);ap.add_argument("--method",required=True);ap.add_argument("--evidence",required=True)
ap.add_argument("--baseline",type=float,required=True);ap.add_argument("--candidate",type=float,required=True)
ap.add_argument("--independent-retest",choices=["PASS","FAIL"],required=True)
a=ap.parse_args()
gain=a.candidate-a.baseline
decision="ACCEPT_FOR_TARGET" if gain>0 and a.independent_retest=="PASS" else "REJECT"
body={"source":a.source,"target":a.target,"domain":a.domain,"method":a.method,"evidence":a.evidence,"baseline":a.baseline,"candidate":a.candidate,"gain":gain,"independent_retest":a.independent_retest}
sha=h(body); rec={**body,"pilotage_id":"PILOT:"+sha[:20],"sha256":sha,"glyph":f"Ω⟦PILOT:{a.source}>{a.target}:{a.domain.upper()}:{sha[:8]}⟧","decision":decision,"scope":"TARGET_ONLY","gold_eligible":False,"training_eligible":False,"requires":["F72","AFAH"] if decision=="ACCEPT_FOR_TARGET" else [],"created_at":datetime.datetime.now(datetime.timezone.utc).isoformat()}
if not any(x["sha256"]==sha for x in rows()):
    with DB.open("a") as f:f.write(json.dumps(rec)+"\n")
OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(rec,indent=2)+"\n");print(json.dumps(rec));sys.exit(0 if decision=="ACCEPT_FOR_TARGET" else 5)
