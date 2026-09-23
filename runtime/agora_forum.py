import argparse, hashlib, json, pathlib, datetime, sys
ROOT=pathlib.Path("agora"); ROOT.mkdir(exist_ok=True)
CAPS=ROOT/"capsules.jsonl"; OUT=pathlib.Path("artifacts/agora_capsule.json")
ROLES={"SAPHEA","SPIRALION","ETHERION","HYPERION","ASTRION","METRION","AFAH","CEREBRON"}
KINDS={"QUESTION","METHOD","LESSON","CHALLENGE","CRITIQUE","CORRECTION","PILOTAGE"}
STATES={"PROPOSED","UNDER_TEST","REJECTED","VALIDATED"}

def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def rows():
    if not CAPS.exists(): return []
    return [json.loads(x) for x in CAPS.read_text().splitlines() if x.strip()]

ap=argparse.ArgumentParser()
ap.add_argument("--author",choices=sorted(ROLES),required=True);ap.add_argument("--kind",choices=sorted(KINDS),required=True)
ap.add_argument("--domain",required=True);ap.add_argument("--summary",required=True);ap.add_argument("--evidence",default="")
ap.add_argument("--targets",required=True);ap.add_argument("--parent",default="");ap.add_argument("--state",choices=sorted(STATES),default="PROPOSED")
a=ap.parse_args(); targets=[x.strip().upper() for x in a.targets.split(",") if x.strip()]
if not targets or any(x not in ROLES for x in targets): sys.exit(2)
body={"author":a.author,"kind":a.kind,"domain":a.domain,"summary":a.summary,"evidence":a.evidence,"targets":targets,"parent":a.parent,"state":a.state}
sha=hashlib.sha256(canon(body)).hexdigest(); cid="AGORA:"+sha[:20]
old=next((r for r in rows() if r["sha256"]==sha),None)
if old: out={"status":"DEDUP_EXACT","capsule":old}
else:
    cap={**body,"capsule_id":cid,"sha256":sha,"glyph":f"Ω⟦AGORA:{a.kind}:{a.domain.upper()}:{sha[:8]}⟧","created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"training_eligible":False,"gold_eligible":False}
    with CAPS.open("a") as f:f.write(json.dumps(cap,ensure_ascii=False)+"\n")
    out={"status":"POSTED","capsule":cap}
OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n");print(json.dumps(out,ensure_ascii=False))
