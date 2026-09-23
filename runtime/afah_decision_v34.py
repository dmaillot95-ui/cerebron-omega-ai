import json,hashlib,pathlib
P=pathlib.Path("artifacts/f72_review_packet_v32.json");C=pathlib.Path("artifacts/f72_counter_audit_v33.json");OUT=pathlib.Path("artifacts/afah_decision_v34.json");OUT.parent.mkdir(exist_ok=True)
body={"schema":"CEREBRON_AFAH_DECISION_V34","role":"EPISTEMIC_FUSION_NOT_VOTING"}
if not P.exists() or not C.exists():
 body.update({"decision":"OPEN","reason":"REQUIRED_AUDIT_INPUT_MISSING","promotion":False})
else:
 p=json.load(open(P));c=json.load(open(C));gaps=p.get("open_gaps",[]);contr=p.get("contradictions",[])
 evidence_ready=p.get("candidate_for_f72_review",False) and c.get("counter_audit_pass_for_afah_review",False)
 if contr:
  decision="RED";reason="UNRESOLVED_CONTRADICTIONS"
 elif not evidence_ready:
  decision="OPEN";reason="EVIDENCE_CHAIN_INCOMPLETE_OR_BLOCKED"
 elif gaps:
  decision="OPEN";reason="PHYSICAL_VALIDATION_GAPS_REMAIN"
 else:
  decision="VALIDATED";reason="ALL_DECLARED_GATES_CLOSED"
 body.update({"decision":decision,"reason":reason,"promotion":decision=="VALIDATED","f72_packet_sha256":p.get("sha256"),"counter_audit_sha256":c.get("sha256"),"open_gaps":gaps,"contradictions":contr,"independence_class":c.get("independence_class")})
body["allowed_decisions"]=["VALIDATED","RED","OPEN","REJECT"]
body["epistemic"]=["NO_MAJORITY_VOTE","CLAIM_LE_EVIDENCE","OPEN_IS_NOT_FAILURE","VALIDATED_REQUIRES_ALL_DECLARED_GATES_CLOSED","NO_AUTOMATIC_PHYSICAL_CERTIFICATION"]
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
