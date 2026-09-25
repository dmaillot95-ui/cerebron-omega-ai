#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parent
a=json.loads((R/"architecture/ELYRA_VISUAL_SIMULATION_V1.json").read_text())
p=json.loads((R/"config/project.json").read_text())
assert a["farm_id"]==174
assert a["identity"]=="ELYRA"
assert p["target_repo_exists"] is True
assert p["target_repo_initialized"] is True
assert p["training_status"]=="NOT_TRAINED"
assert p["visual_simulation_executed"] is True
assert p["video_render_executed"] is True
assert p["physical_model_claimed"] is False
assert p["production_video_claimed"] is False
assert p["physical_validation_claimed"] is False
assert p["physical_test_status"]=="NOT_TESTED"
assert p["visual_canary"]["run_id"]==36160498658
assert p["visual_canary"]["result_sha256"]=="edfa8d7f50c0906f8f5fa3051f6109c1fb7ba5463722df698e011e822d3d38c9"
assert p["video_canary"]["run_id"]==36161254578
assert p["video_canary"]["video_sha256"]=="95d5e25537760e22825728d0b019801023bd0ac1c321ab9a66cc6c5b8ca587fa"
print("PASS F174 ELYRA MP4 render canary executed; production and physical validation not claimed")
