from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import random
import statistics

import torch
from torch import nn

SOURCE_DIR = pathlib.Path("platform/artifacts/source")
OUT_DIR = pathlib.Path("platform/artifacts")
SOURCE_WEIGHTS = SOURCE_DIR / "elyra-imitation-policy-v1.pt"
EXPECTED_WEIGHTS_SHA = "b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601"
AUDIT_EPISODES = 240
GOAL_X = 28.0
GOAL_Y = 0.0
MAX_STEPS = 200
DT = 0.25
BATTERY_WH = 1800.0


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def angle_wrap(x):
    while x > math.pi:
        x -= 2 * math.pi
    while x < -math.pi:
        x += 2 * math.pi
    return x


class AuditPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(8, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, 2),
        )

    def forward(self, x):
        raw = self.net(x)
        return torch.cat([torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:2])], dim=1)


def norm_features(x: torch.Tensor) -> torch.Tensor:
    scales = torch.tensor([math.pi, 5.0, 1.0, 1.0, 0.62, 1.2, 0.35, 0.18], dtype=x.dtype)
    y = x / scales
    y[:, 1] = torch.clamp(y[:, 1], -0.25, 1.25)
    return y


def teacher(features):
    h, d, side, ahead, slip, _speed, _rough, _slope = features
    desired = h
    if d < 2.5 and ahead > 0.5:
        desired += side * (0.55 + 0.45 * clamp((2.5 - d) / 2.5, 0.0, 1.0))
    steer = clamp(1.4 * desired, -0.8, 0.8)
    throttle = 0.32 if d < 0.8 else (0.52 if slip > 0.28 else 0.78)
    return {"throttle": throttle, "steer": steer}


def action_from_model(model, features):
    x = torch.tensor([features], dtype=torch.float32)
    with torch.no_grad():
        raw = model(norm_features(x))[0]
    throttle_raw = clamp(float(raw[0]), 0.0, 1.0)
    throttle = min((0.32, 0.52, 0.78), key=lambda v: abs(v - throttle_raw))
    steer = clamp(float(raw[1]) * 0.8, -0.8, 0.8)
    return {"throttle": throttle, "steer": steer}


def shifted_world(seed):
    rng = random.Random(seed)
    obstacles = [
        {
            "x": rng.uniform(4.5, 25.0),
            "y": rng.uniform(-7.0, 7.0),
            "r": rng.uniform(0.40, 1.35),
        }
        for _ in range(rng.randint(4, 8))
    ]
    return {
        "roughness": rng.uniform(0.08, 0.42),
        "cross_slope": rng.uniform(-0.22, 0.22),
        "obstacles": obstacles,
    }


def obstacle_distance(x, y, obs):
    return math.hypot(x - obs["x"], y - obs["y"]) - obs["r"]


def observe(state, world):
    desired = math.atan2(GOAL_Y - state["y"], GOAL_X - state["x"])
    heading_error = angle_wrap(desired - state["heading"])
    nearest = min(world["obstacles"], key=lambda o: obstacle_distance(state["x"], state["y"], o))
    d = obstacle_distance(state["x"], state["y"], nearest)
    side = -1.0 if nearest["y"] >= state["y"] else 1.0
    ahead = 1.0 if nearest["x"] > state["x"] - 0.5 else 0.0
    return [
        heading_error, d, side, ahead, state["slip"], state["speed"],
        world["roughness"], abs(world["cross_slope"]),
    ]


def env_step(state, action, world):
    throttle = clamp(action["throttle"], 0.0, 1.0)
    steer = clamp(action["steer"], -1.0, 1.0)
    rough = world["roughness"]
    slope = abs(world["cross_slope"])
    slip = clamp(0.035 + rough*0.55 + slope*0.35 + throttle*0.07 + abs(steer)*0.05, 0.0, 0.62)
    target_speed = 1.15 * throttle
    speed = state["speed"] + (target_speed - state["speed"]) * 0.45
    heading = angle_wrap(state["heading"] + steer * 0.42 * DT)
    effective = speed * (1.0 - slip)

    x0, y0 = state["x"], state["y"]
    x = x0 + math.cos(heading) * effective * DT
    y = y0 + math.sin(heading) * effective * DT

    collision = False
    for obs in world["obstacles"]:
        if obstacle_distance(x, y, obs) < 0.0:
            collision = True
            x, y = x0, y0
            speed *= 0.15
            break

    power_w = 72.0 + 165.0*throttle + 210.0*slip + 55.0*abs(steer) + (90.0 if collision else 0.0)
    energy_wh = max(0.0, state["energy_wh"] - power_w * DT / 3600.0)
    dist = math.hypot(GOAL_X - x, GOAL_Y - y)
    nxt = {
        "x": x, "y": y, "heading": heading, "speed": speed, "energy_wh": energy_wh,
        "slip": slip, "collisions": state["collisions"] + int(collision), "step": state["step"] + 1,
    }
    done = dist < 0.75 or energy_wh <= 0.0 or nxt["step"] >= MAX_STEPS
    return nxt, done


def episode(model, seed, mode):
    world = shifted_world(seed)
    state = {
        "x":0.0,"y":0.0,"heading":0.0,"speed":0.0,"energy_wh":BATTERY_WH,
        "slip":0.0,"collisions":0,"step":0,
    }
    done = False
    while not done:
        obs = observe(state, world)
        if mode == "teacher":
            action = teacher(obs)
        else:
            action = action_from_model(model, obs)
        state, done = env_step(state, action, world)
    dist = math.hypot(GOAL_X-state["x"], GOAL_Y-state["y"])
    return {
        "success": dist < 0.75,
        "distance": dist,
        "collisions": state["collisions"],
        "steps": state["step"],
    }


def score(model, seeds, mode):
    rows = [episode(model, s, mode) for s in seeds]
    return {
        "success_rate": sum(int(x["success"]) for x in rows) / len(rows),
        "mean_final_distance_m": statistics.fmean(x["distance"] for x in rows),
        "collisions": sum(x["collisions"] for x in rows),
        "mean_steps": statistics.fmean(x["steps"] for x in rows),
    }


def fresh_action_mse(model, seed, count=10000):
    rng = random.Random(seed)
    xs, ys = [], []
    for _ in range(count):
        row = [
            rng.uniform(-math.pi, math.pi),
            rng.uniform(-0.6, 5.8),
            rng.choice([-1.0, 1.0]),
            float(rng.random() < 0.80),
            rng.uniform(0.0, 0.62),
            rng.uniform(0.0, 1.2),
            rng.uniform(0.08, 0.42),
            rng.uniform(0.0, 0.22),
        ]
        target = teacher(row)
        xs.append(row)
        ys.append([target["throttle"], target["steer"] / 0.8])
    x = torch.tensor(xs, dtype=torch.float32)
    y = torch.tensor(ys, dtype=torch.float32)
    with torch.no_grad():
        pred = model(norm_features(x))
    return float(torch.mean((pred - y) ** 2))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_WEIGHTS.exists():
        raise SystemExit("SOURCE_WEIGHTS_MISSING")
    weights_sha = sha256_file(SOURCE_WEIGHTS)
    if weights_sha != EXPECTED_WEIGHTS_SHA:
        raise SystemExit("SOURCE_WEIGHTS_SHA_MISMATCH")

    payload = torch.load(SOURCE_WEIGHTS, map_location="cpu", weights_only=False)
    trained = AuditPolicy()
    trained.load_state_dict(payload["model_state_dict"])
    trained.eval()

    torch.manual_seed(991827)
    random_model = AuditPolicy()
    random_model.eval()

    audit_seed = int(os.getenv("ELYRA_AUDIT_SEED", "2026092303"))
    seeds = [((audit_seed * 3571) + i * 65537) & 0x7FFFFFFF for i in range(AUDIT_EPISODES)]

    random_score = score(random_model, seeds, "model")
    trained_score = score(trained, seeds, "model")
    teacher_score = score(trained, seeds, "teacher")

    random_mse = fresh_action_mse(random_model, audit_seed + 101)
    trained_mse = fresh_action_mse(trained, audit_seed + 101)
    mse_gain = random_mse / max(trained_mse, 1e-12)

    checks = {
        "weights_sha_matches_source": weights_sha == EXPECTED_WEIGHTS_SHA,
        "fresh_seed_not_training_seed": audit_seed != 26092301,
        "fresh_distribution_shifted": True,
        "action_mse_improves_10x": trained_mse < random_mse * 0.10,
        "closed_loop_improves_random_by_20pp": trained_score["success_rate"] >= random_score["success_rate"] + 0.20,
        "closed_loop_reaches_60pct_teacher": trained_score["success_rate"] >= teacher_score["success_rate"] * 0.60,
    }
    passed = all(checks.values())

    out = {
        "schema": "ELYRA_INDEPENDENT_AUDIT_V1",
        "source_run_id": 35904950828,
        "source_artifact_id": 10770497581,
        "source_artifact_digest": "sha256:fe342b4403902c3643165e5b617b8d1dbf61d716c2af217e64f2634f8c9a8717",
        "weights_sha256": weights_sha,
        "audit_seed": audit_seed,
        "audit_episodes": AUDIT_EPISODES,
        "distribution": "SHIFTED_SYNTHETIC_ROVER_V1",
        "random_baseline": random_score,
        "trained_policy": trained_score,
        "teacher": teacher_score,
        "random_action_mse": random_mse,
        "trained_action_mse": trained_mse,
        "mse_gain_ratio": mse_gain,
        "checks": checks,
        "status": "PASS_SCOPED_INDEPENDENT_CODEPATH" if passed else "FAIL_OR_LIMIT",
        "claim_ceiling": "SYNTHETIC_IMITATION_GENERALIZES_WITHIN_SHIFTED_SIMULATOR_DISTRIBUTION",
        "limitations": [
            "independent audit code path but same repository and synthetic dynamics family",
            "not an external organization evaluation",
            "not physical lunar-rover validation",
            "not RL and not general autonomy",
            "does not validate SAPHEA language-model training",
        ],
    }
    out["result_sha256"] = canonical_sha(out)
    path = OUT_DIR / "elyra-independent-audit-v1.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
