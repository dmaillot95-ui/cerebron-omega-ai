#!/usr/bin/env python3
import json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
b=json.loads((R/"config/spiralix-universal-bus-v1.json").read_text())
g=json.loads((R/"config/glyph-vector.json").read_text())
a=json.loads((R/"config/spiralix-agora.json").read_text())
f=json.loads((R/"config/spiralix-forum.json").read_text())
br=json.loads((R/"config/burst20-controller-v1.json").read_text())
rr=json.loads((R/"config/real-worker-receipt-schema-v1.json").read_text())
assert b["runtime_changed"] is False and b["language"]=="SPIRALIX-OMEGA" and b["mode"]=="CEREBRON-M"
assert b["counts"]=={"logical_ai":39,"available_ai":38,"slots_per_ai":8,"total_endpoints":312,"required_active_endpoints":304,"prep_only_endpoints":8}
assert len(b["endpoints"])==312 and len({e["endpoint_id"] for e in b["endpoints"]})==312
assert sum(bool(e["spiralix_required"]) for e in b["endpoints"])==304
nu=[e for e in b["endpoints"] if e["ai_id"]=="F162-NU"]; assert len(nu)==8 and all(not e["spiralix_required"] for e in nu)
for x in ["A₀","A₁","A₂","A₃","A₄","A₅","A₆","A₇","AGΩ","FRΩ","B₂₀","MΩ","CΜ"]: assert x in g["glyphs"]
assert a["universal_bus"]["status"]=="MANDATORY" and a["universal_bus"]["reject_missing_envelope"] is True
assert f["universal_bus"]["status"]=="MANDATORY" and f["universal_bus"]["reject_missing_envelope"] is True
assert br["spiralix_bus"]["required"] is True and "spiralix_envelope_sha256" in br["receipt_required"]
assert rr["spiralix"]["required"] is True and "spiralix_envelope_sha256" in rr["required"]
with tempfile.TemporaryDirectory() as td:
    out=Path(td)/"canary.json"
    subprocess.run([sys.executable,str(R/"tools/spiralix_bus.py"),"--self-test-all","--output",str(out)],check=True)
    x=json.loads(out.read_text()); assert x["status"]=="PASS" and x["active_endpoints_tested"]==304 and x["prep_only_endpoints"]==8
print(json.dumps({"status":"PASS","language":"SPIRALIX-OMEGA","mode":"CEREBRON-M","logical_ai":39,"available_ai":38,"active_endpoints":304,"prep_only":8,"agora":"MANDATORY","forum":"MANDATORY","burst20":"MANDATORY"},sort_keys=True))
