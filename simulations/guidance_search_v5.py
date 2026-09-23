import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/guidance_search_v5.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.5
base={"lat":28.5,"target_h":400e3,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.}
def sim(p0,p1,enddeg):
 r=Re;vr=0.;vt=omega*Re*math.cos(math.radians(base["lat"]));m=base["m0"];t=0.;maxq=0.;mdot=base["T"]/(base["Isp"]*g0)
 while t<base["burn"] and m>base["mf"]:
  h=max(0.,r-Re);rho=rho0*math.exp(-h/H);v=math.hypot(vr,vt);q=.5*rho*v*v;maxq=max(maxq,q);D=q*base["Cd"]*base["A"]
  f=min(1.,max(0.,(t-p0)/(p1-p0)));gam=math.radians(90-(90-enddeg)*f);Tr=base["T"]*math.sin(gam);Tt=base["T"]*math.cos(gam)
  Dr=D*vr/v if v else 0.;Dt=D*vt/v if v else 0.;ar=Tr/m-Dr/m-mu/r**2+vt*vt/r;at=Tt/m-Dt/m-vr*vt/r
  vr+=ar*dt;vt+=at*dt;r=max(Re,r+vr*dt);m=max(base["mf"],m-mdot*dt);t+=dt
 h=r-Re;v=math.hypot(vr,vt);E=.5*v*v-mu/r;vc=math.sqrt(mu/(Re+base["target_h"]))
 if E<0:
  a=-mu/(2*E);e=math.sqrt(max(0.,1-(r*vt)**2/(mu*a)));rp=a*(1-e)-Re
 else:rp=-1e9
 crit={"alt":abs(h-base["target_h"])<=20e3,"vr":abs(vr)<=100.,"vt":abs(vt-vc)<=150.,"bound":E<0,"perigee":rp>=120e3}
 score=(abs(h-base["target_h"])/20000)+(abs(vr)/100)+(abs(vt-vc)/150)+(0 if E<0 else 20)+(0 if rp>=120e3 else min(20,(120e3-rp)/10000))
 return {"pitch_start_s":p0,"pitch_end_s":p1,"terminal_angle_deg":enddeg,"score":score,"criteria":crit,"pass":all(crit.values()),"h":h,"vr":vr,"vt":vt,"perigee_h":rp,"max_q":maxq}
rows=[]
for p0 in [5,10,15,20]:
 for p1 in [120,150,180,210]:
  if p1<=p0:continue
  for ed in [0,5,10,15,20]:rows.append(sim(p0,p1,ed))
rows.sort(key=lambda x:x["score"]);best=rows[0]
body={"schema":"CEREBRON_GUIDANCE_SEARCH_V5","method":"DETERMINISTIC_GRID_SEARCH","evaluated":len(rows),"best":best,"top10":rows[:10],"epistemic":["SEARCH_NOT_PROOF_OF_GLOBAL_OPTIMUM","3DOF_POINT_MASS","COARSE_GRID","NO_6DOF","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
