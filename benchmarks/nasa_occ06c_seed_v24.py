import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/nasa_occ06c_seed_v24.json");OUT.parent.mkdir(exist_ok=True)
# NASA/NESC 2015 OCC06C public initial conditions, independently sourced from NESC Academy.
r=(-4292653.41,955168.47,5139356.57);v=(109.649663,-7527.726490,1484.521489)
mu=3.986004418e14
dot=lambda a,b:sum(x*y for x,y in zip(a,b))
cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
norm=lambda a:math.sqrt(dot(a,a))
rn=norm(r);vn=norm(v);h=cross(r,v);hn=norm(h);E=vn*vn/2-mu/rn
evec=tuple(((vn*vn-mu/rn)*r[i]-dot(r,v)*v[i])/mu for i in range(3));ecc=norm(evec);a=-mu/(2*E);inc=math.degrees(math.acos(h[2]/hn))
body={"schema":"CEREBRON_NASA_OCC06C_SEED_V24","source":{"authority":"NASA NESC Academy","case":"Orbital Check Case 06C","url":"https://nescacademy.nasa.gov/flightsim/2015/orbital/occ06c","duration_s":28800,"gravity":"Inverse Square","sun_perturbation":True,"moon_perturbation":False},"published_initial_state":{"J2000_position_m":r,"J2000_velocity_m_s":v},"derived_two_body_diagnostics":{"radius_m":rn,"speed_m_s":vn,"specific_energy_J_kg":E,"semi_major_axis_m":a,"eccentricity":ecc,"inclination_deg":inc},"decision":"EXTERNAL_INITIAL_STATE_INGESTED","g03_status":"PARTIAL_EXTERNAL_INITIAL_CONDITION","limits":["NO_RAW_TIME_HISTORY_INGESTED_YET","SUN_PERTURBATION_NOT_REPRODUCED","TWO_BODY_DIAGNOSTICS_ONLY","NOT_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
