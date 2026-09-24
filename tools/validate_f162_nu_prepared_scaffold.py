#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"scaffolds/f162-nu"
assert R.exists()
a=json.loads((R/"architecture/NU_ARCHITECTURE_V1.json").read_text())
p=json.loads((R/"config/project.json").read_text())
assert a["farm_id"]==162
assert a["name"]=="NU"
assert a["role_id"]=="NULL_MODEL_CHALLENGER"
assert a["runtime_changed"] is False
assert p["status"]=="PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING"
subprocess.run([sys.executable,"validate_architecture.py"],cwd=R,check=True)
subprocess.run([sys.executable,"-m","unittest","tests/test_scaffold.py","-v"],cwd=R,check=True)
print(json.dumps({
  "status":"PASS",
  "farm_id":162,
  "name":"NU",
  "role_id":"NULL_MODEL_CHALLENGER",
  "repository_exists":False,
  "deployment_status":"PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING"
},sort_keys=True))
