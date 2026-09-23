import json,hashlib,pathlib
IN=pathlib.Path("artifacts/occ06c_solar_ablation_v30.json");OUT=pathlib.Path("artifacts/frozen_acceptance_v31.json");OUT.parent.mkdir(exist_ok=True)
# Thresholds are frozen BEFORE observing any future V30 result.
thresholds={"position_rms_m":100.0,"position_max_m":500.0,"velocity_rms_m_s":0.10,"velocity_max_m_s":0.50,"required_relative_rms_improvement":0.05}
body={"schema":"CEREBRON_FROZEN_ACCEPTANCE_V31","case":"OCC06C","thresholds":thresholds,"threshold_status":"FROZEN_PRE_RESULT","rationale":{"position":"engineering verification gate, not certification","velocity":"engineering verification gate, not certification","improvement":"solar model must improve both RMS metrics by at least 5%"}}
if not IN.exists():
 body.update({"decision":"THRESHOLDS_FROZEN_AWAITING_V30_EXTERNAL_RESULT","f72":"BLOCKED"})
else:
 d=json.load(open(IN))
 if not d.get("ready"):
  body.update({"decision":"THRESHOLDS_FROZEN_V30_BLOCKED","v30_decision":d.get("decision"),"f72":"BLOCKED"})
 else:
  e=d["earth_only"];s=d["earth_plus_sun"]
  relp=(e["position_rms_m"]-s["position_rms_m"])/e["position_rms_m"] if e["position_rms_m"] else 0
  relv=(e["velocity_rms_m_s"]-s["velocity_rms_m_s"])/e["velocity_rms_m_s"] if e["velocity_rms_m_s"] else 0
  checks={"position_rms":s["position_rms_m"]<=thresholds["position_rms_m"],"position_max":s["position_max_m"]<=thresholds["position_max_m"],"velocity_rms":s["velocity_rms_m_s"]<=thresholds["velocity_rms_m_s"],"velocity_max":s["velocity_max_m_s"]<=thresholds["velocity_max_m_s"],"solar_improves_position":relp>=thresholds["required_relative_rms_improvement"],"solar_improves_velocity":relv>=thresholds["required_relative_rms_improvement"]}
  body.update({"decision":"ACCEPTANCE_PASS_CANDIDATE" if all(checks.values()) else "ACCEPTANCE_FAIL","checks":checks,"relative_improvement":{"position":relp,"velocity":relv},"f72":"REVIEW_REQUIRED" if all(checks.values()) else "BLOCKED"})
body["epistemic"]=["THRESHOLDS_FROZEN_BEFORE_RESULT","PASS_IS_NOT_CERTIFICATION","PASS_DOES_NOT_CLOSE_G01_G04_G05","F72_REQUIRES_INDEPENDENT_REVIEW","AFAH_REMAINS_PENDING"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
