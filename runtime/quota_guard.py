import argparse, datetime, json, pathlib, sys

CFG=pathlib.Path("config/memory-fabric-v1.json")
LEDGER=pathlib.Path("runtime/quota_ledger.json")
OUT=pathlib.Path("artifacts/quota_state.json")
DOMAINS=["COLLATZ","AGORA_TASKS","LEARNING","SIMULATION","SPACE_WORLD","AELYS_ELYRA","GOLD_PROMOTION","MEMORY_MUTATIONS"]

def load():
    if LEDGER.exists(): return json.loads(LEDGER.read_text())
    return {"schema":"CEREBRON_QUOTA_LEDGER_V1","totals":{d:{"generated":0,"persisted":0,"gold":0,"files":0,"requests":0,"runtime_seconds":0} for d in DOMAINS}}

def level(p,e):
    if p>=e["freeze_pct"]: return "FREEZE"
    if p>=e["raw_stop_pct"]: return "RAW_STOP"
    if p>=e["compress_pct"]: return "COMPRESS"
    if p>=e["soft_pct"]: return "WARN"
    return "NORMAL"

ap=argparse.ArgumentParser()
ap.add_argument("--domain",choices=DOMAINS,required=True)
ap.add_argument("--generated",type=int,default=0);ap.add_argument("--persisted",type=int,default=0)
ap.add_argument("--gold",type=int,default=0);ap.add_argument("--files",type=int,default=0)
ap.add_argument("--requests",type=int,default=0);ap.add_argument("--runtime-seconds",type=float,default=0)
ap.add_argument("--capacity-bytes",type=int,required=True)
a=ap.parse_args()
if min(a.generated,a.persisted,a.gold,a.files,a.requests,a.runtime_seconds,a.capacity_bytes)<0 or a.capacity_bytes==0: sys.exit(2)

cfg=json.loads(CFG.read_text()); e=cfg["emergency"]; x=load(); t=x["totals"][a.domain]
for k,v in {"generated":a.generated,"persisted":a.persisted,"gold":a.gold,"files":a.files,"requests":a.requests,"runtime_seconds":a.runtime_seconds}.items(): t[k]+=v
used=sum(v["persisted"] for v in x["totals"].values()); pct=min(100.0,100.0*used/a.capacity_bytes); st=level(pct,e)
x.update({"updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"capacity_bytes":a.capacity_bytes,"persisted_bytes":used,"usage_pct":pct,"state":st})
x["policy"]={"allow_raw_write":st not in ("RAW_STOP","FREEZE"),"force_compression":st in ("COMPRESS","RAW_STOP","FREEZE"),"allow_new_cycles":st!="FREEZE"}
LEDGER.write_text(json.dumps(x,indent=2)+"\n");OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(x,indent=2)+"\n")
print(json.dumps(x));sys.exit(4 if st=="FREEZE" else 0)
