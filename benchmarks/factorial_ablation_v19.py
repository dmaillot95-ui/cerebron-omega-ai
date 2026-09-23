import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/factorial_ablation_v19.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;J2=1.08262668e-3;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.5
C={"lat":28.5,"lon":-80.6,"az":90.,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"p0":12.,"p1":170.,"ed":5.}
dot=lambda a,b:sum(x*y for x,y in zip(a,b))
cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
norm=lambda a:math.sqrt(dot(a,a))
mul=lambda a,k:tuple(k*x for x in a)
add=lambda a,b:tuple(x+y for x,y in zip(a,b))
lat=math.radians(C["lat"]);lon=math.radians(C["lon"]);az=math.radians(C["az"])
u0=(math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat));e0=(-math.sin(lon),math.cos(lon),0.);n0=cross(u0,e0)
def grav(r,j2):
 x,y,z=r;rr=norm(r);k=-mu/rr**3
 if not j2:return mul(r,k)
 z2=z*z;r2=rr*rr;f=1.5*J2*(Re/rr)**2
 return (k*x*(1-f*(5*z2/r2-1)),k*y*(1-f*(5*z2/r2-1)),k*z*(1-f*(5*z2/r2-3)))
def sim(dynamic,j2):
 r=mul(u0,Re);v=(-omega*r[1],omega*r[0],0.);m=C["m0"];md=C["T"]/(C["Isp"]*g0);t=0.
 while t<C["burn"] and m>C["mf"]:
  rr=norm(r);h=max(0.,rr-Re);u=mul(r,1/rr)
  if dynamic:
   e=cross((0.,0.,1.),u);e=mul(e,1/norm(e));n=cross(u,e)
  else:e,n=e0,n0
  sp=norm(v);rho=rho0*math.exp(-h/H);D=.5*rho*sp*sp*C["Cd"]*C["A"];f=min(1.,max(0.,(t-C["p0"])/(C["p1"]-C["p0"])));el=math.radians(90-(90-C["ed"])*f)
  horiz=add(mul(n,math.cos(az)),mul(e,math.sin(az)));td=add(mul(u,math.sin(el)),mul(horiz,math.cos(el)));drag=mul(v,-D/(m*sp)) if sp else (0.,0.,0.)
  acc=add(add(grav(r,j2),drag),mul(td,C["T"]/m));v=add(v,mul(acc,dt));r=add(r,mul(v,dt));m=max(C["mf"],m-md*dt);t+=dt
 rr=norm(r);hv=cross(r,v);return {"altitude_m":rr-Re,"speed_m_s":norm(v),"inclination_deg":math.degrees(math.acos(max(-1,min(1,hv[2]/norm(hv)))))}
A=sim(False,False);B=sim(True,False);Cj=sim(False,True);D=sim(True,True)
metrics=["altitude_m","speed_m_s","inclination_deg"];effects={}
for k in metrics:
 effects[k]={"dynamic_frame_at_noJ2":B[k]-A[k],"J2_at_fixed_frame":Cj[k]-A[k],"interaction":D[k]-B[k]-Cj[k]+A[k],"dynamic_frame_at_J2":D[k]-Cj[k],"J2_at_dynamic_frame":D[k]-B[k]}
body={"schema":"CEREBRON_FACTORIAL_ABLATION_V19","design":{"A_fixed_noJ2":A,"B_dynamic_noJ2":B,"C_fixed_J2":Cj,"D_dynamic_J2":D},"effects":effects,"reality_gap":"G02_DYNAMICS_FIDELITY_PARTIAL","epistemic":["TWO_BY_TWO_FACTORIAL_ABLATION","DYNAMIC_FRAME_EFFECT_SEPARATED","J2_EFFECT_SEPARATED","INTERACTION_REPORTED","NUMERICAL_MODEL_ONLY","NO_EXTERNAL_REFERENCE","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
