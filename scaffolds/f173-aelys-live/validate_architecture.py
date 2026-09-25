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
assert p["live_production_status"]=="NOT_DEPLOYED"
assert p["external_runtime_status"]=="UNQUALIFIED"
assert p["paid_provider_auto_activation"] is False
assert p["dedicated_repo_selftest_run_id"]==36164296182
assert p["dedicated_repo_head"]=="e9ac658d4c092c3fd3b1b799a7eb2653f645737d"
assert p["status"]=="LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED"
assert p["local_live_loop_canary"]["run_id"]==36162553038
assert p["local_live_loop_canary"]["result_sha256"]=="a860b0f9becd088496c6580b6febd608af0964e73c10b6ac04452048326fb3a4"
assert p["local_live_loop_canary"]["external_calls_executed"] is False
assert p["local_live_loop_canary"]["production_live_claimed"] is False
assert p["local_tts_canary"]["run_id"]==36163338754
assert p["local_tts_canary"]["wav_sha256"]=="71eea3f77b68a77b5ca773950c961f63d38b4f33ed06cffcab57c325e56a2e9e"
assert p["local_tts_canary"]["external_service_used"] is False
assert p["local_tts_canary"]["paid_provider_used"] is False
assert p["local_tts_canary"]["production_live_claimed"] is False
assert p["local_session_replay_canary"]["run_id"]==36163483531
assert p["local_session_replay_canary"]["final_trace_hash"]=="abcc5451ebbcb0965a9f220d8b445b2504ff97471e8dba1cbc1426ce9dc783b8"
assert p["local_session_replay_canary"]["result_sha256"]=="785eef06fa1357f513dbbee3f5dd87e9f36949a4e63588df67c4fffe6c404510"
assert p["local_session_replay_canary"]["external_calls_executed"] is False
assert p["local_session_replay_canary"]["production_live_claimed"] is False
assert p["local_http_loopback_canary"]["run_id"]==36164204308
assert p["local_http_loopback_canary"]["transport"]=="HTTP_LOOPBACK"
assert p["local_http_loopback_canary"]["bind"]=="127.0.0.1"
assert p["local_http_loopback_canary"]["http_status"]==200
assert p["local_http_loopback_canary"]["presentation_status"]=="HOLD"
assert p["local_http_loopback_canary"]["result_sha256"]=="c9b21d56586df27bd4dee8e9964b170fb241fdec9b9f91822068d86ed77b8450"
assert p["local_http_loopback_canary"]["external_endpoint_used"] is False
assert p["local_http_loopback_canary"]["production_live_claimed"] is False
print("PASS F173 local loop + TTS + replay + HTTP loopback canaries; external runtime unqualified")
