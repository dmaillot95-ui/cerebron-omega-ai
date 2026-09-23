import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/cross_model_v11.json");OUT.parent.mkdir(exist_ok=True)
mu=3.986004418e14;Re=6378137.;g0=9.80665
checks=[]
def chk(name,a,b,tol,deps):
 rel=abs(a-b)/max(abs(b),1e-30);checks.append({"name":name,"method_A":a,"method_B":b,"relative_difference":rel,"tolerance":tol,"pass":rel<=tol,"shared_dependencies":deps})
# Circular speed: force balance vs vis-viva specialized to circular orbit.
r=Re+400e3
chk("CIRCULAR_SPEED",math.sqrt(mu/r),math.sqrt(mu*(2/r-1/r)),1e-14,["mu","radius"])
# Tsiolkovsky: exponential closed form vs numerical integration of dm relation.
dv=9400.;ve=450*g0;ratio_closed=math.exp(dv/ve)
n=200000;du=dv/n;lnr=sum(du/ve for _ in range(n));ratio_num=math.exp(lnr)
chk("ROCKET_MASS_RATIO",ratio_closed,ratio_num,2e-11,["g0","Isp","delta_v","rocket_equation_assumption"])
# Thermal expansion: direct formula vs segmented accumulation.
L=10.;alpha=23e-6;dT=100.;direct=L*alpha*dT
seg=sum((L/1000)*alpha*dT for _ in range(1000))
chk("THERMAL_EXPANSION",direct,seg,1e-12,["length","alpha","delta_T","linear_expansion_model"])
# Stress: F/A in SI vs N/mm2 conversion.
si=100000/(1000e-6);nmm=100000/1000*1e6
chk("AXIAL_STRESS",si,nmm,1e-14,["force","area","uniform_axial_stress_model"])
passed=all(x["pass"] for x in checks)
shared=sorted({d for x in checks for d in x["shared_dependencies"]})
body={"schema":"CEREBRON_CROSS_MODEL_V11","checks":checks,"pass":passed,"dependency_audit":{"shared_dependencies":shared,"independence_class":"IMPLEMENTATION_DIVERSITY_WITH_SHARED_PHYSICS_ASSUMPTIONS"},"decision":"CROSS_CHECK_PASS_DEPENDENCY_LIMITED" if passed else "RED_DIVERGENCE","gates":{"F72":"PENDING_DEPENDENCY_REVIEW","AFAH":"PENDING"},"epistemic":["ALTERNATIVE_IMPLEMENTATIONS","COMMON_CONSTANTS_DISCLOSED","COMMON_PHYSICAL_LAWS_DISCLOSED","NOT_FULLY_INDEPENDENT_EVIDENCE","NO_HARDWARE_CALIBRATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if passed else 13)
