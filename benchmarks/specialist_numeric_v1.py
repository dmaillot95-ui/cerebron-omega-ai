import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/specialist_numeric_benchmark.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14; Re=6378137.0; g0=9.80665
cases=[]
# Orbital circular speed, 400 km
r=Re+400e3; v=math.sqrt(mu/r); ref=7672.598648385013
cases.append(("ORB_CIRC_400KM",v,ref,"m/s",1e-9))
# Hohmann transfer LEO 400 km to GEO radius 42164 km: total impulsive delta-v
r1=r;r2=42164e3
dv1=math.sqrt(mu/r1)*(math.sqrt(2*r2/(r1+r2))-1)
dv2=math.sqrt(mu/r2)*(1-math.sqrt(2*r1/(r1+r2)))
dv=dv1+dv2; refdv=3854.00957873035
cases.append(("HOHMANN_400KM_GEO",dv,refdv,"m/s",1e-9))
# Rocket equation mass ratio for dv=9400 m/s, Isp=450 s
mr=math.exp(9400/(450*g0)); refmr=8.42165808152076
cases.append(("TSIOLKOVSKY_MR",mr,refmr,"ratio",1e-9))
# Thermal expansion: 10 m Al-like member, alpha 23e-6/K, dT=100K
dl=10*23e-6*100; refdl=.023
cases.append(("THERMAL_EXPANSION",dl,refdl,"m",1e-12))
# Axial stress: 100 kN / 1000 mm2
stress=100000/(1000e-6); refstress=100e6
cases.append(("AXIAL_STRESS",stress,refstress,"Pa",1e-12))
rows=[]
for cid,val,ref,unit,tol in cases:
 rel=abs(val-ref)/(abs(ref) or 1); rows.append({"id":cid,"value":val,"reference":ref,"unit":unit,"relative_error":rel,"pass":rel<=tol})
score=sum(x["pass"] for x in rows)/len(rows)
body={"schema":"CEREBRON_SPECIALIST_NUMERIC_BENCHMARK_V1","cases":rows,"score":score,"limits":["ANALYTIC_REFERENCE_CASES","NO_CFD_FEA","NO_HARDWARE_VALIDATION","NO_MODEL_INTELLIGENCE_CLAIM"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));sys.exit(0 if score==1 else 7)
