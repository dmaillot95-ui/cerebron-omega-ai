import json,hashlib,pathlib
OUT=pathlib.Path("artifacts/nasa_time_history_gate_v23.json");OUT.parent.mkdir(exist_ok=True)
source={"authority":"NASA NESC","document_id":"NESC-RP-12-00770","report":"NASA/TM-2015-218675 Vol I/II","evidence":"NASA states orbital/atmospheric time histories were stored as CSV with regular simulation time steps and made electronically available.","historical_data_url":"http://nescacademy.nasa.gov/flightsim/index.html","ntrs_volume_i":"https://ntrs.nasa.gov/citations/20150001263","ntrs_volume_ii":"https://ntrs.nasa.gov/citations/20150001264"}
# Fail-closed admission: no copied trajectory values are accepted unless a real external dataset file
# is committed with provenance + SHA. This prevents fabricating NASA vectors from plots/text.
candidate=pathlib.Path("external/nasa_nesc/time_history.csv")
present=candidate.exists()
sha=hashlib.sha256(candidate.read_bytes()).hexdigest() if present else None
body={"schema":"CEREBRON_NASA_TIME_HISTORY_GATE_V23","source":source,"dataset":{"path":str(candidate),"present":present,"sha256":sha},"decision":"READY_FOR_POINTWISE_COMPARISON" if present else "BLOCKED_EXTERNAL_DATASET_NOT_INGESTED","g03_status":"PARTIAL_EXTERNAL_REFERENCE","requirements":["REAL_NASA_TIME_HISTORY_FILE","SOURCE_PROVENANCE","FILE_SHA256","COLUMN_SCHEMA_AND_UNITS","CASE_ID_AND_INITIAL_CONDITIONS","POINTWISE_RESIDUALS"],"epistemic":["NO_SYNTHETIC_NASA_STATE_VECTORS","PLOTS_NOT_DIGITIZED_AS_GROUND_TRUTH","FAIL_CLOSED_EXTERNAL_EVIDENCE","WORKFLOW_DOES_NOT_IMPLY_DATA_AVAILABILITY"]}
body["sha256"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();OUT.write_text(json.dumps(body,indent=2)+"\n");print(json.dumps(body))
