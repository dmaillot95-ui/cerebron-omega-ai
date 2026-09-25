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
assert p["dedicated_repo_selftest_run_id"]==36163651569
assert p["dedicated_repo_head"]=="6742951eb3f5f4a4804f8cb79aaae579b09be5a6"
assert p["status"]=="LOCAL_LIVE_LOOP_TTS_SESSION_REPLAY_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED"
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
print("PASS F173 local loop + TTS + session replay canaries; external runtime unqualified")
