import json,hashlib,pathlib,copy
CYCLE="SPACE-E2E-VERIFY-0001";SEED=20260923
payloads=[{"farm":i,"value":i*i,"cycle":CYCLE,"seed":SEED} for i in range(101,111)]
def chain(items):
 parent="GENESIS";out=[]
 for x in items:
  p={**x,"parent_sha":parent};raw=json.dumps(p,sort_keys=True,separators=(",",":")).encode();p["outputs_sha"]=hashlib.sha256(raw).hexdigest();out.append(p);parent=p["outputs_sha"]
 return out
def verify(c):
 if c[0]["parent_sha"]!="GENESIS": return False
 for i,p in enumerate(c):
  q={k:v for k,v in p.items() if k!="outputs_sha"};sha=hashlib.sha256(json.dumps(q,sort_keys=True,separators=(",",":")).encode()).hexdigest()
  if sha!=p["outputs_sha"]: return False
  if i and p["parent_sha"]!=c[i-1]["outputs_sha"]: return False
 return True
a=chain(payloads);b=chain(payloads);replay=(a==b and a[-1]["outputs_sha"]==b[-1]["outputs_sha"])
corrupt=copy.deepcopy(a);corrupt[4]["value"]+=1;corruption_rejected=not verify(corrupt)
wrong_parent=copy.deepcopy(a);wrong_parent[7]["parent_sha"]="BAD";wrong_parent_rejected=not verify(wrong_parent)
checks={"baseline_valid":verify(a),"deterministic_replay":replay,"payload_corruption_rejected":corruption_rejected,"parent_corruption_rejected":wrong_parent_rejected};status="PASS" if all(checks.values()) else "FAIL"
res={"status":status,"checks":checks,"final_sha":a[-1]["outputs_sha"],"epistemic":"PROTOCOL_INTEGRITY_TEST_NOT_PHYSICAL_VALIDATION_NOT_CROSS_REPO_BUS"};pathlib.Path("artifacts/space-integrity").mkdir(parents=True,exist_ok=True);pathlib.Path("artifacts/space-integrity/result.json").write_text(json.dumps(res,indent=2)+"\n");print(json.dumps(res));raise SystemExit(0 if status=="PASS" else 1)
