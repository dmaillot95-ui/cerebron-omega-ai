import json,hashlib,pathlib
P=pathlib.Path("artifacts/f72_review_packet_v32.json");OUT=pathlib.Path("artifacts/f72_counter_audit_v33.json");OUT.parent.mkdir(exist_ok=True)
body={"schema":"CEREBRON_F72_COUNTER_AUDIT_V33","auditor":"F72_COUNTER_AUDIT","producer":"ASTRION_METRION_CHAIN"}
if not P.exists():
 body.update({"decision":"BLOCKED_PACKET_MISSING","independent_review":False})
else:
 d=json.load(open(P));findings=[]
 if d.get("missing"):findings.append("INCOMPLETE_PACKET")
 if d.get("contradictions"):findings.append("UNRESOLVED_CONTRADICTIONS")
 if d.get("open_gaps"):findings.append("OPEN_PHYSICAL_GAPS")
 if "PACKET_ASSEMBLY_NOT_INDEPENDENT_EVIDENCE" not in d.get("epistemic",[]):findings.append("INDEPENDENCE_DISCLOSURE_MISSING")
 # Counter-audit is logically separate code path, but not an independent organization/experiment.
 ready=d.get("candidate_for_f72_review",False) and not d.get("missing") and not d.get("contradictions")
 body.update({"packet_sha256":d.get("sha256"),"findings":findings,"producer_candidate":d.get("candidate_for_f72_review"),"counter_audit_pass_for_afah_review":ready,"decision":"COUNTER_AUDIT_PASS_TO_AFAH_REVIEW" if ready else "COUNTER_AUDIT_BLOCK","independent_review":False,"independence_class":"SEPARATE_CODE_PATH_SAME_REPOSITORY_AND_EVIDENCE"})
body["hard_limits"]=["NOT_INDEPENDENT_ORGANIZATION","NOT_INDEPENDENT_EXPERIMENT","SAME_UPSTREAM_EVIDENCE","OPEN_G01_G04_G05_PREVENT_PHYSICAL_VALIDATION"]
body["epistemic"]=["COUNTER_AUDIT_NOT_NEW_EVIDENCE","NO_MAJORITY_VOTE","AFAH_MUST_REVIEW_DEPENDENCIES","NO_AUTO_PROMOTION"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
