import math,json,hashlib,pathlib,sys
OUT=pathlib.Path("artifacts/orbit_target_v3.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;omega=7.2921159e-5;g0=9.80665
cfg={"latitude_deg":28.5,"launch_azimuth_deg":90.0,"target_altitude_m":400e3,"target_eccentricity_max":0.01,"target_inclination_deg":28.5,"mass0_kg":500000.,"dry_payload_kg":60000.,"thrust_n":8e6,"isp_s":450.}
lat=math.radians(cfg["latitude_deg"]);az=math.radians(cfg["launch_azimuth_deg"]);rt=Re+cfg["target_altitude_m"]
earth_surface_speed=omega*Re*math.cos(lat)
east_component=earth_surface_speed
vcirc=math.sqrt(mu/rt)
# Required inertial tangential speed and ideal rocket budget; this is a targeting budget, not propagated ascent.
rotation_credit=east_component*math.sin(az)
required_vehicle_dv=max(0.,vcirc-rotation_credit)
available_dv=cfg["isp_s"]*g0*math.log(cfg["mass0_kg"]/cfg["dry_payload_kg"])
margin=available_dv-required_vehicle_dv
# Minimum prograde inclination for due-east launch in this spherical approximation.
min_inc=abs(cfg["latitude_deg"]);inc_error=abs(cfg["target_inclination_deg"]-min_inc)
eligible=margin>0 and inc_error<1e-9
body={"schema":"CEREBRON_ORBIT_TARGET_V3","config":cfg,"results":{"earth_rotation_credit_m_s":rotation_credit,"target_circular_speed_m_s":vcirc,"required_vehicle_dv_m_s_idealized":required_vehicle_dv,"available_rocket_equation_dv_m_s":available_dv,"idealized_dv_margin_m_s":margin,"minimum_due_east_inclination_deg":min_inc,"inclination_error_deg":inc_error,"target_budget_eligible":eligible},"epistemic":["ROTATING_EARTH_TARGET_BUDGET","SPHERICAL_EARTH","NO_ASCENT_PROPAGATION_COUPLING","NO_GRAVITY_DRAG_STEERING_LOSSES_IN_TARGET_MARGIN","NO_PLANE_CHANGE","NO_J2","NO_6DOF","NOT_ORBIT_INSERTION_PROOF","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));sys.exit(0 if eligible else 11)
