import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/cycle_close_v20.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.
def prop(dt):
 r0=Re+400e3;vc=math.sqrt(mu/r0);s=[r0,0.,0.,vc];T=2*math.pi*math.sqrt(r0**3/mu);n=round(T/dt)
 def f(q):
  x,y,vx,vy=q;r=math.hypot(x,y);k=-mu/r**3;return [vx,vy,k*x,k*y]
 for _ in range(n):
  k1=f(s);q=[s[i]+dt*k1[i]/2 for i in range(4)];k2=f(q);q=[s[i]+dt*k2[i]/2 for i in range(4)];k3=f(q);q=[s[i]+dt*k3[i] for i in range(4)];k4=f(q)
  s=[s[i]+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6 for i in range(4)]
 return {"dt":dt,"radius_error_m":abs(math.hypot(s[0],s[1])-r0),"closure_m":math.hypot(s[0]-r0,s[1])}
conv=[prop(x) for x in [8.,4.,2.,1.,.5]]
trend=conv[-1]["radius_error_m"]<=conv[0]["radius_error_m"] and conv[-1]["closure_m"]<=conv[0]["closure_m"]
artifacts=["space_vehicle_chain.json","ascent_3dof.json","orbit_target_v3.json","orbit_insertion_v4.json","guidance_search_v5.json","guidance_constrained_v6.json","robustness_mc_v7.json","failure_injection_v8.json","evidence_pack_v9.json","independent_reproduction_v10.json","cross_model_v11.json","red_team_v12.json","reality_gap_v13.json","eci_dynamics_v14.json","eci_3d_v15.json","powered_eci_3d_v16.json","powered_eci_j2_v17.json","convergence_ablation_v18.json","factorial_ablation_v19.json"]
present=[x for x in artifacts if (pathlib.Path("artifacts")/x).exists()]
body={"schema":"CEREBRON_CYCLE_CLOSE_V20","dt_convergence":conv,"convergence_trend_pass":trend,"evidence_inventory":{"expected":19,"present":len(present),"missing":[x for x in artifacts if x not in present]},"maturity":{"analytic_reference_core":"S7_CANDIDATE_REPRODUCED","trajectory_models":"S5_ARTIFACT_PLUS_SHA","calibration":"BELOW_S8","F72":"BLOCKED","AFAH":"BLOCKED"},"gaps":{"G01_uncertainty_calibration":"OPEN","G02_dynamics_fidelity":"PARTIAL","G03_independent_external_reference":"OPEN","G04_hardware_evidence":"OPEN","G05_FDIR_validation":"OPEN","G06_optimizer_confidence":"OPEN"},"decision":"CYCLE_1_CLOSED_ENGINEERING_PRECALIBRATION","next_cycle":"EXTERNAL_REFERENCE_AND_CALIBRATION","epistemic":["NUMERICAL_CONVERGENCE_NOT_PHYSICAL_VALIDATION","S7_CANDIDATE_ONLY_FOR_REPRODUCED_ANALYTIC_CORE","NO_S8_WITHOUT_CALIBRATION","NO_F72_PROMOTION_WITH_OPEN_P0_GAPS"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
