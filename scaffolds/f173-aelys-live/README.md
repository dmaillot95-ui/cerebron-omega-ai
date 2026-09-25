# AÉLYS LIVE

CÉRÉBRON — F173

## Mission
Préparer une couche live AÉLYS vérifiable : contrat de session, ingress, routage, présentation, sortie locale et replay, sans déclarer de production live avant qualification réelle des runtimes externes.

## État
LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED

- target_repo: dmaillot95-ui/cerebron-farm-173-aelys-live
- target_repo_exists: true
- target_repo_initialized: true
- dedicated_repo_head: e9ac658d4c092c3fd3b1b799a7eb2653f645737d
- dedicated_repo_selftest_run: 36164296182
- training_status: NOT_TRAINED
- live_production_status: NOT_DEPLOYED
- external_runtime_status: UNQUALIFIED
- paid_provider_auto_activation: false

### Local live-loop canary
- run: 36162553038
- result_sha256: a860b0f9becd088496c6580b6febd608af0964e73c10b6ac04452048326fb3a4
- artifact_id: 10876417068
- external_calls_executed: false
- production_live_claimed: false

### Local TTS canary
- run: 36163338754
- engine: espeak-ng
- duration_s: 3.78254
- wav_bytes: 166854
- wav_sha256: 71eea3f77b68a77b5ca773950c961f63d38b4f33ed06cffcab57c325e56a2e9e
- artifact_id: 10875663863
- external_service_used: false
- paid_provider_used: false
- production_live_claimed: false
- voice_identity_claimed: false

### Local session replay canary
- run: 36163483531
- events: 3
- final_trace_hash: abcc5451ebbcb0965a9f220d8b445b2504ff97471e8dba1cbc1426ce9dc783b8
- result_sha256: 785eef06fa1357f513dbbee3f5dd87e9f36949a4e63588df67c4fffe6c404510
- artifact_id: 10876263729
- external_calls_executed: false
- production_live_claimed: false


### Local HTTP loopback canary
- run: 36164204308
- transport: HTTP_LOOPBACK
- bind: 127.0.0.1
- http_status: 200
- presentation_status: HOLD
- result_sha256: c9b21d56586df27bd4dee8e9964b170fb241fdec9b9f91822068d86ed77b8450
- artifact_id: 10876727408
- artifact_digest: sha256:03fad961a41073e42bd096830a93eb3caf6ef53e4995fae2077a6221c4c2f733
- external_endpoint_used: false
- paid_provider_used: false
- production_live_claimed: false
- raw_user_ref_persisted: false

REALITY > COHERENCE
EVIDENCE > CONFIDENCE
CLAIM <= EVIDENCE
MEMORY != TRAINING

LOCAL_CANARY_PASS != EXTERNAL_RUNTIME_QUALIFIED
TTS_LOCAL_CANARY != PRODUCTION_VOICE
SESSION_REPLAY != LIVE_DEPLOYMENT

HTTP_LOOPBACK_PASS != EXTERNAL_ENDPOINT_QUALIFIED
