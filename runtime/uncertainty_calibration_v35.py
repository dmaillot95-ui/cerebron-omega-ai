import csv,json,hashlib,pathlib,math,statistics
SRC=pathlib.Path("external/calibration/uncertainty_observations.csv");OUT=pathlib.Path("artifacts/uncertainty_calibration_v35.json");OUT.parent.mkdir(exist_ok=True)
required=["parameter","observed","reference"]
body={"schema":"CEREBRON_UNCERTAINTY_CALIBRATION_V35","source":str(SRC)}
if not SRC.exists():
 body.update({"decision":"BLOCKED_EXTERNAL_CALIBRATION_DATA_MISSING","g01_status":"OPEN","ready":False})
else:
 raw=SRC.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()));missing=[k for k in required if not rows or k not in rows[0]]
 if missing:
  body.update({"decision":"BLOCKED_CALIBRATION_SCHEMA","g01_status":"OPEN","ready":False,"missing_columns":missing})
 else:
  groups={}
  for r in rows:
   p=r["parameter"].strip();o=float(r["observed"]);ref=float(r["reference"])
   if not (math.isfinite(o) and math.isfinite(ref)): raise ValueError("non-finite calibration datum")
   groups.setdefault(p,[]).append(o-ref)
  stats={}
  for p,e in groups.items():
   n=len(e);mean=sum(e)/n;sd=statistics.stdev(e) if n>1 else None
   stats[p]={"n":n,"bias":mean,"sample_std":sd,"rmse":math.sqrt(sum(x*x for x in e)/n),"min_error":min(e),"max_error":max(e)}
  enough=bool(stats) and all(v["n"]>=5 for v in stats.values())
  body.update({"decision":"CALIBRATION_CANDIDATE_READY_FOR_REVIEW" if enough else "BLOCKED_INSUFFICIENT_CALIBRATION_SAMPLES","g01_status":"REVIEW_REQUIRED" if enough else "OPEN","ready":enough,"dataset_sha256":hashlib.sha256(raw).hexdigest(),"parameters":stats})
body["requirements_for_g01_close"]=["EXTERNAL_PROVENANCE","UNIT_AND_DEFINITION_MATCH","REPRESENTATIVE_OPERATING_DOMAIN","INDEPENDENT_REVIEW","FROZEN_ACCEPTANCE_CRITERIA"]
body["epistemic"]=["OBSERVED_RESIDUALS_NOT_ASSUMED_DISTRIBUTIONS","N_GE_5_IS_PIPELINE_MINIMUM_NOT_SCIENTIFIC_SUFFICIENCY","CALIBRATION_CANDIDATE_NOT_VALIDATION","NO_SYNTHETIC_DATA","G01_NOT_AUTO_CLOSED"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
