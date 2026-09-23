from __future__ import annotations

import hashlib
import json
import pathlib

V5 = {
    "run_id": 35873551620,
    "job_id": 107223537626,
    "artifact_id": 10756230520,
    "result_sha256": "24ca9d124df1e215946108ad783f34a8ba942c52b1c7d9fdc0d1b466959f968c",
    "lunar_zmax_m": 0.24499006569385529,
    "earth_zmax_m": 0.24493995308876038,
    "lunar_spread_m": 0.31200000643730164,
    "earth_spread_m": 0.31200000643730164,
}

V6 = {
    "run_id": 35899534732,
    "job_id": 107311855880,
    "artifact_id": 10767758851,
    "artifact_digest": "sha256:6dcf42b7a4302975a90223c39f3e55fe03ee5c38060c538c7776e59ebdc0c9b1",
    "result_sha256": "e5beddcd3609538d4dc9ef882f3c26af6bc62427b83a4773eb05b199f9a9ee4a",
    "dynamic_discrimination_index": 0.387336969872355,
    "delta_0_5s": {
        "spread": 0.40455185566988094,
        "height": 0.5958988387551634,
        "com_z": 0.6344948595984261,
    },
}

def rel(a, b):
    return abs(a-b)/max(abs(a),abs(b),1e-12)

v5_zmax_delta = rel(V5["lunar_zmax_m"], V5["earth_zmax_m"])
v5_spread_delta = rel(V5["lunar_spread_m"], V5["earth_spread_m"])

comparison = {
    "schema": "CEREBRON_AGORA_F139_GAIN_V3",
    "v5": V5,
    "v6": V6,
    "v5_final_zmax_relative_delta": v5_zmax_delta,
    "v5_final_spread_relative_delta": v5_spread_delta,
    "v6_dynamic_discrimination_index": V6["dynamic_discrimination_index"],
    "interpretation": {
        "v5": "CONSTRAINED_PACKING_TOO_WEAKLY_DISCRIMINATING",
        "v6": "FREE_COLLAPSE_TRANSIENT_METRICS_STRONGLY_MORE_DISCRIMINATING",
        "metric_warning": "V5 final-state delta and V6 multi-time proxy are not identical metrics; do not present their ratio as a calibrated scientific gain factor.",
    },
    "decision": "KEEP_FREE_COLLAPSE_AS_MORE_DISCRIMINATING_TEST",
    "gold_promotion": "BLOCKED_PENDING_REPRODUCTION_AND_CALIBRATION",
    "training_eligible": False,
    "gold_eligible": False,
    "limitations": [
        "same Newton numerical engine family; not an independent physical reproduction",
        "monodisperse spherical grains",
        "contact/material parameters not experimentally calibrated",
        "V6 discrimination proxy is an engineering sensitivity metric",
    ],
}
raw=json.dumps(comparison,sort_keys=True,separators=(",",":")).encode()
comparison["comparison_sha256"]=hashlib.sha256(raw).hexdigest()
pathlib.Path("artifacts").mkdir(exist_ok=True)
pathlib.Path("artifacts/agora_f139_gain_v3.json").write_text(json.dumps(comparison,indent=2)+"\n")
print(json.dumps(comparison))
