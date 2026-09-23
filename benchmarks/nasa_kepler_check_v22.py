import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/nasa_kepler_check_v22.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14
# Independent NASA/NESC-inspired dynamic check: numerical RK4 vs analytic Kepler circular solution.
r0=6778137.;v0=math.sqrt(mu/r0);period=2*math.pi*math.sqrt(r0**3/mu)
def deriv(s):
 x,y,vx,vy=s;r=math.hypot(x,y);k=-mu/r**3;return (vx,vy,k*x,k*y)
def rk4(s,dt):
 k1=deriv(s);q=tuple(s[i]+dt*k1[i]/2 for i in range(4));k2=deriv(q);q=tuple(s[i]+dt*k2[i]/2 for i in range(4));k3=deriv(q);q=tuple(s[i]+dt*k3[i] for i in range(4));k4=deriv(q)
 return tuple(s[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(4))
dt=1.;steps=round(period/dt);s=(r0,0.,0.,v0)
for _ in range(steps):s=rk4(s,dt)
t=steps*dt;n=math.sqrt(mu/r0**3);ref=(r0*math.cos(n*t),r0*math.sin(n*t),-v0*math.sin(n*t),v0*math.cos(n*t))
pos_err=math.hypot(s[0]-ref[0],s[1]-ref[1]);vel_err=math.hypot(s[2]-ref[2],s[3]-ref[3])
crit={"position_error_lt_1m":pos_err<1.,"velocity_error_lt_1mm_s":vel_err<1e-3}
body={"schema":"CEREBRON_NASA_KEPLER_DYNAMIC_CHECK_V22","source":{"authority":"NASA NESC","document":"Expansion of Check-Cases for 6DOF Simulation","document_id":"NESC-RP-23-01853 / NASA-TM-20240013031 Volume II Part 2","method":"Case 1 spherical-gravity two-body solution provides machine-precision Keplerian reference"},"case":{"radius_m":r0,"circular_speed_m_s":v0,"period_s":period,"dt_s":dt,"steps":steps},"comparison":{"numerical_state":s,"analytic_state":ref,"position_error_m":pos_err,"velocity_error_m_s":vel_err},"criteria":crit,"pass":all(crit.values()),"g02_status":"PARTIAL_EXTERNAL_DYNAMIC_REFERENCE","g03_status":"PARTIAL_EXTERNAL_METHOD_REFERENCE","limits":["OUR_NUMERIC_CASE_NOT_NASA_PUBLISHED_STATE_VECTOR","SAME_TWO_BODY_PHYSICS","NOT_EXPERIMENT","NO_HARDWARE_VALIDATION"],"next":"INGEST_PUBLISHED_NASA_TIME_HISTORY_OR_CHECK_CASE_STATE_VECTOR"}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if body["pass"] else 22)
