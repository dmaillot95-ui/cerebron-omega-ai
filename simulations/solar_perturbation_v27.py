import math,json,hashlib,pathlib,csv
OUT=pathlib.Path("artifacts/solar_perturbation_v27.json");OUT.parent.mkdir(exist_ok=True)
muE=3.986004418e14;muS=1.32712440018e20;AU=149597870700.;DATA=pathlib.Path("external/nasa_nesc/occ06c_time_history.csv")
def norm(a):return math.sqrt(sum(x*x for x in a))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,k):return tuple(k*x for x in a)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def solar_accel(r,rs):
 d=sub(rs,r);dn=norm(d);sn=norm(rs)
 return sub(mul(d,muS/dn**3),mul(rs,muS/sn**3))
# Order-of-magnitude canary at a representative LEO state. Sun fixed at +X is NOT an ephemeris.
r=(-4292653.41,955168.47,5139356.57);rs=(AU,0.,0.);a=solar_accel(r,rs)
body={"schema":"CEREBRON_SOLAR_PERTURBATION_V27","model":"THIRD_BODY_DIFFERENTIAL_ACCELERATION","representative_state_m":r,"sun_placeholder_m":rs,"solar_acceleration_m_s2":a,"solar_acceleration_norm_m_s2":norm(a),"dataset_present":DATA.exists(),"decision":"MODEL_COMPONENT_READY_DATA_COMPARISON_PENDING" if not DATA.exists() else "READY_FOR_SOLAR_ABLATION_WITH_EPHEMERIS_REQUIRED","g02_status":"PARTIAL","g03_status":"PARTIAL","requirements":["REAL_SOLAR_EPHEMERIS_FOR_OCC06C_EPOCH","RAW_NASA_OCC06C_TIME_HISTORY","FRAME_AND_TIME_SCALE_ALIGNMENT"],"epistemic":["THIRD_BODY_EQUATION_IMPLEMENTED","FIXED_SUN_VECTOR_CANARY_ONLY","NOT_NASA_EPHEMERIS","NO_POINTWISE_VALIDATION_YET","NO_PROMOTION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
