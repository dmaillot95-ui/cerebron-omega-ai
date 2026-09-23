import json,hashlib,pathlib,datetime
ROOT=pathlib.Path("artifacts");OUT=ROOT/"evidence_pack_v9.json"
expected=[
 ("V1","space_vehicle_chain.json"),("V2","ascent_3dof.json"),("V3","orbit_target_v3.json"),
 ("V4","orbit_insertion_v4.json"),("V5","guidance_search_v5.json"),("V6","guidance_constrained_v6.json"),
 ("V7","robustness_mc_v7.json"),("V8","failure_injection_v8.json")]
items=[];missing=[]
for ver,name in expected:
 p=ROOT/name
 if not p.exists():missing.append({"version":ver,"artifact":name});continue
 raw=p.read_bytes();d=json.loads(raw)
 items.append({"version":ver,"artifact":name,"artifact_sha256":hashlib.sha256(raw).hexdigest(),"embedded_sha256":d.get("sha256"),"schema":d.get("schema"),"epistemic":d.get("epistemic",[])})
limits=sorted({x for i in items for x in i["epistemic"]})
contr=[]
if any("NO_HARDWARE_VALIDATION" in i["epistemic"] for i in items):contr.append("NO_HARDWARE_EVIDENCE")
if any("SEARCH_NOT_GLOBAL_OPTIMUM" in i["epistemic"] or "SEARCH_NOT_PROOF_OF_GLOBAL_OPTIMUM" in i["epistemic"] for i in items):contr.append("OPTIMUM_NOT_PROVEN")
if any("UNCERTAINTY_MODEL_NOT_CALIBRATED" in i["epistemic"] for i in items):contr.append("UNCERTAINTY_NOT_CALIBRATED")
complete=len(items)==len(expected)
maturity="S5_ARTIFACT_PLUS_SHA" if complete else "S2_WORKFLOW_PRESENT_PARTIAL_EVIDENCE"
decision="OPEN_REQUIRES_REPRODUCTION_CALIBRATION" if complete else "RED_INCOMPLETE_EVIDENCE_CHAIN"
body={"schema":"CEREBRON_EVIDENCE_PACK_V9","expected_count":len(expected),"observed_count":len(items),"complete":complete,"items":items,"missing":missing,"maturity":maturity,"contradictions_or_gaps":contr,"decision":decision,"gates":{"METRION":"STRUCTURAL_EVIDENCE_AUDIT_ONLY","F72":"NOT_YET_VALIDATED","AFAH":"NOT_YET_PROMOTED"},"rules":["CLAIM_LE_EVIDENCE","SIMULATION_NE_TEST","WORKFLOW_SUCCESS_NE_PHYSICAL_VALIDATION","REPRODUCTION_REQUIRED","CALIBRATION_REQUIRED_BEFORE_S8"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
