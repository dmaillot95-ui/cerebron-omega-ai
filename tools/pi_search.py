#!/usr/bin/env python3
"""PI-SEARCH v1 — shared facade combining PI-SWEEP and PI-NEEDLE.

This tool standardizes candidate-direction generation for every CEREBRON AI.
It does not alter runtime, does not generate semantic answers itself, and
does not claim exhaustive coverage of an infinite answer space.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

# Allow both `python -m tools.pi_search` and direct `python tools/pi_search.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.pi_response_sweep import circle_sweep, fibonacci_sphere, refine_circle
from tools.pi_needle import sample_needles, coverage_stats

DEFAULTS = {
    "coarse_sweep_samples": 16,
    "needle_samples": 512,
    "sphere_samples": 32,
    "refine_top_k": 16,
    "refine_half_width_deg": 11.25,
    "refine_samples_per_sector": 9,
}

def build_search_packet(task_id, sweep_n=16, needle_n=512, sphere_n=32):
    sweep = circle_sweep(sweep_n)
    needles, seed = sample_needles(task_id, needle_n)
    sphere = fibonacci_sphere(sphere_n)
    packet = {
        "schema": "CEREBRON_PI_SEARCH_V1",
        "task_id": task_id,
        "runtime_changed": False,
        "seed": seed,
        "modes": {
            "sweep": {
                "count": len(sweep),
                "step_deg": 360.0 / sweep_n,
                "directions": sweep
            },
            "needle": {
                "count": len(needles),
                "coverage": coverage_stats(needles),
                "directions": needles
            },
            "sphere": {
                "count": len(sphere),
                "directions": sphere
            }
        },
        "recommended_flow": [
            "COARSE_SWEEP",
            "PI_NEEDLE_MONTE_CARLO",
            "GENERATE_CANDIDATES",
            "SCORE_QUALITY_EVIDENCE_NOVELTY",
            "DIVERSITY_FILTER",
            "REFINE_PROMISING_SECTORS",
            "ELYSIUM_REDTEAM",
            "OMEGA_EVIDENCE_GATE",
            "CEREBRON_FUSION"
        ],
        "rules": [
            "PI_IS_NOT_AN_ORACLE",
            "ANGLE_IS_SEARCH_DIRECTION_NOT_TRUTH",
            "FINITE_SEARCH_IS_NOT_EXHAUSTIVE",
            "FALSE_AND_TRUE_CANDIDATES_MAY_BOTH_APPEAR",
            "SAME_TASK_SAME_SEED_FOR_REPRODUCIBILITY",
            "CLAIM_LE_EVIDENCE",
            "RUNTIME_FREEZE"
        ]
    }
    raw=json.dumps(packet,sort_keys=True,separators=(",",":")).encode()
    packet["result_sha256"]=hashlib.sha256(raw).hexdigest()
    return packet

def refine_sector(center_deg, half_width_deg=11.25, n=9):
    rows=refine_circle(math.radians(center_deg),math.radians(half_width_deg),n)
    for row in rows:
        row["theta_deg"]=math.degrees(row["theta_rad"])
        row["unit_vector"]=[math.cos(row["theta_rad"]),math.sin(row["theta_rad"])]
    return rows

def self_test():
    a=build_search_packet("PI-SEARCH-SELFTEST",16,128,32)
    b=build_search_packet("PI-SEARCH-SELFTEST",16,128,32)
    assert a["result_sha256"]==b["result_sha256"]
    assert a["seed"]==b["seed"]
    assert len(a["modes"]["sweep"]["directions"])==16
    assert len(a["modes"]["needle"]["directions"])==128
    assert len(a["modes"]["sphere"]["directions"])==32
    assert len(refine_sector(180.0,11.25,9))==9
    assert a["runtime_changed"] is False
    return {
        "status":"PASS",
        "schema":a["schema"],
        "seed":a["seed"],
        "sweep":16,
        "needle":128,
        "sphere":32,
        "runtime_changed":False,
        "result_sha256":a["result_sha256"],
        "claim":"shared deterministic search packet self-test only"
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",default="CEREBRON-PI-SEARCH")
    ap.add_argument("--sweep",type=int,default=16)
    ap.add_argument("--needle",type=int,default=512)
    ap.add_argument("--sphere",type=int,default=32)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2))
        return
    out=build_search_packet(args.task,args.sweep,args.needle,args.sphere)
    Path("out").mkdir(exist_ok=True)
    Path("out/pi-search.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":out["schema"],
        "task_id":out["task_id"],
        "seed":out["seed"],
        "sweep":args.sweep,
        "needle":args.needle,
        "sphere":args.sphere,
        "needle_max_gap_deg":out["modes"]["needle"]["coverage"]["max_gap_deg"],
        "result_sha256":out["result_sha256"],
        "runtime_changed":False
    },sort_keys=True))

if __name__=="__main__":
    main()
