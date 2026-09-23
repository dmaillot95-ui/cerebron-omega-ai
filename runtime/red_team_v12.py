import json,hashlib,pathlib,math
OUT=pathlib.Path("artifacts/red_team_v12.json");OUT.parent.mkdir(exist_ok=True)
tests=[]
def add(i,claim,status,evidence,impact):
 tests.append({"id":i,"claim":claim,"status":status,"evidence":evidence,"impact":impact})
add("RT01","Simulation implies physical validation","REJECT","All V-chain artifacts explicitly disclaim hardware validation","CRITICAL")
add("RT02","Independent code paths imply independent evidence","RED","V10/V11 share constants and physical laws","HIGH")
add("RT03","Guidance search proves global optimum","REJECT","V5/V6 explicitly use finite grid/local refinement","HIGH")
add("RT04","Monte Carlo establishes calibrated reliability","REJECT","V7 uncertainty distributions are assumed, not calibrated","CRITICAL")
add("RT05","Orbital insertion criterion is sufficient for certified mission success","RED","Simplified atmosphere/guidance; no 6DOF/J2/wind/hardware","CRITICAL")
add("RT06","Analytic reference checks are reproducible","PASS","V10 separate implementation plus V11 alternate formulations","MEDIUM")
add("RT07","Failure policy is certified FDIR","REJECT","V8 explicitly policy-level, not flight software","CRITICAL")
add("RT08","S7 can be promoted automatically","REJECT","V10 marks S7 candidate; F72/AFAH remain pending","HIGH")
add("RT09","Current chain is useful as pre-calibration engineering evidence","PASS","Artifacts, SHA, deterministic cases, constraints and dependency audit exist","MEDIUM")
add("RT10","Common-dependency risk is represented","PASS","V11 records shared dependencies and limited independence class","MEDIUM")
counts={s:sum(x["status"]==s for x in tests) for s in ["PASS","OPEN","RED","REJECT"]}
blocking=[x["id"] for x in tests if x["status"] in ("RED","REJECT") and x["impact"] in ("HIGH","CRITICAL")]
decision="BLOCK_PROMOTION" if blocking else "ELIGIBLE_FOR_F72_REVIEW"
body={"schema":"CEREBRON_RED_TEAM_V12","tests":tests,"counts":counts,"blocking_findings":blocking,"decision":decision,"required_actions":["CALIBRATE_UNCERTAINTIES_WITH_EXTERNAL_DATA","ADD_HIGHER_FIDELITY_DYNAMICS","OBTAIN_INDEPENDENT_REFERENCE_OR_EXPERIMENT","KEEP_F72_AFAH_PENDING_UNTIL_BLOCKERS_CLOSED"],"epistemic":["RED_TEAM_REVIEW","STATIC_EVIDENCE_AUDIT","NO_NEW_PHYSICAL_EVIDENCE","NO_CERTIFICATION_CLAIM"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body));raise SystemExit(0)
