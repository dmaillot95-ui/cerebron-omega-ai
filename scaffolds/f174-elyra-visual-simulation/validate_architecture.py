#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent
a=json.loads((R/"architecture/ELYRA_VISUAL_SIMULATION_V1.json").read_text())
p=json.loads((R/"config/project.json").read_text())
assert a["farm_id"]==174
assert a["identity"]=="ELYRA"
assert p["target_repo_exists"] is True
assert p["target_repo_initialized"] is True
assert p["training_status"]=="NOT_TRAINED"
assert p["visual_simulation_executed"] is False
assert p["physical_test_status"]=="NOT_TESTED"
assert p["dedicated_repo_selftest_run_id"]==36156887593
print("PASS F174 ELYRA dedicated repository initialized; selftest PASS; simulation not executed")
