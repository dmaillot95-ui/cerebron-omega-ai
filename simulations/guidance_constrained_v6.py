import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/guidance_constrained_v6.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.5
C={"lat":28.5,"target_h":400e3,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"max_q_pa":45000.,"max_g":4.5,"allow_pa":350e6,"axial_area_m2":.08,"sf":1.5}
def sim(p0,p1,ed):
 r=Re;vr=0.;vt=omega*Re*math.cos(math.radians(C["lat"]));m=C["m0"];t=0.;mq=pg=ps=0.;md=C["T"]/(C["Isp"]*g0)
 while t<C["burn"] and m>C["mf"]:
  h=max(0.,r-Re);rho=rho0*math.exp(-h/H);v=math.hypot(vr,vt);q=.5*rho*v*v;D=q*C["Cd"]*C["A"];mq=max(mq,q)
  f=min(1.,max(0.,(t-p0)/(p1-p0)));ga=math.radians(90-(90-ed)*f);Tr=C["T"]*math.sin(ga);Tt=C["T"]*math.cos(ga)
  Dr=D*vr/v if v else 0.;Dt=D*vt/v if v else 0.;ar=Tr/m-Dr/m-mu/r**2+vt*vt/r;at=Tt/m-Dt/m-vr*vt/r
  proper=math.hypot(Tr-Dr,Tt-Dt)/m;pg=max(pg,proper/g0);ps=max(ps,proper*m/C["axial_area_m2"])
  vr+=ar*dt;vt+=at*dt;r=max(Re,r+vr*dt);m=max(C["mf"],m-md*dt);t+=dt
 h=r-Re;v=math.hypot(vr,vt);E=.5*v*v-mu/r;vc=math.sqrt(mu/(Re+C["target_h"]))
 if E<0:
  a=-mu/(2*E);e=math.sqrt(max(0.,1-(r*vt)**2/(mu*a)));rp=a*(1-e)-Re
 else:rp=-1e9
 orb=abs(h-C["target_h"])/20000+abs(vr)/100+abs(vt-vc)/150+(0 if E<0 else 20)+(0 if rp>=120e3 else min(20,(120e3-rp)/10000))
 struct_margin=C["allow_pa"]/(ps*C["sf"])-1 if ps else 999.
 cons={"max_q":mq<=C["max_q_pa"],"max_g":pg<=C["max_g"],"structure":struct_margin>=0}
 penalty=sum(50 for ok in cons.values() if not ok)
 return {"p0":p0,"p1":p1,"enddeg":ed,"objective":orb+penalty,"orbital_score":orb,"constraints":cons,"max_q_pa":mq,"peak_g":pg,"structural_margin":struct_margin,"h":h,"vr":vr,"vt":vt,"perigee_h":rp}
# stage 1 coarse
rows=[sim(a,b,e) for a in [5,10,15,20] for b in [120,150,180,210] for e in [0,5,10,15,20] if b>a];rows.sort(key=lambda x:x["objective"])
# stage 2 deterministic local refinement around top 3
seen={(x["p0"],x["p1"],x["enddeg"]) for x in rows}
for seed in rows[:3]:
 for da in [-2.5,0,2.5]:
  for db in [-10,0,10]:
   for de in [-2.5,0,2.5]:
    k=(seed["p0"]+da,seed["p1"]+db,max(0,seed["enddeg"]+de))
    if k not in seen and k[1]>k[0]:rows.append(sim(*k));seen.add(k)
rows.sort(key=lambda x:x["objective"]);best=rows[0]
body={"schema":"CEREBRON_GUIDANCE_CONSTRAINED_V6","method":"COARSE_PLUS_LOCAL_REFINEMENT","evaluated":len(rows),"constraints":{"max_q_pa":C["max_q_pa"],"max_g":C["max_g"],"allowable_stress_pa":C["allow_pa"],"safety_factor":C["sf"]},"best":best,"top10":rows[:10],"epistemic":["CONSTRAINT_AWARE_SEARCH","STRUCTURAL_MODEL_AXIAL_ONLY","SEARCH_NOT_GLOBAL_OPTIMUM","NO_BUCKLING","NO_AEROELASTICITY","NO_6DOF","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
