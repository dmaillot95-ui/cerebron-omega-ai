#!/usr/bin/env python3
import json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/"config/geometric-vector-learning-v1.json").read_text())
hist=json.loads((R/"memory/gvl-learning-history.json").read_text())
assert cfg["schema"]=="CEREBRON_GEOMETRIC_VECTOR_LEARNING_V1"
assert cfg["runtime_changed"] is False
assert cfg["counts"]=={"logical_ai":39,"available_ai":38,"prep_only_ai":1}
assert cfg["vector_space"]["dimension"]==16
assert len(cfg["ais"])==39
assert sum(1 for x in cfg["ais"] if x["available"])==38
assert hist["current_claim"]=="GEOMETRIC_GROWTH_NOT_DEMONSTRATED"
with tempfile.TemporaryDirectory() as td:
    out=Path(td)/"gvl.json"
    subprocess.run([sys.executable,str(R/"tools/gvl_vector_engine.py"),"--canary","--output",str(out)],check=True)
    x=json.loads(out.read_text())
    assert x["status"]=="PASS"
    assert x["available_ai"]==38
    assert x["vector_dimension"]==16
    assert x["checks"]["all_available_have_vectors"] is True
    assert x["growth"]["geometric_like_claim_allowed"] is False
print(json.dumps({"status":"PASS","available_ai":38,"dimension":16,"geometric_growth_claim":"DENY_PENDING_4_POSITIVE_TRANSFER_CYCLES"},sort_keys=True))
