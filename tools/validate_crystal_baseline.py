#!/usr/bin/env python3
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
cp=json.loads((R/"checkpoints/CEREBRON_80_M01_CRYSTAL_BASELINE.json").read_text())
farms=json.loads((R/"config/farms.json").read_text())
top=json.loads((R/"config/ai-8-agent-topology-v1.json").read_text())
crystal=json.loads((R/"config/crystal-preservation-v1.json").read_text())
route=json.loads((R/"config/private-memory-route.json").read_text())
mem=json.loads((R/"config/memory-fabric-v1.json").read_text())

assert cp["message"]==1
assert cp["runtime_changed"] is False

# The crystal baseline preserves farms 1..172. Later farms may only extend it append-only.
expected=farms["max_farms"]
assert expected >= 172
assert farms["policy"]["farm_cap"]==expected
assert len(farms["farms"])==expected
assert {f["id"] for f in farms["farms"]}==set(range(1, expected+1))
assert all(any(f["id"]==i for f in farms["farms"]) for i in range(1,173))

assert top["per_ai_agent_slots"]==8
assert top["burst_pool"]["max_agents"]==20
assert top["runtime_changed"] is False
assert crystal["no_overwrite"] is True
assert "APPEND_OR_VERSION_NEVER_DESTRUCTIVE_OVERWRITE" in crystal["invariants"]
assert route["routes"]["private_data_plane"]["availability"]=="VERIFIED_SCOPED"
assert mem["status"].startswith("CONTROL_PLANE_ACTIVE_HF_PRIVATE_SCOPED_VERIFIED")

by_id={f["id"]:f for f in farms["farms"]}
assert by_id[162]["repository_exists"] is False
assert by_id[162]["status"]=="PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING"
assert (R/by_id[162]["local_scaffold"]).exists()

if expected >= 174:
    assert by_id[173]["repository_exists"] is True
    assert by_id[173]["repository_initialized"] is True
    assert by_id[173]["status"]=="LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_EXECUTED_EXTERNAL_RUNTIME_UNQUALIFIED"
    assert by_id[173]["dedicated_repo_selftest_run_id"]==36164296182
    assert by_id[173]["master_plugin_bus_status"]=="DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED"
    assert by_id[173]["local_live_loop_canary"]["run_id"]==36162553038
    assert by_id[173]["local_live_loop_canary"]["external_calls_executed"] is False
    assert by_id[173]["local_tts_canary"]["run_id"]==36163338754
    assert by_id[173]["local_tts_canary"]["external_service_used"] is False
    assert by_id[173]["local_tts_canary"]["production_live_claimed"] is False
    assert by_id[173]["local_session_replay_canary"]["run_id"]==36163483531
    assert by_id[173]["local_session_replay_canary"]["external_calls_executed"] is False
    assert by_id[173]["local_session_replay_canary"]["production_live_claimed"] is False
    assert by_id[173]["local_http_loopback_canary"]["run_id"]==36164204308
    assert by_id[173]["local_http_loopback_canary"]["external_endpoint_used"] is False
    assert by_id[173]["local_http_loopback_canary"]["production_live_claimed"] is False
    assert by_id[173]["production_status"]=="NOT_DEPLOYED"
    assert by_id[173]["evidence"]["unified_plugin_bus_guard_run_id"]==36163898021
    assert (R/by_id[173]["local_scaffold"]).exists()

    assert by_id[174]["repository_exists"] is True
    assert by_id[174]["repository_initialized"] is True
    assert by_id[174]["status"]=="VIDEO_RENDER_CANARY_EXECUTED"
    assert by_id[174]["dedicated_repo_selftest_run_id"]==36161396850
    assert by_id[174]["simulation_status"]=="VIDEO_RENDER_CANARY_EXECUTED"
    assert by_id[174]["visual_simulation_executed"] is True
    assert by_id[174]["video_render_executed"] is True
    assert by_id[174]["physical_validation_claimed"] is False
    assert by_id[174]["physical_test_status"]=="NOT_TESTED"
    assert by_id[174]["visual_canary"]["run_id"]==36160498658
    assert by_id[174]["visual_canary"]["result_sha256"]=="edfa8d7f50c0906f8f5fa3051f6109c1fb7ba5463722df698e011e822d3d38c9"
    assert by_id[174]["video_canary"]["run_id"]==36161254578
    assert by_id[174]["video_canary"]["video_sha256"]=="95d5e25537760e22825728d0b019801023bd0ac1c321ab9a66cc6c5b8ca587fa"
    assert by_id[174]["production_video_claimed"] is False
    assert (R/by_id[174]["local_scaffold"]).exists()

missing=[f["id"] for f in farms["farms"] if f.get("repository_exists") is False]
assert missing==[162], missing

print(json.dumps({
 "status":"PASS",
 "campaign_message":1,
 "crystal_baseline_min_farms":172,
 "registry_count":len(farms["farms"]),
 "extension_count":max(0, expected-172),
 "agent_slots_per_ai":top["per_ai_agent_slots"],
 "burst_pool_max":top["burst_pool"]["max_agents"],
 "hf_scope":"SCOPED_VERIFIED",
 "missing_repository_ids":missing,
 "runtime_changed":False,
 "no_destructive_overwrite":True
}, sort_keys=True))
