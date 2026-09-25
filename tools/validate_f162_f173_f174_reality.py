#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
farms=json.loads((ROOT/"config/farms.json").read_text())
bootstrap=json.loads((ROOT/"config/farm-bootstrap-manifest-f162-f174.json").read_text())
assert bootstrap["schema"]=="CEREBRON_MISSING_REPO_BOOTSTRAP_V1"
assert {t["farm_id"] for t in bootstrap["targets"]}=={162,174}
for target in bootstrap["targets"]:
    for item in target["files"]:
        p=ROOT/item["path"]
        assert p.exists(), f"missing bootstrap source {p}"
        actual=subprocess.check_output(["git","hash-object",str(p)],cwd=ROOT,text=True).strip()
        assert actual==item["blob_sha"], (item["path"], actual, item["blob_sha"])

by_id={f["id"]:f for f in farms["farms"]}
assert farms["max_farms"]==174
assert farms["policy"]["farm_cap"]==174
assert farms["policy"]["no_farm_above_174"] is True
assert farms["policy"]["no_farm_above_172"] is False
assert 174 not in farms["policy"]["extension_repository_empty_ids"]
assert set(farms["policy"]["extension_repository_initialized_ids"])=={173,174}
assert set(farms["policy"]["extension_repository_selftest_pass_ids"])=={173,174}

f162=by_id[162]
assert f162["status"]=="PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING"
assert f162["repository_exists"] is False
assert (ROOT/f162["local_scaffold"]).exists()
assert f162["bootstrap_manifest"]=="config/farm-bootstrap-manifest-f162-f174.json"
assert (ROOT/f162["bootstrap_manifest"]).exists()

f173=by_id[173]
assert f173["repo"]=="cerebron-farm-173-aelys-live"
assert f173["identity"]=="AELYS"
assert f173["repository_exists"] is True
assert f173["repository_initialized"] is True
assert f173["training_status"]=="NOT_TRAINED"
assert f173["production_status"]=="NOT_DEPLOYED"
assert f173["dedicated_repo_selftest_run_id"]==36156589051
assert f173["master_plugin_bus_status"]=="DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED"
assert f173["local_contracts_status"]=="QUALIFIED"
assert f173["external_runtime_status"]=="UNQUALIFIED"
assert f173["rdx_route_provider"]=="RDX_EXCHANGE"
assert f173["f152_rdx_route_forbidden"] is True
assert f173["runtime_qualification_file"]=="config/runtime-qualification.json"
assert f173["evidence"]["unified_plugin_bus_guard_run_id"]==36156083228

f174=by_id[174]
assert f174["repo"]=="cerebron-farm-174-elyra-visual-simulation"
assert f174["identity"]=="ELYRA"
assert f174["status"]=="VIDEO_RENDER_CANARY_EXECUTED"
assert f174["repository_exists"] is True
assert f174["repository_initialized"] is True
assert f174["training_status"]=="NOT_TRAINED"
assert f174["simulation_status"]=="VIDEO_RENDER_CANARY_EXECUTED"
assert f174["visual_simulation_executed"] is True
assert f174["video_render_executed"] is True
assert f174["physical_model_claimed"] is False
assert f174["physical_validation_claimed"] is False
assert f174["physical_test_status"]=="NOT_TESTED"
assert f174["visual_canary"]["run_id"]==36160498658
assert f174["visual_canary"]["result_sha256"]=="edfa8d7f50c0906f8f5fa3051f6109c1fb7ba5463722df698e011e822d3d38c9"
assert f174["video_canary"]["run_id"]==36161254578
assert f174["video_canary"]["video_sha256"]=="95d5e25537760e22825728d0b019801023bd0ac1c321ab9a66cc6c5b8ca587fa"
assert f174["production_video_claimed"] is False
assert f174["dedicated_repo_selftest_run_id"]==36161396850
assert f174["dedicated_repo_head"]=="c122845a964461968ed9e7f9545b2edef59f0dcc"
assert f174["bootstrap_manifest"]=="config/farm-bootstrap-manifest-f162-f174.json"

for sub in ["scaffolds/f173-aelys-live","scaffolds/f174-elyra-visual-simulation"]:
    p=ROOT/sub
    subprocess.run([sys.executable,"validate_architecture.py"],cwd=p,check=True)
    subprocess.run([sys.executable,"-m","unittest","tests/test_scaffold.py","-v"],cwd=p,check=True)

print(json.dumps({
  "status":"PASS",
  "registry_max_farm":174,
  "f162":"PREPARED_REPOSITORY_MISSING",
  "f173":"LOCAL_CONTRACTS_QUALIFIED_EXTERNAL_RUNTIME_UNQUALIFIED",
  "f174":"VIDEO_RENDER_CANARY_EXECUTED_PRODUCTION_FALSE_PHYSICAL_NOT_TESTED",
  "training_claims":0,
  "execution_claims":0
},sort_keys=True))
