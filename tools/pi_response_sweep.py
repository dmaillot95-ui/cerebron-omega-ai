#!/usr/bin/env python3
"""PI-SWEEP v1 — shared deterministic response-angle search.

This is a search/coverage tool, not a reasoning model and not a proof engine.
It does not modify the CEREBRON runtime. It generates common directional
probes that any real AI/agent can receive and answer independently.

Math:
- A full planar rotation is 2*pi radians = 360 degrees.
- A finite run cannot enumerate a continuum, so coverage is sampled.
- Coarse sectors can be refined around promising directions.
- 3D directions use a deterministic Fibonacci-sphere approximation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

TAU = 2.0 * math.pi

RESPONSE_OPERATORS = [
    "DIRECT",
    "INVERSE",
    "BOUNDARY_CASE",
    "COUNTEREXAMPLE",
    "CAUSAL",
    "COUNTERFACTUAL",
    "ANALOGICAL",
    "FORMAL_PROOF",
    "NUMERICAL",
    "EXPERIMENTAL",
    "SYSTEMS",
    "FAILURE_MODE",
    "ALTERNATIVE_REPRESENTATION",
    "RESOURCE_CONSTRAINT",
    "TRANSFER",
    "RED_TEAM",
]

def circle_sweep(n=16, phase=0.0):
    if n < 4 or n > 4096:
        raise ValueError("n must be in [4,4096]")
    step = TAU / n
    out = []
    for k in range(n):
        theta = (phase + k * step) % TAU
        out.append({
            "angle_id": f"C{k:04d}",
            "theta_rad": theta,
            "theta_deg": math.degrees(theta),
            "unit_vector": [math.cos(theta), math.sin(theta)],
            "operator": RESPONSE_OPERATORS[k % len(RESPONSE_OPERATORS)],
        })
    return out

def refine_circle(center_rad, half_width_rad, n=9):
    if n < 3 or n > 4096:
        raise ValueError("n must be in [3,4096]")
    if not (0.0 < half_width_rad <= math.pi):
        raise ValueError("half_width_rad must be in (0,pi]")
    return [
        {
            "angle_id": f"R{k:04d}",
            "theta_rad": (center_rad - half_width_rad + (2.0 * half_width_rad) * k/(n-1)) % TAU,
        }
        for k in range(n)
    ]

def fibonacci_sphere(n=32):
    if n < 4 or n > 4096:
        raise ValueError("n must be in [4,4096]")
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    pts = []
    for k in range(n):
        z = 1.0 - 2.0 * (k + 0.5) / n
        r = math.sqrt(max(0.0, 1.0 - z*z))
        phi = (k * golden_angle) % TAU
        x = r * math.cos(phi)
        y = r * math.sin(phi)
        pts.append({
            "angle_id": f"S{k:04d}",
            "azimuth_rad": phi,
            "azimuth_deg": math.degrees(phi),
            "elevation_rad": math.asin(z),
            "elevation_deg": math.degrees(math.asin(z)),
            "unit_vector": [x, y, z],
            "operator": RESPONSE_OPERATORS[k % len(RESPONSE_OPERATORS)],
        })
    return pts

def coverage_manifest(circle_n=16, sphere_n=32):
    circle = circle_sweep(circle_n)
    sphere = fibonacci_sphere(sphere_n)
    payload = {
        "schema": "CEREBRON_PI_SWEEP_V1",
        "runtime_changed": False,
        "meaning": "shared finite directional search; not exhaustive reasoning",
        "math": {
            "pi_rad": math.pi,
            "tau_2pi_rad": TAU,
            "full_rotation_deg": 360.0,
            "circle_samples": circle_n,
            "circle_step_deg": 360.0 / circle_n,
            "circle_max_nearest_sample_error_deg": 180.0 / circle_n,
            "sphere_samples": sphere_n,
        },
        "operators": RESPONSE_OPERATORS,
        "circle": circle,
        "sphere": sphere,
        "protocol": [
            "COARSE_SWEEP",
            "GENERATE_ONE_CANDIDATE_PER_DIRECTION",
            "SCORE_WITH_COMMON_METRICS",
            "REFINE_TOP_SECTORS",
            "ELYSIUM_REDTEAM",
            "OMEGA_EVIDENCE_GATE",
            "CEREBRON_FUSION",
        ],
        "rules": [
            "SAME_ANGLE_SET_FOR_COMPARABLE_RUNS",
            "ANGLE_IS_SEARCH_DIRECTION_NOT_TRUTH",
            "FINITE_SWEEP_IS_NOT_EXHAUSTIVE_PROOF",
            "CONSENSUS_IS_NOT_TRUTH",
            "CLAIM_LE_EVIDENCE",
            "RUNTIME_FREEZE",
        ],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["result_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload

def self_test():
    c = circle_sweep(16)
    assert len(c) == 16
    assert abs(c[0]["theta_rad"]) < 1e-15
    assert abs(c[8]["theta_rad"] - math.pi) < 1e-12
    for p in c:
        x,y = p["unit_vector"]
        assert abs(x*x + y*y - 1.0) < 1e-12
    s = fibonacci_sphere(64)
    for p in s:
        x,y,z = p["unit_vector"]
        assert abs(x*x + y*y + z*z - 1.0) < 1e-12
    r = refine_circle(math.pi, math.pi/8, 9)
    assert len(r) == 9
    m = coverage_manifest(16,32)
    assert m["runtime_changed"] is False
    assert m["math"]["full_rotation_deg"] == 360.0
    assert len(m["operators"]) == 16
    return {
        "status": "PASS",
        "circle_n": 16,
        "sphere_n": 64,
        "operators": len(RESPONSE_OPERATORS),
        "runtime_changed": False,
        "claim": "deterministic geometry/coverage self-test only",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--circle", type=int, default=16)
    ap.add_argument("--sphere", type=int, default=32)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return
    out = coverage_manifest(args.circle, args.sphere)
    Path("out").mkdir(exist_ok=True)
    Path("out/pi-response-sweep.json").write_text(json.dumps(out, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "schema": out["schema"],
        "circle_samples": args.circle,
        "sphere_samples": args.sphere,
        "circle_step_deg": out["math"]["circle_step_deg"],
        "max_nearest_error_deg": out["math"]["circle_max_nearest_sample_error_deg"],
        "result_sha256": out["result_sha256"],
        "runtime_changed": False,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
