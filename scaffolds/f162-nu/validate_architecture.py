import json,pathlib
R=pathlib.Path(__file__).resolve().parent;N="NU"
req=[R/"architecture"/f"{N}_ARCHITECTURE_V1.json",R/"memory"/f"{N}_MEMORY_CONTRACT_V1.json",R/"benchmarks"/f"{N}_BENCHMARK_V1.json",R/"config"/"model-candidates.json",R/"training"/f"{N}_TRAINING_READINESS_GATES_V1.json"]
missing=[str(p.relative_to(R)) for p in req if not p.exists()]
if missing:print(json.dumps({"status":"FAIL","missing":missing}));raise SystemExit(1)
a=json.loads((R/"architecture"/f"{N}_ARCHITECTURE_V1.json").read_text());b=json.loads((R/"benchmarks"/f"{N}_BENCHMARK_V1.json").read_text());m=json.loads((R/"memory"/f"{N}_MEMORY_CONTRACT_V1.json").read_text())
assert a["farm_id"]==162;assert a["role_id"]=="NULL_MODEL_CHALLENGER";assert a["runtime_changed"] is False;assert a["campaign"]["passes"]==10;assert b["m6_rule"]=="M6_NEVER_IN_TRAIN";assert "M6_COLD_BENCHMARK" in m["training_forbidden"]
print(json.dumps({"status":"PASS","name":N,"farm_id":162,"runtime_changed":False,"m6_guard":True,"passes":10,"deployment":"REPOSITORY_MISSING"}))
