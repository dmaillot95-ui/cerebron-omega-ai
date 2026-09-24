#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/"config/greek-ai-constellation-v1.json").read_text())
reg=json.loads((ROOT/"config/farms.json").read_text())

roles=cfg["roles"]
assert len(roles)==24, len(roles)
assert len({r["letter"] for r in roles})==24
assert len({r["name"] for r in roles})==24
assert len({r["role_id"] for r in roles})==24
assert cfg["per_ai_passes"]==10
assert cfg["raw_role_passes_per_full_campaign"]==240
assert cfg["runtime_changed"] is False
assert cfg["compression_funnel"]==[
    "240_RAW_PASSES",
    "24_LOCAL_CAPSULES",
    "6_PHASE_CAPSULES",
    "3_INDEPENDENT_META_SYNTHESIS",
    "1_FINAL_VERIFIED_SYNTHESIS",
]

farm_by_id={f["id"]:f for f in reg["farms"]}
for r in roles:
    f=farm_by_id[r["id"]]
    assert f["greek_constellation"] is True
    assert f["identity"]==r["name"]
    assert f["greek_letter"]==r["letter"]
    assert f["role_id"]==r["role_id"]
    assert f["campaign_passes"]==10

assert reg["policy"]["greek_ai_count"]==24
assert reg["policy"]["greek_ai_full_campaign_passes"]==240

print(json.dumps({
    "status":"PASS",
    "greek_ai_count":len(roles),
    "unique_role_ids":len({r["role_id"] for r in roles}),
    "passes_per_ai":cfg["per_ai_passes"],
    "raw_passes":cfg["raw_role_passes_per_full_campaign"],
    "final_capsules":1,
    "runtime_changed":False,
}, sort_keys=True))
