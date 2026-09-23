import math,json,hashlib,pathlib,random,statistics
OUT=pathlib.Path("artifacts/robustness_mc_v7.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.5
N=200;seed=720122;R=random.Random(seed)
nom={"lat":28.5,"target_h":400e3,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"p0":10.,"p1":160.,"ed":5.,"maxq":45000.,"maxg":4.5}
def run(i):
 T=nom["T"]*(1+R.gauss(0,.01));Isp=nom["Isp"]*(1+R.gauss(0,.005));m0=nom["m0"]*(1+R.gauss(0,.005));Cd=nom["Cd"]*(1+R.gauss(0,.05));rhoScale=max(.7,min(1.3,1+R.gauss(0,.08)));p0=nom["p0"]+R.gauss(0,1.);p1=nom["p1"]+R.gauss(0,3.);ed=max(0,nom["ed"]+R.gauss(0,1.))
 r=Re;vr=0.;vt=omega*Re*math.cos(math.radians(nom["lat"]));m=m0;t=0.;mq=pg=0.;md=T/(Isp*g0)
 while t<nom["burn"] and m>nom["mf"]:
  h=max(0.,r-Re);rho=rho0*rhoScale*math.exp(-h/H);v=math.hypot(vr,vt);q=.5*rho*v*v;mq=max(mq,q);D=q*Cd*nom["A"]
  f=min(1.,max(0.,(t-p0)/(p1-p0)));ga=math.radians(90-(90-ed)*f);Tr=T*math.sin(ga);Tt=T*math.cos(ga);Dr=D*vr/v if v else 0.;Dt=D*vt/v if v else 0.
  ar=Tr/m-Dr/m-mu/r**2+vt*vt/r;at=Tt/m-Dt/m-vr*vt/r;pg=max(pg,math.hypot(Tr-Dr,Tt-Dt)/m/g0)
  vr+=ar*dt;vt+=at*dt;r=max(Re,r+vr*dt);m=max(nom["mf"],m-md*dt);t+=dt
 h=r-Re;v=math.hypot(vr,vt);E=.5*v*v-mu/r;vc=math.sqrt(mu/(Re+nom["target_h"]))
 if E<0:
  a=-mu/(2*E);e=math.sqrt(max(0.,1-(r*vt)**2/(mu*a)));rp=a*(1-e)-Re
 else:rp=-1e9
 crit={"alt":abs(h-nom["target_h"])<=20e3,"vr":abs(vr)<=100.,"vt":abs(vt-vc)<=150.,"bound":E<0,"perigee":rp>=120e3,"maxq":mq<=nom["maxq"],"maxg":pg<=nom["maxg"]}
 return {"i":i,"pass":all(crit.values()),"criteria":crit,"h":h,"vr":vr,"vt":vt,"perigee_h":rp,"max_q":mq,"peak_g":pg}
rows=[run(i) for i in range(N)];passes=sum(x["pass"] for x in rows);rate=passes/N
fails={k:sum(not x["criteria"][k] for x in rows) for k in rows[0]["criteria"]}
body={"schema":"CEREBRON_ROBUSTNESS_MC_V7","seed":seed,"samples":N,"pass_count":passes,"pass_rate":rate,"failure_counts":fails,"metrics":{"altitude_mean":statistics.mean(x["h"] for x in rows),"altitude_stdev":statistics.pstdev(x["h"] for x in rows),"max_q_p95":sorted(x["max_q"] for x in rows)[int(.95*(N-1))],"peak_g_p95":sorted(x["peak_g"] for x in rows)[int(.95*(N-1))]},"epistemic":["DETERMINISTIC_SEEDED_MONTE_CARLO","ASSUMED_GAUSSIAN_UNCERTAINTIES","UNCERTAINTY_MODEL_NOT_CALIBRATED","200_SAMPLES_ONLY","NO_HARDWARE_VALIDATION"],"sample_preview":rows[:10]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
