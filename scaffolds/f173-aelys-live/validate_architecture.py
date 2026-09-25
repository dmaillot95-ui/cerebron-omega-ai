#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent
a=json.loads((R/"architecture/AELYS_LIVE_ARCHITECTURE_V1.json").read_text())
p=json.loads((R/"config/project.json").read_text())
assert a["farm_id"]==173
assert a["identity"]=="AELYS"
assert p["target_repo_exists"] is True
assert p["target_repo_initialized"] is True
assert p["training_status"]=="NOT_TRAINED"
assert p["dedicated_repo_selftest_run_id"]==36162643249
assert p["master_plugin_bus_status"]=="DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED"
assert p["unified_plugin_bus_guard_run_id"]==36156083228
assert p["status"]=="LOCAL_LIVE_LOOP_CANARY_PASS_EXTERNAL_RUNTIME_UNQUALIFIED"
assert p["local_live_loop_canary"]["run_id"]==36162553038
assert p["local_live_loop_canary"]["result_sha256"]=="a860b0f9becd088496c6580b6febd608af0964e73c10b6ac04452048326fb3a4"
assert p["local_live_loop_canary"]["external_calls_executed"] is False
assert p["local_live_loop_canary"]["production_live_claimed"] is False
assert p["external_runtime_status"]=="UNQUALIFIED"
assert p["live_production_status"]=="NOT_DEPLOYED"
assert p["paid_provider_auto_activation"] is False
print("PASS F173 AELYS local live-loop canary; external runtime unqualified")
