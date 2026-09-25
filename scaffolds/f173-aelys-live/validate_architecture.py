#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent
a=json.loads((R/"architecture/AELYS_LIVE_ARCHITECTURE_V1.json").read_text())
p=json.loads((R/"config/project.json").read_text())
assert a["farm_id"]==173
assert a["identity"]=="AELYS"
assert p["target_repo_exists"] is True
assert p["target_repo_initialized"] is False
assert p["training_status"]=="NOT_TRAINED"
assert p["live_production_status"]=="NOT_DEPLOYED"
assert p["paid_provider_auto_activation"] is False
print("PASS F173 AELYS LIVE prepared scaffold")
