import csv,json,hashlib,pathlib,math
DATA=pathlib.Path("external/nasa_nesc/occ06c_time_history.csv");OUT=pathlib.Path("artifacts/nasa_residuals_v26.json");OUT.parent.mkdir(exist_ok=True)
req=["time_s","x_m","y_m","z_m","vx_m_s","vy_m_s","vz_m_s"];mu=3.986004418e14
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,k):return tuple(x*k for x in a)
def norm(a):return math.sqrt(sum(x*x for x in a))
def deriv(s):
 r=s[:3];v=s[3:];rn=norm(r);a=mul(r,-mu/rn**3);return v+a
def rk4(s,dt):
 k1=deriv(s);k2=deriv(add(s,mul(k1,dt/2)));k3=deriv(add(s,mul(k2,dt/2)));k4=deriv(add(s,mul(k3,dt)))
 return tuple(s[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(6))
body={"schema":"CEREBRON_NASA_RESIDUALS_V26","case":"OCC06C"}
if not DATA.exists():
 body.update({"decision":"BLOCKED_RAW_NASA_TIME_HISTORY_MISSING","g03_status":"PARTIAL"})
else:
 raw=DATA.read_bytes();rows=list(csv.DictReader(raw.decode().splitlines()));missing=[k for k in req if not rows or k not in rows[0]]
 if missing: body.update({"decision":"BLOCKED_SCHEMA_MISMATCH","missing":missing,"g03_status":"PARTIAL"})
 else:
  R=[[float(x[k]) for k in req] for x in rows];s=tuple(R[0][1:]);t=R[0][0];pe=[];ve=[]
  for row in R:
   target=row[0];gap=target-t
   while gap>1e-12:
    h=min(1.0,gap);s=rk4(s,h);t+=h;gap=target-t
   pe.append(norm(tuple(s[i]-row[i+1] for i in range(3))))
   ve.append(norm(tuple(s[i+3]-row[i+4] for i in range(3))))
  rms=lambda a:math.sqrt(sum(x*x for x in a)/len(a))
  body.update({"decision":"RESIDUALS_COMPUTED","dataset_sha256":hashlib.sha256(raw).hexdigest(),"rows":len(R),"residuals":{"position_rms_m":rms(pe),"position_max_m":max(pe),"velocity_rms_m_s":rms(ve),"velocity_max_m_s":max(ve),"final_position_m":pe[-1],"final_velocity_m_s":ve[-1]},"g03_status":"EXTERNAL_TIME_HISTORY_COMPARED","limits":["ASTRION_MODEL_TWO_BODY_ONLY","NASA_OCC06C_INCLUDES_SUN_PERTURBATION","MODEL_MISMATCH_EXPECTED","NO_VALIDATION_THRESHOLD_FROZEN_YET"],"decision_gate":"OPEN_MODEL_MISMATCH_QUANTIFIED"})
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
