import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/orbit_insertion_v4.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5;rho0=1.225;H=8500.;g0=9.80665;dt=.1
c={"lat_deg":28.5,"target_alt_m":400e3,"m0":500000.,"mf":60000.,"T":8e6,"Isp":450.,"Cd":.35,"A":20.,"burn":240.,"pitch0":12.,"pitch1":170.}
lat=math.radians(c["lat_deg"]);r=Re;vr=0.;vt=omega*Re*math.cos(lat);m=c["m0"];t=0.;maxq=0.;gl=0.;dl=0.;mdot=c["T"]/(c["Isp"]*g0)
while t<c["burn"] and m>c["mf"]:
 h=max(0.,r-Re);rho=rho0*math.exp(-h/H);v=math.hypot(vr,vt);q=.5*rho*v*v;maxq=max(maxq,q);D=q*c["Cd"]*c["A"]
 f=min(1.,max(0.,(t-c["pitch0"])/(c["pitch1"]-c["pitch0"])));gam=math.radians(90.-80.*f)
 Tr=c["T"]*math.sin(gam);Tt=c["T"]*math.cos(gam)
 Dr=D*vr/v if v else 0.;Dt=D*vt/v if v else 0.;g=mu/r**2
 ar=Tr/m-Dr/m-g+vt*vt/r;at=Tt/m-Dt/m-vr*vt/r
 gl+=g*max(0.,math.sin(gam))*dt;dl+=D/m*dt
 vr+=ar*dt;vt+=at*dt;r=max(Re,r+vr*dt);m=max(c["mf"],m-mdot*dt);t+=dt
h=r-Re;v=math.hypot(vr,vt);energy=.5*v*v-mu/r
if energy<0:
 a=-mu/(2*energy);e=math.sqrt(max(0.,1-(r*vt)**2/(mu*a)));rp=a*(1-e);ra=a*(1+e)
else:a=e=rp=ra=float("nan")
target_r=Re+c["target_alt_m"];vc=math.sqrt(mu/target_r)
criteria={"altitude_band":abs(h-c["target_alt_m"])<=20e3,"radial_speed":abs(vr)<=100.,"tangential_speed":abs(vt-vc)<=150.,"bound_orbit":energy<0,"perigee_above_120km":bool(energy<0 and rp-Re>=120e3)}
inserted=all(criteria.values())
body={"schema":"CEREBRON_ORBIT_INSERTION_V4","config":c,"terminal":{"altitude_m":h,"vr_m_s":vr,"vt_m_s":vt,"speed_m_s":v,"mass_kg":m,"specific_energy_j_kg":energy,"semi_major_axis_m":a,"eccentricity":e,"perigee_alt_m":rp-Re if energy<0 else None,"apogee_alt_m":ra-Re if energy<0 else None,"target_circular_speed_m_s":vc,"max_q_pa":maxq,"gravity_loss_m_s_approx":gl,"drag_loss_m_s":dl},"criteria":criteria,"insertion_pass":inserted,"epistemic":["COUPLED_3DOF_TARGET_CHECK","ROTATING_EARTH_INITIAL_VELOCITY","PRESCRIBED_GUIDANCE","SPHERICAL_EARTH","EXPONENTIAL_ATMOSPHERE","NO_J2","NO_WIND","NO_6DOF","NUMERICAL_CANARY_NOT_FLIGHT_CERTIFICATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
OUT.write_text(json.dumps(body,indent=2,allow_nan=False if energy<0 else True)+"\n");print(json.dumps(body));sys.exit(0)
