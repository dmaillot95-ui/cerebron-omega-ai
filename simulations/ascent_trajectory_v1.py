import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/ascent_trajectory.json");OUT.parent.mkdir(exist_ok=True)
g0=9.80665;Re=6378137.;rho0=1.225;H=8500.;dt=.25
cfg={"mass0_kg":500000.,"dry_plus_payload_kg":60000.,"thrust_n":8e6,"isp_s":450.,"cd":0.35,"area_m2":20.,"burn_s":240.,"pitch_start_s":12.,"pitch_end_s":170.}
m=cfg["mass0_kg"];h=0.;v=0.;x=0.;t=0.;maxq={"q_pa":0.,"t_s":0.,"h_m":0.,"v_m_s":0.};peak_g=0.;samples=[]
mdot=cfg["thrust_n"]/(cfg["isp_s"]*g0)
while t<=cfg["burn_s"] and m>cfg["dry_plus_payload_kg"]:
 rho=rho0*math.exp(-h/H);q=.5*rho*v*v;drag=q*cfg["cd"]*cfg["area_m2"]
 if q>maxq["q_pa"]:maxq={"q_pa":q,"t_s":t,"h_m":h,"v_m_s":v}
 # simplified pitch program: 90deg vertical -> 10deg above horizon
 f=min(1,max(0,(t-cfg["pitch_start_s"])/(cfg["pitch_end_s"]-cfg["pitch_start_s"])))
 ang=math.radians(90-80*f)
 g=g0*(Re/(Re+h))**2
 thrust=cfg["thrust_n"]; ax=(thrust*math.cos(ang)-drag)/m; az=thrust*math.sin(ang)/m-g
 a=math.hypot(ax,az);peak_g=max(peak_g,a/g0)
 vx=v*math.cos(ang)+ax*dt; vz=v*math.sin(ang)+az*dt
 # scalarized guidance approximation retained explicitly as model limitation
 v=max(0,math.hypot(vx,vz));x+=max(0,vx)*dt;h=max(0,h+vz*dt);m=max(cfg["dry_plus_payload_kg"],m-mdot*dt)
 if int(t)%20==0 and abs(t-round(t))<dt/2:samples.append({"t_s":round(t,2),"h_m":h,"v_m_s":v,"mass_kg":m,"q_pa":q})
 t+=dt
body={"schema":"CEREBRON_ASCENT_TRAJECTORY_V1","config":cfg,"results":{"end_t_s":t,"altitude_m":h,"speed_m_s":v,"downrange_m":x,"mass_kg":m,"max_q":maxq,"peak_proper_accel_g_approx":peak_g},"samples":samples,"epistemic":["2D_GUIDANCE_APPROXIMATION","EXPONENTIAL_ATMOSPHERE","CONSTANT_THRUST_ISP_CD","NO_EARTH_ROTATION","NO_WIND","NO_6DOF","NO_CFD","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));sys.exit(0 if maxq["q_pa"]>0 and h>0 and m>=cfg["dry_plus_payload_kg"] else 9)
