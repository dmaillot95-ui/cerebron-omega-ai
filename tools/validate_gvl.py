#!/usr/bin/env python3
import json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/"config/geometric-vector-learning-v1.json").read_text())
hist=json.loads((R/"memory/gvl-learning-history.json").read_text())
lessons=json.loads((R/"memory/gvl-lesson-index.json").read_text())
lesson_schema=json.loads((R/"config/gvl-lesson-capsule-schema-v1.json").read_text())
registry=json.loads((R/"config/gvl-specialization-registry-v2.json").read_text())
benchmark=json.loads((R/"config/gvl-growth-benchmark-v1.json").read_text())
assert cfg["schema"]=="CEREBRON_GEOMETRIC_VECTOR_LEARNING_V2"
assert cfg["runtime_changed"] is False
assert cfg["counts"]=={"logical_ai":39,"available_ai":38,"prep_only_ai":1}
assert registry["schema"]=="CEREBRON_GVL_SPECIALIZATION_REGISTRY_V2"
assert registry["dimension"]==32
assert benchmark["schema"]=="CEREBRON_GVL_GROWTH_BENCHMARK_V1"
assert benchmark["status"]=="FROZEN_MEASUREMENT_CONTRACT"
assert len(benchmark["task_families"])>=6
assert (R/"tools/gvl_lesson_promoter.py").exists()
assert len(registry["ais"])==39
assert sum(1 for x in registry["ais"] if x["available"])==38
assert cfg["vector_space"]["dimension"]==32
assert len(cfg["ais"])==39
assert sum(1 for x in cfg["ais"] if x["available"])==38
assert hist["current_claim"]=="GEOMETRIC_GROWTH_NOT_DEMONSTRATED"
assert lesson_schema["schema"]=="CEREBRON_GVL_LESSON_CAPSULE_SCHEMA_V1"
assert lessons["schema"]=="CEREBRON_GVL_LESSON_INDEX_V1"
assert lessons["dedup_summary"]["merged_redundant"]>=1
assert lessons["dedup_summary"]["promoted_validated"]==0
for item in lessons["lessons"]:
    assert item["promotion_status"] in lesson_schema["promotion_status_values"]
    if item["promotion_status"]=="MERGED_REDUNDANT":
        assert item.get("merged_into")
        assert item.get("novelty_score")==0.0
with tempfile.TemporaryDirectory() as td:
    out=Path(td)/"gvl.json"
    subprocess.run([sys.executable,str(R/"tools/gvl_vector_engine.py"),"--canary","--output",str(out)],check=True)
    x=json.loads(out.read_text())
    assert x["status"]=="PASS"
    assert x["available_ai"]==38
    assert x["vector_dimension"]==32
    assert x["checks"]["all_available_have_vectors"] is True
    assert x["growth"]["geometric_like_claim_allowed"] is False
print(json.dumps({"status":"PASS","available_ai":38,"dimension":32,"geometric_growth_claim":"DENY_PENDING_4_POSITIVE_TRANSFER_CYCLES"},sort_keys=True))
