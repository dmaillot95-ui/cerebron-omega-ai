import math,json,hashlib,pathlib
OUT=pathlib.Path("artifacts/independent_reproduction_v10.json");OUT.parent.mkdir(exist_ok=True)
# Independent analytic implementation: no import from V1-V9.
mu=3.986004418e14;Re=6378137.;g0=9.80665
cases=[]
def add(name,a,b,rtol):
 rel=abs(a-b)/max(abs(b),1e-30);cases.append({"case":name,"implementation_b":a,"reference":b,"rtol":rtol,"relative_error":rel,"pass":rel<=rtol})
# Published/analytic constants used as fixed reference cases for reproducibility, not hardware calibration.
r=Re+400e3;add("LEO_400KM_CIRCULAR_SPEED",math.sqrt(mu/r),7668.558175407055,1e-10)
r1=Re+400e3;r2=42164e3
v1=math.sqrt(mu/r1);v2=math.sqrt(mu/r2);a=(r1+r2)/2
dv1=math.sqrt(mu*(2/r1-1/a))-v1;dv2=v2-math.sqrt(mu*(2/r2-1/a));add("HOHMANN_LEO_GEO_TOTAL_DV",dv1+dv2,3854.033557470784,1e-9)
add("TSIOLKOVSKY_MASS_RATIO_9400_450",math.exp(9400/(450*g0)),8.40871508149324,1e-9)
add("THERMAL_EXPANSION_10M_AL_100K",10*23e-6*100,.023,1e-12)
add("AXIAL_STRESS_100KN_1000MM2",100000/(1000e-6),100e6,1e-12)
passed=all(x["pass"] for x in cases)
body={"schema":"CEREBRON_INDEPENDENT_REPRODUCTION_V10","method":"SEPARATE_ANALYTIC_IMPLEMENTATION","cases":cases,"pass":passed,"maturity_candidate":"S7_REPRODUCED" if passed else "S5_ARTIFACT_PLUS_SHA","gates":{"F72":"PENDING","AFAH":"PENDING"},"epistemic":["INDEPENDENT_CODE_PATH","ANALYTIC_REFERENCE_CASES","NOT_INDEPENDENT_EXPERIMENT","NOT_HARDWARE_CALIBRATION","S7_CANDIDATE_NOT_AUTOMATIC_PROMOTION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if passed else 12)
