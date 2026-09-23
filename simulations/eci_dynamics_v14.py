import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/eci_dynamics_v14.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5
def accel(s):
 x,y,vx,vy=s;r=math.hypot(x,y);k=-mu/r**3;return (k*x,k*y)
def rk4(s,dt):
 def f(q):
  ax,ay=accel(q);return (q[2],q[3],ax,ay)
 k1=f(s);q2=tuple(s[i]+dt*k1[i]/2 for i in range(4));k2=f(q2)
 q3=tuple(s[i]+dt*k2[i]/2 for i in range(4));k3=f(q3)
 q4=tuple(s[i]+dt*k3[i] for i in range(4));k4=f(q4)
 return tuple(s[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(4))
def invariants(s):
 x,y,vx,vy=s;r=math.hypot(x,y);v2=vx*vx+vy*vy
 return .5*v2-mu/r,x*vy-y*vx
r0=Re+400e3;vc=math.sqrt(mu/r0);period=2*math.pi*math.sqrt(r0**3/mu);s=(r0,0.,0.,vc);e0,h0=invariants(s)
dt=2.;n=round(period/dt)
max_alt_err=0.
for _ in range(n):
 s=rk4(s,dt);max_alt_err=max(max_alt_err,abs(math.hypot(s[0],s[1])-r0))
e1,h1=invariants(s);energy_rel=abs((e1-e0)/e0);h_rel=abs((h1-h0)/h0);closure=math.hypot(s[0]-r0,s[1])
# Rotation sanity: equatorial inertial surface speed.
rotation_speed=omega*Re
criteria={"orbit_radius_error_m":max_alt_err<1.0,"energy_conservation":energy_rel<1e-10,"angular_momentum_conservation":h_rel<1e-10,"one_orbit_closure_m":closure<20000.,"rotation_reference":abs(rotation_speed-465.1010849)<0.01}
passed=all(criteria.values())
body={"schema":"CEREBRON_ECI_DYNAMICS_V14","method":"PLANAR_ECI_TWO_BODY_RK4","reference_case":{"altitude_m":400e3,"circular_speed_m_s":vc,"period_s":period,"dt_s":dt,"steps":n},"results":{"max_radius_error_m":max_alt_err,"energy_relative_drift":energy_rel,"angular_momentum_relative_drift":h_rel,"one_orbit_closure_m":closure,"equatorial_rotation_speed_m_s":rotation_speed},"criteria":criteria,"pass":passed,"reality_gap":"G02_DYNAMICS_FIDELITY_PARTIAL","epistemic":["EARTH_CENTERED_INERTIAL","RK4_NUMERICAL_PROPAGATION","TWO_BODY_REFERENCE","EARTH_ROTATION_REFERENCE","NO_J2","NO_ATMOSPHERE_IN_REFERENCE_CASE","NO_3D_INCLINATION","NO_HARDWARE_VALIDATION","G02_NOT_CLOSED"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if passed else 14)
