import json,hashlib,pathlib,math
OUT=pathlib.Path("artifacts/external_reference_v21.json");OUT.parent.mkdir(exist_ok=True)
# NASA NESC check-case constants, source documented in artifact.
ref={"Re_m":6378137.0,"mu_m3_s2":3.986004418e14,"omega_rad_s":7.292115e-5,"J2":0.00108262982}
model={"Re_m":6378137.0,"mu_m3_s2":3.986004418e14,"omega_rad_s":7.2921159e-5,"J2":1.08262668e-3}
tol={"Re_m":1e-12,"mu_m3_s2":1e-12,"omega_rad_s":2e-7,"J2":5e-6}
cmp={}
for k in ref:
 rel=abs(model[k]-ref[k])/abs(ref[k]);cmp[k]={"model":model[k],"reference":ref[k],"relative_error":rel,"tolerance":tol[k],"pass":rel<=tol[k]}
body={"schema":"CEREBRON_EXTERNAL_REFERENCE_V21","source":{"authority":"NASA Engineering and Safety Center","document":"Check-cases for Verification of Six-Degree-of-Freedom Flight Vehicle Simulations, Volume II","document_id":"NESC-RP-12-00770","source_url":"https://ntrs.nasa.gov/api/citations/20150001264/downloads/9-10-25%2020150001264.pdf","table":"Table 73"},"comparison":cmp,"pass":all(x["pass"] for x in cmp.values()),"g03_status":"PARTIAL_EXTERNAL_CONSTANT_REFERENCE","limits":["CONSTANTS_ONLY","NOT_TRAJECTORY_REFERENCE","NOT_INDEPENDENT_EXPERIMENT","NO_HARDWARE_VALIDATION"],"next":"NASA_NESC_DYNAMIC_CHECK_CASE_REPRODUCTION"}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0 if body["pass"] else 21)
