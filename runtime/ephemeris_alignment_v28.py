import json,hashlib,pathlib,math,datetime
OUT=pathlib.Path("artifacts/ephemeris_alignment_v28.json");OUT.parent.mkdir(exist_ok=True)
# Fail-closed contract for OCC06C solar ephemeris. No fabricated epoch/frame conversion.
E=pathlib.Path("external/nasa_nesc/occ06c_ephemeris.json")
required={"epoch_utc","frame","time_scale","sun_position_source","sun_ephemeris_sha256"}
body={"schema":"CEREBRON_EPHEMERIS_ALIGNMENT_V28","case":"OCC06C","ephemeris_path":str(E)}
if not E.exists():
 body.update({"decision":"BLOCKED_EPHEMERIS_NOT_INGESTED","alignment_ready":False,"missing":sorted(required),"g02_status":"PARTIAL","g03_status":"PARTIAL"})
else:
 d=json.loads(E.read_text());missing=sorted(required-set(d))
 frame_ok=d.get("frame") in {"J2000","ICRF"};scale_ok=d.get("time_scale") in {"UTC","TT","TDB"}
 sha=d.get("sun_ephemeris_sha256","");sha_ok=isinstance(sha,str) and len(sha)==64
 epoch_ok=False
 try: datetime.datetime.fromisoformat(d.get("epoch_utc","").replace("Z","+00:00"));epoch_ok=True
 except: pass
 checks={"schema_complete":not missing,"frame_supported":frame_ok,"time_scale_supported":scale_ok,"sha256_present":sha_ok,"epoch_parseable":epoch_ok}
 body.update({"decision":"READY_FOR_TIME_ALIGNED_SOLAR_PROPAGATION" if all(checks.values()) else "BLOCKED_ALIGNMENT_METADATA","alignment_ready":all(checks.values()),"checks":checks,"metadata":d,"g02_status":"PARTIAL","g03_status":"PARTIAL"})
body["requirements_next"]=["EPHEMERIS_INTERPOLATION","TIME_SCALE_CONVERSION_IF_REQUIRED","FRAME_TRANSFORM_IF_REQUIRED","POINTWISE_OCC06C_ABLATION"]
body["epistemic"]=["NO_ASSUMED_OCC06C_EPOCH","NO_FAKE_EPHEMERIS","FRAME_TIME_ALIGNMENT_REQUIRED","FAIL_CLOSED","NO_VALIDATION_CLAIM"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
