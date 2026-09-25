#!/usr/bin/env python3
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
bus=json.loads((R/"config/cerebron-unified-plugin-bus-v1.json").read_text())
farms=json.loads((R/"config/farms.json").read_text())
by_id={f["id"]:f for f in farms["farms"]}

assert bus["schema"]=="CEREBRON_UNIFIED_PLUGIN_BUS_V1"
assert bus["automatic_external_calls"] is False
assert bus["automatic_training"] is False
assert bus["paid_provider_auto_activation"] is False

assert by_id[152]["identity"]=="BETA"
assert bus["routes"]["rdx.search"]=="RDX_EXCHANGE"
assert bus["routes"]["rdx.fetch"]=="RDX_EXCHANGE"
assert "F152_RDX" not in bus["providers"]
assert bus["providers"]["RDX_EXCHANGE"]["repository"]=="dmaillot95-ui/cerebron-rdx-exchange"
assert bus["providers"]["RDX_EXCHANGE"]["runtime_status"]=="UNBOUND"

assert by_id[173]["identity"]=="AELYS"
assert by_id[173]["repository_initialized"] is True
assert bus["providers"]["AELYS"]["farm_id"]==173
assert by_id[173]["status"]=="LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_EXECUTED_EXTERNAL_RUNTIME_UNQUALIFIED"
assert by_id[173]["local_live_loop_canary"]["run_id"]==36162553038
assert by_id[173]["external_runtime_status"]=="UNQUALIFIED"
assert by_id[173]["production_status"]=="NOT_DEPLOYED"
assert bus["providers"]["AELYS"]["local_live_loop_canary"]["status"]=="PASS"
assert bus["providers"]["AELYS"]["local_live_loop_canary"]["run_id"]==36162553038
assert bus["providers"]["AELYS"]["local_live_loop_canary"]["external_calls_executed"] is False
assert bus["providers"]["AELYS"]["local_live_loop_canary"]["production_live_claimed"] is False
assert bus["providers"]["AELYS"]["local_tts_canary"]["status"]=="PASS"
assert bus["providers"]["AELYS"]["local_tts_canary"]["run_id"]==36163338754
assert bus["providers"]["AELYS"]["local_tts_canary"]["wav_sha256"]=="71eea3f77b68a77b5ca773950c961f63d38b4f33ed06cffcab57c325e56a2e9e"
assert bus["providers"]["AELYS"]["local_tts_canary"]["external_service_used"] is False
assert bus["providers"]["AELYS"]["local_tts_canary"]["production_live_claimed"] is False
assert bus["providers"]["AELYS"]["local_session_replay_canary"]["status"]=="PASS"
assert bus["providers"]["AELYS"]["local_session_replay_canary"]["run_id"]==36163483531
assert bus["providers"]["AELYS"]["local_session_replay_canary"]["final_trace_hash"]=="abcc5451ebbcb0965a9f220d8b445b2504ff97471e8dba1cbc1426ce9dc783b8"
assert bus["providers"]["AELYS"]["local_session_replay_canary"]["external_calls_executed"] is False
assert bus["providers"]["AELYS"]["local_session_replay_canary"]["production_live_claimed"] is False
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["status"]=="PASS"
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["run_id"]==36164204308
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["transport"]=="HTTP_LOOPBACK"
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["bind"]=="127.0.0.1"
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["http_status"]==200
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["result_sha256"]=="c9b21d56586df27bd4dee8e9964b170fb241fdec9b9f91822068d86ed77b8450"
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["external_endpoint_used"] is False
assert bus["providers"]["AELYS"]["local_http_loopback_canary"]["production_live_claimed"] is False
assert bus["invariants"]["f173_http_loopback_does_not_imply_external_runtime"] is True
assert bus["invariants"]["f173_local_canaries_do_not_imply_external_runtime"] is True
assert bus["providers"]["AELYS"]["runtime_status"]=="LOCAL_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED"

assert by_id[174]["identity"]=="ELYRA"
assert by_id[174]["repository_initialized"] is True
assert by_id[174]["simulation_status"]=="VIDEO_RENDER_CANARY_EXECUTED"
assert by_id[174]["visual_simulation_executed"] is True
assert by_id[174]["video_render_executed"] is True
assert by_id[174]["physical_validation_claimed"] is False
assert by_id[174]["physical_test_status"]=="NOT_TESTED"
assert by_id[174]["visual_canary"]["run_id"]==36160498658
assert 174 in bus["providers"]["ELYRA"]["farm_refs"]
assert bus["routes"]["visual.simulate"]=="ELYRA"
assert "visual.simulate" in bus["providers"]["ELYRA"]["capabilities"]
assert bus["providers"]["ELYRA"]["runtime_status"]=="UNQUALIFIED"
assert bus["providers"]["ELYRA"]["visual_canary"]["status"]=="PASS"
assert bus["providers"]["ELYRA"]["visual_canary"]["run_id"]==36160498658
assert bus["providers"]["ELYRA"]["visual_canary"]["video_render_executed"] is False
assert bus["providers"]["ELYRA"]["visual_canary"]["physical_validation_claimed"] is False
assert bus["providers"]["ELYRA"]["video_canary"]["status"]=="PASS"
assert bus["providers"]["ELYRA"]["video_canary"]["run_id"]==36161254578
assert bus["providers"]["ELYRA"]["video_canary"]["video_sha256"]=="95d5e25537760e22825728d0b019801023bd0ac1c321ab9a66cc6c5b8ca587fa"
assert bus["providers"]["ELYRA"]["video_canary"]["production_video_claimed"] is False
assert bus["providers"]["ELYRA"]["video_canary"]["physical_validation_claimed"] is False

for capability, provider in bus["routes"].items():
    assert provider in bus["providers"], (capability,provider)
    assert capability in bus["providers"][provider]["capabilities"], (capability,provider)

assert bus["invariants"]["f152_identity"]=="BETA"
assert bus["invariants"]["f152_must_not_route_rdx"] is True
assert bus["invariants"]["unknown_capability"]=="DENY"
assert bus["invariants"]["f174_repository_initialized_not_simulation_execution"] is True

print(json.dumps({
  "status":"PASS",
  "rdx_provider":"RDX_EXCHANGE",
  "rdx_runtime":"UNBOUND",
  "f152_identity":"BETA",
  "f173_runtime":"LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED",
  "f174_runtime":"UNQUALIFIED_MP4_CANARY_EXECUTED_PRODUCTION_FALSE_PHYSICAL_FALSE",
  "automatic_external_calls":False,
  "automatic_training":False
},sort_keys=True))
