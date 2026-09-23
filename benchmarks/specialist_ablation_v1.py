import json, pathlib, hashlib, sys
OUT=pathlib.Path("artifacts/specialist_ablation.json"); OUT.parent.mkdir(exist_ok=True)

CASES=[
 {"id":"SP-ORB-01","domain":"ORBITAL_MECHANICS","facts":{"simulation":True,"physical_test":False,"independent_check":True},"expected":"NOT_PHYSICALLY_VALIDATED"},
 {"id":"SP-THM-01","domain":"THERMAL","facts":{"simulation":True,"physical_test":True,"calibrated":False},"expected":"CALIBRATION_REQUIRED"},
 {"id":"EN-TOL-01","domain":"TOLERANCES","facts":{"units_checked":False,"independent_check":True},"expected":"UNITS_REQUIRED"},
 {"id":"EN-VAL-01","domain":"VALIDATION","facts":{"simulation":True,"physical_test":True,"calibrated":True,"independent_check":True},"expected":"ELIGIBLE_FOR_F72"}
]
def baseline(c):
 f=c["facts"]
 if f.get("simulation"): return "RESULT_AVAILABLE"
 if f.get("independent_check"): return "CHECKED"
 return "OPEN"
def specialist(c):
 f=c["facts"]
 if f.get("units_checked") is False:return "UNITS_REQUIRED"
 if f.get("simulation") and not f.get("physical_test"):return "NOT_PHYSICALLY_VALIDATED"
 if f.get("physical_test") and not f.get("calibrated",False):return "CALIBRATION_REQUIRED"
 if f.get("physical_test") and f.get("calibrated") and f.get("independent_check"):return "ELIGIBLE_FOR_F72"
 return "OPEN"
rows=[]
for c in CASES:
 b=baseline(c); s=specialist(c)
 rows.append({"id":c["id"],"expected":c["expected"],"baseline":b,"specialist":s,"baseline_ok":b==c["expected"],"specialist_ok":s==c["expected"]})
bs=sum(x["baseline_ok"] for x in rows)/len(rows); ss=sum(x["specialist_ok"] for x in rows)/len(rows)
body={"schema":"CEREBRON_SPECIALIST_ABLATION_V1","benchmark":"COLD_SYNTHETIC_POLICY_GATE","cases":rows,"baseline_score":bs,"specialist_score":ss,"gain":ss-bs,"limits":["SYNTHETIC_POLICY_TEST","NOT_MODEL_INTELLIGENCE_BENCHMARK","NOT_PHYSICAL_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
sys.exit(0 if body["gain"]>0 else 6)
