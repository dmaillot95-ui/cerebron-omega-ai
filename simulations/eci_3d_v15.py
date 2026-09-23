import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/eci_3d_v15.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,k):return tuple(x*k for x in a)
def deriv(s):
 r=s[:3];v=s[3:];rn=norm(r);a=mul(r,-mu/rn**3);return v+a
def rk4(s,dt):
 k1=deriv(s);k2=deriv(add(s,mul(k1,dt/2)));k3=deriv(add(s,mul(k2,dt/2)));k4=deriv(add(s,mul(k3,dt)))
 return tuple(s[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(6))
def elements(s):
 r=s[:3];v=s[3:];rn=norm(r);vn=norm(v);h=cross(r,v);hn=norm(h);inc=math.degrees(math.acos(max(-1,min(1,h[2]/hn))))
 evec=tuple(((vn*vn-mu/rn)*r[i]-dot(r,v)*v[i])/mu for i in range(3));e=norm(evec);E=vn*vn/2-mu/rn;a=-mu/(2*E)
 return {"a_m":a,"e":e,"inclination_deg":inc,"energy":E,"h":hn}
lat=math.radians(28.5);lon=0.;rmag=Re+400e3
# local basis at lon=0: up, east, north
up=(math.cos(lat),0.,math.sin(lat));east=(0.,1.,0.);north=(-math.sin(lat),0.,math.cos(lat))
r=mul(up,rmag);vc=math.sqrt(mu/rmag)
# due-east circular inertial velocity gives inclination ~= latitude
v=mul(east,vc);s=r+v;e0=elements(s);period=2*math.pi*math.sqrt(rmag**3/mu);dt=2.;n=round(period/dt)
for _ in range(n):s=rk4(s,dt)
e1=elements(s)
crit={"inclination":abs(e0["inclination_deg"]-28.5)<1e-10,"eccentricity":e0["e"]<1e-12,"a_drift":abs(e1["a_m"]-e0["a_m"])<1.,"e_drift":abs(e1["e"]-e0["e"])<1e-8,"inclination_drift":abs(e1["inclination_deg"]-e0["inclination_deg"])<1e-9}
body={"schema":"CEREBRON_ECI_3D_V15","reference":{"latitude_deg":28.5,"altitude_m":400e3,"azimuth":"DUE_EAST","period_s":period},"initial_elements":e0,"final_elements":e1,"criteria":crit,"pass":all(crit.values()),"earth_rotation":{"omega_rad_s":omega,"surface_east_speed_at_lat_m_s":omega*Re*math.cos(lat)},"reality_gap":"G02_DYNAMICS_FIDELITY_PARTIAL","epistemic":["ECI_3D_CARTESIAN","TWO_BODY_RK4","ORBITAL_ELEMENTS_3D","EARTH_ROTATION_REPORTED_NOT_PROPAGATED_IN_REFERENCE_ORBIT","NO_J2","NO_ATMOSPHERE","NO_THRUST_IN_REFERENCE_CASE","NO_HARDWARE_VALIDATION","G02_NOT_CLOSED"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if body["pass"] else 15)
