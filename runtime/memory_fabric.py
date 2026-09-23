import hashlib,json,pathlib,sys
ROOT=pathlib.Path("memory_index");ROOT.mkdir(exist_ok=True)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def admit(namespace,klass,payload,producer,cycle):
 raw=canonical(payload);sha=hashlib.sha256(raw).hexdigest();mid=f"{namespace}:{klass}:{sha[:16]}"
 return {"memory_id":mid,"namespace":namespace,"class":klass,"sha256":sha,"bytes":len(raw),"backend":"POINTER_ONLY_CANARY","object_key":f"{namespace}/{sha[:2]}/{sha}.json","producer":producer,"cycle_id":cycle,"replay_recipe":payload.get("replay_recipe"),"epistemic":payload.get("epistemic","UNSPECIFIED")}
p={"seed":20260923,"config_sha":"abc","metrics":{"loss":0.1},"replay_recipe":"seed+config+version","epistemic":"SIMULATED"}
a=admit("SIMULATION","M2",p,"F113","MEM-CANARY-1");b=admit("SIMULATION","M2",p,"F113","MEM-CANARY-1")
checks={"dedup_id":a["memory_id"]==b["memory_id"],"dedup_sha":a["sha256"]==b["sha256"],"content_addressed":a["sha256"] in a["object_key"],"small_manifest":len(canonical(a))<2048}
out={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"manifest":a,"note":"CONTROL_PLANE_CANARY_ONLY_NO_EXTERNAL_STORAGE_WRITE"}
pathlib.Path("artifacts").mkdir(exist_ok=True);pathlib.Path("artifacts/memory_fabric.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out));sys.exit(0 if out["status"]=="PASS" else 1)
