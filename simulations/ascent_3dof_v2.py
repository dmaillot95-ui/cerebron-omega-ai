import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/ascent_3dof.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;rho0=1.225;H=8500.;g0=9.80665;dt=.1
c={"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"pitch0":12.,"pitch1":170.}
r=Re;vr=0.;vt=0.;m=c["m0"];t=0.;grav_loss=0.;drag_loss=0.;maxq={"q":0.,"t":0.,"h":0.};peakg=0.
mdot=c["T"]/(c["Isp"]*g0)
while t<c["burn"] and m>c["mf"]:
 h=max(0.,r-Re);rho=rho0*math.exp(-h/H);v=math.hypot(vr,vt);q=.5*rho*v*v
 if q>maxq["q"]:maxq={"q":q,"t":t,"h":h}
 D=q*c["Cd"]*c["A"];f=min(1.,max(0.,(t-c["pitch0"])/(c["pitch1"]-c["pitch0"])));gamma=math.radians(90.-80.*f)
 Tr=c["T"]*math.sin(gamma);Tt=c["T"]*math.cos(gamma)
 if v>1e-9:Dr=D*vr/v;Dt=D*vt/v
 else:Dr=Dt=0.
 ar=Tr/m-Dr/m-mu/r**2+vt**2/r
 at=Tt/m-Dt/m-vr*vt/r
 grav_loss+=(mu/r**2)*max(0.,math.sin(gamma))*dt;drag_loss+=(D/m)*dt
 peakg=max(peakg,math.hypot(Tr-Dr,Tt-Dt)/m/g0)
 vr+=ar*dt;vt+=at*dt;r=max(Re,r+vr*dt);m=max(c["mf"],m-mdot*dt);t+=dt
v=math.hypot(vr,vt);vcirc=math.sqrt(mu/r);specific=.5*v*v-mu/r
body={"schema":"CEREBRON_ASCENT_3DOF_V2","config":c,"results":{"t_s":t,"altitude_m":r-Re,"vr_m_s":vr,"vt_m_s":vt,"speed_m_s":v,"local_circular_speed_m_s":vcirc,"specific_orbital_energy_j_kg":specific,"mass_kg":m,"max_q":maxq,"gravity_loss_m_s_approx":grav_loss,"drag_loss_m_s":drag_loss,"peak_proper_accel_g":peakg},"epistemic":["3DOF_POINT_MASS","SPHERICAL_NONROTATING_EARTH","PRESCRIBED_THRUST_ANGLE","EXPONENTIAL_ATMOSPHERE","NO_LIFT","NO_WIND","NO_6DOF_ATTITUDE","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));sys.exit(0 if r>Re and maxq["q"]>0 and drag_loss>=0 and grav_loss>=0 else 10)
