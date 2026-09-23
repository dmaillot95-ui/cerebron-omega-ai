import csv,json,hashlib,pathlib,math,bisect
HIST=pathlib.Path("external/nasa_nesc/occ06c_time_history.csv");EPH=pathlib.Path("external/nasa_nesc/occ06c_sun_ephemeris.csv");META=pathlib.Path("external/nasa_nesc/occ06c_ephemeris.json");OUT=pathlib.Path("artifacts/occ06c_solar_ablation_v30.json");OUT.parent.mkdir(exist_ok=True)
muE=3.986004418e14;muS=1.32712440018e20
def norm(a):return math.sqrt(sum(x*x for x in a))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,k):return tuple(k*x for x in a)
body={"schema":"CEREBRON_OCC06C_SOLAR_ABLATION_V30"}
if not (HIST.exists() and EPH.exists() and META.exists()):
 body.update({"decision":"BLOCKED_EXTERNAL_INPUTS_MISSING","ready":False,"missing":[str(p) for p in (HIST,EPH,META) if not p.exists()]})
else:
 hr=list(csv.DictReader(HIST.read_text().splitlines()));er=list(csv.DictReader(EPH.read_text().splitlines()));meta=json.loads(META.read_text())
 H=[[float(r[k]) for k in ["time_s","x_m","y_m","z_m","vx_m_s","vy_m_s","vz_m_s"]] for r in hr];E=[[float(r[k]) for k in ["time_s","sun_x_m","sun_y_m","sun_z_m"]] for r in er];et=[r[0] for r in E]
 ephsha=hashlib.sha256(EPH.read_bytes()).hexdigest()
 if ephsha!=meta.get("sun_ephemeris_sha256"): body.update({"decision":"BLOCKED_EPHEMERIS_SHA_MISMATCH","ready":False})
 elif H[0][0]<E[0][0] or H[-1][0]>E[-1][0]: body.update({"decision":"BLOCKED_EPHEMERIS_COVERAGE","ready":False})
 else:
  def sun(t):
   i=bisect.bisect_right(et,t)-1;i=max(0,min(i,len(E)-2));w=(t-E[i][0])/(E[i+1][0]-E[i][0]);return tuple(E[i][j]*(1-w)+E[i+1][j]*w for j in range(1,4))
  def deriv(s,t,solar):
   r=s[:3];v=s[3:];rn=norm(r);a=mul(r,-muE/rn**3)
   if solar:
    rs=sun(t);d=sub(rs,r);a=add(a,sub(mul(d,muS/norm(d)**3),mul(rs,muS/norm(rs)**3)))
   return v+a
  def rk4(s,t,h,solar):
   k1=deriv(s,t,solar);k2=deriv(add(s,mul(k1,h/2)),t+h/2,solar);k3=deriv(add(s,mul(k2,h/2)),t+h/2,solar);k4=deriv(add(s,mul(k3,h)),t+h,solar);return tuple(s[i]+h*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(6))
  def run(solar):
   s=tuple(H[0][1:]);t=H[0][0];pe=[];ve=[]
   for row in H:
    while row[0]-t>1e-12:
     h=min(1.,row[0]-t);s=rk4(s,t,h,solar);t+=h
    pe.append(norm(tuple(s[i]-row[i+1] for i in range(3))));ve.append(norm(tuple(s[i+3]-row[i+4] for i in range(3))))
   rms=lambda x:math.sqrt(sum(v*v for v in x)/len(x))
   return {"position_rms_m":rms(pe),"position_max_m":max(pe),"velocity_rms_m_s":rms(ve),"velocity_max_m_s":max(ve)}
  earth=run(False);solar=run(True)
  body.update({"decision":"ABLATION_COMPUTED","ready":True,"earth_only":earth,"earth_plus_sun":solar,"improvement":{"position_rms_m":earth["position_rms_m"]-solar["position_rms_m"],"velocity_rms_m_s":earth["velocity_rms_m_s"]-solar["velocity_rms_m_s"]},"g03_status":"EXTERNAL_TIME_HISTORY_ABLATION_COMPUTED"})
body["epistemic"]=["POINTWISE_EXTERNAL_COMPARISON","SOLAR_THIRD_BODY_ABLATION","IMPROVEMENT_MEASURED_NOT_ASSUMED","NO_AUTOMATIC_VALIDATION","F72_REMAINS_BLOCKED_PENDING_THRESHOLDS_AND_REVIEW"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
