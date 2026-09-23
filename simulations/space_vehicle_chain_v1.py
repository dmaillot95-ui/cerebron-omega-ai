import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/space_vehicle_chain.json");OUT.parent.mkdir(exist_ok=True)
g0=9.80665
cfg={"vehicle":"CANARY-LV1","wet_mass_kg":500000.0,"dry_mass_kg":50000.0,"payload_kg":10000.0,"isp_s":450.0,"thrust_n":8.0e6,"area_m2":20.0,"cd":0.35,"rho_kg_m3":0.02,"velocity_m_s":2500.0,"nose_radius_m":1.5,"allowable_stress_pa":350e6,"axial_area_m2":0.08,"safety_factor":1.5}
prop=cfg["wet_mass_kg"]-cfg["dry_mass_kg"]-cfg["payload_kg"]
final=cfg["dry_mass_kg"]+cfg["payload_kg"]
dv=cfg["isp_s"]*g0*math.log(cfg["wet_mass_kg"]/final)
twr=cfg["thrust_n"]/(cfg["wet_mass_kg"]*g0)
q=.5*cfg["rho_kg_m3"]*cfg["velocity_m_s"]**2
drag=q*cfg["cd"]*cfg["area_m2"]
# Sutton-Graves-like normalized heating indicator, not calibrated heat flux.
heat_indicator=math.sqrt(cfg["rho_kg_m3"]/cfg["nose_radius_m"])*cfg["velocity_m_s"]**3
axial_stress=cfg["thrust_n"]/cfg["axial_area_m2"]
required_allowable=axial_stress*cfg["safety_factor"]
margin=cfg["allowable_stress_pa"]/required_allowable-1
failures=[]
if twr<=1:failures.append("TWR_LE_1")
if margin<0:failures.append("STRUCTURAL_MARGIN_NEGATIVE")
if prop<=0:failures.append("INVALID_MASS_BUDGET")
checks={"mass_closure_kg":cfg["wet_mass_kg"]-(prop+final),"propellant_kg":prop,"delta_v_m_s":dv,"twr":twr,"dynamic_pressure_pa":q,"drag_n":drag,"heating_indicator_uncalibrated":heat_indicator,"axial_stress_pa":axial_stress,"required_allowable_pa":required_allowable,"structural_margin":margin,"failures":failures}
body={"schema":"CEREBRON_SPACE_VEHICLE_CHAIN_V1","config":cfg,"results":checks,"status":"ANALYTIC_CHAIN_PASS" if not failures else "ANALYTIC_CHAIN_FAIL","epistemic":["ANALYTIC_MODEL","HEATING_INDICATOR_NOT_CALIBRATED","NO_TRAJECTORY_INTEGRATION","NO_CFD","NO_FEA","NO_HARDWARE_TEST","NOT_FLIGHT_CERTIFICATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));sys.exit(0 if not failures and abs(checks["mass_closure_kg"])<1e-9 else 8)
