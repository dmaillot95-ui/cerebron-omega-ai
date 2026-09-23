import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/powered_eci_j2_v17.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;J2=1.08262668e-3;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.25
C={"lat_deg":28.5,"lon_deg":-80.6,"az_deg":90.,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"pitch0":12.,"pitch1":170.,"terminal_elev_deg":5.}
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def mul(a,k):return tuple(k*x for x in a)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def gravity_j2(r):
 x,y,z=r;rr=norm(r);z2=z*z;r2=rr*rr;k=-mu/rr**3;f=1.5*J2*(Re/rr)**2
 return (k*x*(1-f*(5*z2/r2-1)),k*y*(1-f*(5*z2/r2-1)),k*z*(1-f*(5*z2/r2-3)))
lat=math.radians(C["lat_deg"]);lon=math.radians(C["lon_deg"]);az=math.radians(C["az_deg"])
up=(math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat));r=mul(up,Re);v=(-omega*r[1],omega*r[0],0.);m=C["m0"];md=C["T"]/(C["Isp"]*g0);t=0.;maxq=0.
while t<C["burn"] and m>C["mf"]:
 rr=norm(r);h=max(0.,rr-Re);u=mul(r,1/rr)
 # Recompute local east/north from instantaneous geocentric position.
 zaxis=(0.,0.,1.);east=cross(zaxis,u);en=norm(east);east=mul(east,1/en) if en>1e-12 else (0.,1.,0.);north=cross(u,east)
 rho=rho0*math.exp(-h/H);speed=norm(v);q=.5*rho*speed*speed;maxq=max(maxq,q);D=q*C["Cd"]*C["A"]
 f=min(1.,max(0.,(t-C["pitch0"])/(C["pitch1"]-C["pitch0"])));elev=math.radians(90-(90-C["terminal_elev_deg"])*f)
 horiz=add(mul(north,math.cos(az)),mul(east,math.sin(az)));tdir=add(mul(u,math.sin(elev)),mul(horiz,math.cos(elev)))
 drag=mul(v,-D/(m*speed)) if speed else (0.,0.,0.);acc=add(add(gravity_j2(r),drag),mul(tdir,C["T"]/m))
 v=add(v,mul(acc,dt));r=add(r,mul(v,dt));m=max(C["mf"],m-md*dt);t+=dt
rr=norm(r);speed=norm(v);E=.5*speed*speed-mu/rr;hv=cross(r,v);hn=norm(hv);inc=math.degrees(math.acos(max(-1,min(1,hv[2]/hn))))
if E<0:
 a=-mu/(2*E);evec=tuple(((speed*speed-mu/rr)*r[i]-dot(r,v)*v[i])/mu for i in range(3));ecc=norm(evec);rp=a*(1-ecc)-Re;ra=a*(1+ecc)-Re
else:a=ecc=rp=ra=None
body={"schema":"CEREBRON_POWERED_ECI_J2_V17","config":C,"terminal":{"altitude_m":rr-Re,"speed_m_s":speed,"mass_kg":m,"inclination_deg":inc,"semi_major_axis_m":a,"eccentricity":ecc,"perigee_alt_m":rp,"apogee_alt_m":ra,"max_q_pa":maxq},"reality_gap":"G02_DYNAMICS_FIDELITY_PARTIAL","epistemic":["DYNAMIC_LOCAL_FRAME","J2_GRAVITY","POWERED_ECI_3D","EARTH_ROTATION_INITIAL_STATE","EXPONENTIAL_ATMOSPHERE","PRESCRIBED_GUIDANCE","NO_WIND","NO_STAGING","NO_6DOF_ATTITUDE","NO_HARDWARE_VALIDATION","G02_NOT_CLOSED"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
