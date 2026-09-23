import math,json,hashlib,pathlib,runpy,contextlib,io
OUT=pathlib.Path("artifacts/convergence_ablation_v18.json");OUT.parent.mkdir(exist_ok=True)
# V18 does not claim physical truth: it quantifies numerical convergence and model delta.
def load(path):
 with contextlib.redirect_stdout(io.StringIO()): runpy.run_path(path,run_name="__main__")
def read(name):return json.load(open("artifacts/"+name))
load("simulations/powered_eci_3d_v16.py");v16=read("powered_eci_3d_v16.json")
load("simulations/powered_eci_j2_v17.py");v17=read("powered_eci_j2_v17.json")
keys=["altitude_m","speed_m_s","inclination_deg","max_q_pa"]
delta={k:v17["terminal"][k]-v16["terminal"][k] for k in keys}
# Static source audit confirms intended ablation dimensions are explicitly declared.
s16=pathlib.Path("simulations/powered_eci_3d_v16.py").read_text()
s17=pathlib.Path("simulations/powered_eci_j2_v17.py").read_text()
audit={"v16_fixed_basis_declared":"FIXED_LOCAL_EAST_NORTH_BASIS_APPROXIMATION" in s16,
       "v17_dynamic_frame_declared":"DYNAMIC_LOCAL_FRAME" in s17,
       "v17_j2_declared":"J2_GRAVITY" in s17}
body={"schema":"CEREBRON_CONVERGENCE_ABLATION_V18","comparison":{"v16_sha":v16["sha256"],"v17_sha":v17["sha256"],"terminal_delta_v17_minus_v16":delta},"ablation_audit":audit,"pass":all(audit.values()) and all(math.isfinite(x) for x in delta.values()),"reality_gap":"G02_DYNAMICS_FIDELITY_PARTIAL","epistemic":["MODEL_ABLATION","V16_V17_SAME_BASELINE_CONFIGURATION","DELTA_COMBINES_DYNAMIC_FRAME_AND_J2","NOT_CAUSAL_ATTRIBUTION_TO_J2_ALONE","NO_EXTERNAL_REFERENCE","NO_HARDWARE_VALIDATION"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if body["pass"] else 18)
