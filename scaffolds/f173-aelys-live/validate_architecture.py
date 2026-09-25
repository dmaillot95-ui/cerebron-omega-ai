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
assert p["dedicated_repo_selftest_run_id"]==36155830169
assert p["master_plugin_bus_status"]=="DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED"
assert p["unified_plugin_bus_guard_run_id"]==36156083228
assert p["live_production_status"]=="NOT_DEPLOYED"
assert p["paid_provider_auto_activation"] is False
print("PASS F173 AELYS LIVE prepared scaffold")
