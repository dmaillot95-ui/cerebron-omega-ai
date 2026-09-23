import json,hashlib,pathlib
BASE={"schema_version":"SPACE_STATE_V2","cycle_id":"FAULT-CANARY-0001","source":101,"destination":102,"logical_slot":1,"payload":{"environment":{"gravity_m_s2":1.62,"solar_factor":1.0,"terrain_cells":64}}}
def digest(p): return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def verify(p,last_slot=0,seen=None):
 seen=seen or set(); errs=[]
 for k in ("schema_version","cycle_id","source","destination","logical_slot","payload","payload_sha"):
  if k not in p: errs.append("MISSING_"+k)
 if errs:return False,errs
 if p["schema_version"]!="SPACE_STATE_V2":errs.append("SCHEMA")
 if p["destination"]!=102:errs.append("DESTINATION")
 if p["logical_slot"]<=last_slot:errs.append("STALE_SLOT")
 if p["cycle_id"] in seen:errs.append("DUPLICATE_CYCLE")
 q=dict(p); claimed=q.pop("payload_sha");
 if digest(q["payload"])!=claimed:errs.append("PAYLOAD_HASH")
 return not errs,errs
base=dict(BASE);base["payload_sha"]=digest(base["payload"])
cases={"valid":base,"missing":{k:v for k,v in base.items() if k!="payload"},"stale":dict(base,logical_slot=0),"duplicate":base,"corrupt":json.loads(json.dumps(base))}
cases["corrupt"]["payload"]["environment"]["gravity_m_s2"]=9.99
results={}
for name,p in cases.items():
 ok,errs=verify(p,last_slot=0,seen={base["cycle_id"]} if name=="duplicate" else set());results[name]={"accepted":ok,"errors":errs}
expected={"valid":True,"missing":False,"stale":False,"duplicate":False,"corrupt":False}
passed=all(results[k]["accepted"]==v for k,v in expected.items())
out={"status":"PASS" if passed else "FAIL","checks":results,"epistemic":"DISTRIBUTED_PACKET_FAILURE_GATE_CANARY_NOT_PHYSICAL_VALIDATION"}
pathlib.Path("artifacts/space-world-fault-gate").mkdir(parents=True,exist_ok=True);pathlib.Path("artifacts/space-world-fault-gate/result.json").write_text(json.dumps(out,indent=2)+"\\n");print(json.dumps(out));raise SystemExit(0 if passed else 1)
