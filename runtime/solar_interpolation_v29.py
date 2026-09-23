import csv,json,hashlib,pathlib,math,bisect
META=pathlib.Path("external/nasa_nesc/occ06c_ephemeris.json");CSV=pathlib.Path("external/nasa_nesc/occ06c_sun_ephemeris.csv");OUT=pathlib.Path("artifacts/solar_interpolation_v29.json");OUT.parent.mkdir(exist_ok=True)
req=["time_s","sun_x_m","sun_y_m","sun_z_m"];body={"schema":"CEREBRON_SOLAR_INTERPOLATION_V29","case":"OCC06C"}
if not META.exists() or not CSV.exists():
 body.update({"decision":"BLOCKED_EPHEMERIS_FILES_MISSING","ready":False,"missing":[str(p) for p in (META,CSV) if not p.exists()]})
else:
 meta=json.loads(META.read_text());raw=CSV.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()));missing=[k for k in req if not rows or k not in rows[0]]
 if missing: body.update({"decision":"BLOCKED_EPHEMERIS_SCHEMA","ready":False,"missing_columns":missing})
 else:
  a=[[float(r[k]) for k in req] for r in rows];mono=all(a[i][0]>a[i-1][0] for i in range(1,len(a)));finite=all(math.isfinite(x) for r in a for x in r)
  sha=hashlib.sha256(raw).hexdigest();sha_match=sha==meta.get("sun_ephemeris_sha256")
  # deterministic midpoint interpolation self-check: linear interpolation must reproduce segment midpoint.
  interp_ok=True;max_mid_err=0.
  for i in range(max(0,len(a)-1)):
   t=(a[i][0]+a[i+1][0])/2;w=(t-a[i][0])/(a[i+1][0]-a[i][0]);p=[a[i][j]*(1-w)+a[i+1][j]*w for j in range(1,4)];ref=[(a[i][j]+a[i+1][j])/2 for j in range(1,4)];err=math.sqrt(sum((p[j]-ref[j])**2 for j in range(3)));max_mid_err=max(max_mid_err,err)
  interp_ok=max_mid_err<1e-6
  ready=len(a)>=2 and mono and finite and sha_match and interp_ok
  body.update({"decision":"READY_FOR_SYNCHRONIZED_SOLAR_PROPAGATION" if ready else "BLOCKED_EPHEMERIS_INTEGRITY","ready":ready,"rows":len(a),"dataset_sha256":sha,"checks":{"strict_time_monotonic":mono,"finite":finite,"sha_matches_metadata":sha_match,"linear_interpolation_self_check":interp_ok},"max_midpoint_self_error_m":max_mid_err})
body["g02_status"]="PARTIAL";body["g03_status"]="PARTIAL";body["epistemic"]=["LINEAR_EPHEMERIS_INTERPOLATION","NO_EXTRAPOLATION_AUTHORIZED","SHA_BOUND_EXTERNAL_DATA","TIME_FRAME_ALIGNMENT_MUST_PASS_V28","NO_VALIDATION_CLAIM"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
