import csv,json,hashlib,pathlib,math
OUT=pathlib.Path("artifacts/nasa_pointwise_v25.json");OUT.parent.mkdir(exist_ok=True)
DATA=pathlib.Path("external/nasa_nesc/occ06c_time_history.csv")
required=["time_s","x_m","y_m","z_m","vx_m_s","vy_m_s","vz_m_s"]
body={"schema":"CEREBRON_NASA_POINTWISE_V25","case":"OCC06C","dataset_path":str(DATA),"requirements":required}
if not DATA.exists():
 body.update({"decision":"BLOCKED_RAW_NASA_TIME_HISTORY_MISSING","g03_status":"PARTIAL_EXTERNAL_INITIAL_CONDITION","rows":0,"epistemic":["FAIL_CLOSED","NO_SYNTHETIC_REFERENCE_POINTS","NO_POINTWISE_CLAIM_WITHOUT_RAW_DATA"]})
else:
 raw=DATA.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()));cols=rows[0].keys() if rows else []
 missing=[x for x in required if x not in cols]
 if missing:
  body.update({"decision":"BLOCKED_SCHEMA_MISMATCH","missing_columns":missing,"rows":len(rows),"dataset_sha256":hashlib.sha256(raw).hexdigest(),"g03_status":"PARTIAL_EXTERNAL_INITIAL_CONDITION"})
 else:
  vals=[];ok=True
  for row in rows:
   try: vals.append([float(row[k]) for k in required])
   except: ok=False;break
  monotonic=ok and all(vals[i][0]>vals[i-1][0] for i in range(1,len(vals)))
  finite=ok and all(math.isfinite(x) for r in vals for x in r)
  body.update({"decision":"READY_FOR_PROPAGATOR_POINTWISE_RESIDUALS" if rows and monotonic and finite else "BLOCKED_DATA_QUALITY","rows":len(rows),"dataset_sha256":hashlib.sha256(raw).hexdigest(),"quality":{"numeric":ok,"finite":finite,"strict_time_monotonic":monotonic},"g03_status":"EXTERNAL_TIME_HISTORY_INGESTED_NOT_YET_REPRODUCED"})
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
