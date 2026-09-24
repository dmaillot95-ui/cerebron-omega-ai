#!/usr/bin/env python3
"""PI-NEEDLE v1 — reproducible Monte-Carlo response-direction sampler.

Concept inspired by Buffon's needle, adapted only as a search metaphor.
This tool does NOT claim that answers are encoded in pi and does NOT use pi
as an oracle. It samples candidate reasoning directions over [0, 2*pi).

RUNTIME FREEZE: this is a shared tool, not a runtime modification.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

TAU = 2.0 * math.pi

OPERATORS = [
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

def seed_from_text(text):
    h = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
    return int(h[:16], 16)

def sample_needles(task_id, n=256, seed=None):
    if n < 8 or n > 100000:
        raise ValueError("n must be in [8,100000]")
    if seed is None:
        seed = seed_from_text(task_id)
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        theta = rng.random() * TAU
        # Independent radial coordinate only for stratification/visualization.
        rho = math.sqrt(rng.random())
        op = OPERATORS[int((theta / TAU) * len(OPERATORS)) % len(OPERATORS)]
        rows.append({
            "needle_id": f"N{i:06d}",
            "theta_rad": theta,
            "theta_deg": math.degrees(theta),
            "rho": rho,
            "unit_vector": [math.cos(theta), math.sin(theta)],
            "operator": op,
        })
    return rows, seed

def angular_distance(a, b):
    d = abs((a-b) % TAU)
    return min(d, TAU-d)

def coverage_stats(rows):
    angles = sorted(r["theta_rad"] for r in rows)
    gaps = []
    for i,a in enumerate(angles):
        b = angles[(i+1) % len(angles)]
        gap = (b-a) % TAU
        gaps.append(gap)
    bins = [0] * len(OPERATORS)
    for r in rows:
        bins[OPERATORS.index(r["operator"])] += 1
    return {
        "sample_count": len(rows),
        "max_gap_deg": math.degrees(max(gaps)),
        "mean_gap_deg": 360.0 / len(rows),
        "operator_counts": dict(zip(OPERATORS, bins)),
    }

def select_diverse(rows, scores, k=16, min_sep_deg=8.0):
    if len(rows) != len(scores):
        raise ValueError("rows/scores length mismatch")
    ranked = sorted(range(len(rows)), key=lambda i: scores[i], reverse=True)
    chosen = []
    min_sep = math.radians(min_sep_deg)
    for i in ranked:
        theta = rows[i]["theta_rad"]
        if all(angular_distance(theta, rows[j]["theta_rad"]) >= min_sep for j in chosen):
            chosen.append(i)
            if len(chosen) >= k:
                break
    return [{"needle": rows[i], "score": float(scores[i])} for i in chosen]

def manifest(task_id, n=256, seed=None):
    rows, used_seed = sample_needles(task_id, n, seed)
    stats = coverage_stats(rows)
    payload = {
        "schema": "CEREBRON_PI_NEEDLE_V1",
        "task_id": task_id,
        "runtime_changed": False,
        "seed": used_seed,
        "meaning": "Monte-Carlo search directions inspired by Buffon; not a pi oracle",
        "math": {
            "pi_rad": math.pi,
            "tau_2pi_rad": TAU,
            "full_rotation_deg": 360.0,
        },
        "samples": rows,
        "coverage": stats,
        "protocol": [
            "DETERMINISTIC_SEED_FROM_TASK",
            "RANDOM_DIRECTION_SAMPLING",
            "AI_GENERATION_PER_SELECTED_DIRECTION",
            "DIVERSITY_SELECTION",
            "LOCAL_REFINEMENT_WITH_PI_SWEEP",
            "ELYSIUM_REDTEAM",
            "OMEGA_EVIDENCE_GATE",
            "CEREBRON_FUSION",
        ],
        "rules": [
            "PI_IS_NOT_AN_ORACLE",
            "RANDOM_SAMPLE_IS_NOT_PROOF",
            "FALSE_AND_TRUE_CANDIDATES_MAY_BOTH_APPEAR",
            "DIVERSITY_BEFORE_DEPTH",
            "CLAIM_LE_EVIDENCE",
            "RUNTIME_FREEZE",
        ],
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["result_sha256"]=hashlib.sha256(raw).hexdigest()
    return payload

def self_test():
    a = manifest("TEST-TASK", 256)
    b = manifest("TEST-TASK", 256)
    assert a["seed"] == b["seed"]
    assert a["result_sha256"] == b["result_sha256"]
    assert len(a["samples"]) == 256
    assert a["runtime_changed"] is False
    for p in a["samples"]:
        x,y=p["unit_vector"]
        assert abs(x*x+y*y-1.0) < 1e-12
    return {
        "status":"PASS",
        "sample_count":256,
        "seed":a["seed"],
        "max_gap_deg":a["coverage"]["max_gap_deg"],
        "result_sha256":a["result_sha256"],
        "runtime_changed":False,
        "claim":"deterministic Monte-Carlo direction sampling self-test only",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",default="CEREBRON-DEMO")
    ap.add_argument("--samples",type=int,default=256)
    ap.add_argument("--seed",type=int,default=None)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2))
        return
    out=manifest(args.task,args.samples,args.seed)
    Path("out").mkdir(exist_ok=True)
    Path("out/pi-needle.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":out["schema"],
        "task_id":out["task_id"],
        "sample_count":out["coverage"]["sample_count"],
        "max_gap_deg":out["coverage"]["max_gap_deg"],
        "mean_gap_deg":out["coverage"]["mean_gap_deg"],
        "seed":out["seed"],
        "result_sha256":out["result_sha256"],
        "runtime_changed":False,
    },sort_keys=True))

if __name__=="__main__":
    main()
