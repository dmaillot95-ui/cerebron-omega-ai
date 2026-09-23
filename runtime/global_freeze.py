import argparse, datetime, hashlib, json, pathlib, sys

STATE=pathlib.Path("runtime/global_state.json")
OUT=pathlib.Path("artifacts/global_freeze_state.json")
ALLOWED={"RUN","DRAIN","CHECKPOINT","VERIFY","FROZEN","RESUME_VERIFY"}
WRITE_DOMAINS=["COLLATZ","AGORA_TASKS","LEARNING","SIMULATION","SPACE_WORLD","AELYS_ELYRA","GOLD_PROMOTION","MEMORY_MUTATIONS"]

def load():
    if STATE.exists(): return json.loads(STATE.read_text())
    return {"schema":"CEREBRON_GLOBAL_STATE_V1","state":"RUN","generation":0,"writes":{x:True for x in WRITE_DOMAINS}}

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def save(s,event):
    s["updated_at"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    s["generation"]=int(s.get("generation",0))+1
    s["state_sha256"]=digest({k:v for k,v in s.items() if k!="state_sha256"})
    STATE.write_text(json.dumps(s,indent=2)+"\n")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"event":event,"state":s},indent=2)+"\n")

ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["status","freeze","resume"]); a=ap.parse_args()
s=load()

if a.command=="status":
    save(s,"STATUS"); print(json.dumps(s)); sys.exit(0)

if a.command=="freeze":
    # Fail closed: stop new writes before checkpointing.
    s["state"]="DRAIN"; s["writes"]={x:False for x in WRITE_DOMAINS}
    s["drain_complete"]=True
    s["state"]="CHECKPOINT"; s["checkpoint_sha256"]=digest(s)
    s["state"]="VERIFY"
    if not s.get("checkpoint_sha256"): sys.exit(2)
    s["state"]="FROZEN"; s["read_only"]=True
    save(s,"FREEZE"); print(json.dumps(s)); sys.exit(0)

# Resume only from a frozen, read-only checkpoint.
if s.get("state")!="FROZEN" or s.get("read_only") is not True or not s.get("checkpoint_sha256"):
    print("FAIL_CLOSED: resume requires verified frozen checkpoint",file=sys.stderr); sys.exit(3)
s["state"]="RESUME_VERIFY"
s["resume_from_checkpoint_sha256"]=s["checkpoint_sha256"]
s["writes"]={x:True for x in WRITE_DOMAINS}; s["read_only"]=False; s["state"]="RUN"
save(s,"RESUME"); print(json.dumps(s))
