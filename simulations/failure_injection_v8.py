import json,hashlib,pathlib,math
OUT=pathlib.Path("artifacts/failure_injection_v8.json");OUT.parent.mkdir(exist_ok=True)
SCENARIOS=[
 {"id":"NOMINAL","fault":"NONE","severity":0.0},
 {"id":"THRUST_LOSS_10","fault":"THRUST_SCALE","severity":0.10},
 {"id":"THRUST_LOSS_25","fault":"THRUST_SCALE","severity":0.25},
 {"id":"EARLY_CUTOFF","fault":"BURN_LOSS","severity":0.15},
 {"id":"GUIDANCE_BIAS","fault":"ANGLE_BIAS_DEG","severity":5.0},
 {"id":"DENSE_ATMOS","fault":"RHO_SCALE","severity":0.25},
 {"id":"SENSOR_ALT_BIAS","fault":"ALT_SENSOR_BIAS_M","severity":5000.0}
]
# Safety-oriented degraded-mode policy canary; no real flight-control implementation.
def assess(s):
 f,z=s["fault"],s["severity"]
 if f=="NONE":return "CONTINUE",["NOMINAL"]
 if f=="THRUST_SCALE" and z<=.10:return "DEGRADED_CONTINUE",["RECOMPUTE_GUIDANCE","TIGHTEN_MARGIN"]
 if f=="THRUST_SCALE":return "ABORT",["SAFE_TERMINATION"]
 if f=="BURN_LOSS":return "ABORT",["SAFE_TERMINATION"]
 if f=="ANGLE_BIAS_DEG":return "HOLD_AND_REVALIDATE",["REDUNDANT_GUIDANCE_CHECK","NO_AUTONOMOUS_RESUME"]
 if f=="RHO_SCALE":return "DEGRADED_CONTINUE",["MAX_Q_LIMIT","THROTTLE_POLICY_REQUIRED"]
 if f=="ALT_SENSOR_BIAS_M":return "HOLD_AND_REVALIDATE",["SENSOR_VOTING","INDEPENDENT_STATE_ESTIMATE"]
 return "ABORT",["SAFE_TERMINATION"]
rows=[]
for s in SCENARIOS:
 decision,actions=assess(s);rows.append({**s,"decision":decision,"actions":actions,"recovery_attempted":decision=="DEGRADED_CONTINUE","autonomous_resume":False})
body={"schema":"CEREBRON_FAILURE_INJECTION_V8","scenarios":rows,"counts":{k:sum(x["decision"]==k for x in rows) for k in ["CONTINUE","DEGRADED_CONTINUE","HOLD_AND_REVALIDATE","ABORT"]},"safety_rules":["FAIL_CLOSED","NO_AUTONOMOUS_RESUME_AFTER_SENSOR_OR_GUIDANCE_ANOMALY","SAFE_TERMINATION_FOR_SEVERE_PROPULSION_FAULT","RECOVERY_POLICY_REQUIRES_FURTHER_VALIDATION"],"epistemic":["POLICY_LEVEL_FAILURE_INJECTION","NOT_FLIGHT_SOFTWARE","NO_REAL_FDIR_CERTIFICATION","NO_HARDWARE_IN_LOOP","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
