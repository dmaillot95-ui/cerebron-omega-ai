import json,hashlib,pathlib
OUT=pathlib.Path("artifacts/f72_review_packet_v32.json");OUT.parent.mkdir(exist_ok=True)
expected={
"V28":"ephemeris_alignment_v28.json","V29":"solar_interpolation_v29.json","V30":"occ06c_solar_ablation_v30.json","V31":"frozen_acceptance_v31.json"}
items={};missing=[]
for k,f in expected.items():
 p=pathlib.Path("artifacts")/f
 if not p.exists(): missing.append(k);continue
 raw=p.read_bytes();d=json.loads(raw);items[k]={"file":f,"file_sha256":hashlib.sha256(raw).hexdigest(),"embedded_sha256":d.get("sha256"),"decision":d.get("decision")}
deps=["NASA_NESC_OCC06C_SOURCE","EARTH_MU_SHARED","SOLAR_MU_SHARED","ASTRION_NUMERICAL_INTEGRATOR","SAME_EXTERNAL_TIME_HISTORY_FOR_ABLATION"]
contradictions=[]
if "V30" in items:
 d=json.load(open("artifacts/occ06c_solar_ablation_v30.json"))
 if d.get("ready") and d.get("improvement",{}).get("position_rms_m",0)<=0: contradictions.append("SOLAR_MODEL_DID_NOT_IMPROVE_POSITION_RMS")
 if d.get("ready") and d.get("improvement",{}).get("velocity_rms_m_s",0)<=0: contradictions.append("SOLAR_MODEL_DID_NOT_IMPROVE_VELOCITY_RMS")
v31=json.load(open("artifacts/frozen_acceptance_v31.json")) if pathlib.Path("artifacts/frozen_acceptance_v31.json").exists() else {}
candidate=(not missing and v31.get("decision")=="ACCEPTANCE_PASS_CANDIDATE" and not contradictions)
body={"schema":"CEREBRON_F72_REVIEW_PACKET_V32","artifacts":items,"missing":missing,"shared_dependencies":deps,"contradictions":contradictions,"candidate_for_f72_review":candidate,"decision":"F72_REVIEW_PACKET_READY" if candidate else "F72_BLOCKED","afah":"PENDING","open_gaps":["G01_UNCERTAINTY_CALIBRATION","G04_HARDWARE_EVIDENCE","G05_FDIR_VALIDATION"],"epistemic":["PACKET_ASSEMBLY_NOT_INDEPENDENT_EVIDENCE","SHARED_DEPENDENCIES_DISCLOSED","NO_AUTO_PROMOTION","AFAH_AFTER_F72_ONLY"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
