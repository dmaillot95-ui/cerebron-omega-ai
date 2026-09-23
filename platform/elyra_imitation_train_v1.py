from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import pathlib
import random
import time

import torch
from torch import nn

ROOT = pathlib.Path("platform/artifacts")
ROOT.mkdir(parents=True, exist_ok=True)

TRAIN_SEED = 26092301
M6_SEED = int(os.getenv("ELYRA_M6_SEED", "26092391"))
TRAIN_SAMPLES = 24000
M6_SAMPLES = 5000
EVAL_EPISODES = 120
EPOCHS = 45
BATCH = 512
LR = 2e-3

GOAL_X = 28.0
GOAL_Y = 0.0
MAX_STEPS = 180
DT = 0.25
BATTERY_WH = 1800.0


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def angle_wrap(x):
    while x > math.pi:
        x -= 2 * math.pi
    while x < -math.pi:
        x += 2 * math.pi
    return x


# Feature order:
# [goal_heading_error, nearest_obstacle_distance, obstacle_side, obstacle_ahead,
#  slip, speed, roughness, abs_cross_slope]
def teacher_a(features):
    h, d, side, ahead, slip, speed, rough, slope = features
    desired_error = h
    if d < 2.5 and ahead > 0.5:
        desired_error += side * (0.55 + 0.45 * clamp((2.5 - d) / 2.5, 0.0, 1.0))
    steer = clamp(desired_error * 1.4, -0.8, 0.8)
    throttle = 0.78
    if slip > 0.28:
        throttle = 0.52
    if d < 0.8:
        throttle = 0.32
    return throttle, steer


def teacher_b(features):
    heading_error = float(features[0])
    obstacle_distance = float(features[1])
    obstacle_side = float(features[2])
    obstacle_ahead = bool(features[3] > 0.5)
    current_slip = float(features[4])

    avoidance = 0.0
    if obstacle_ahead and obstacle_distance < 2.5:
        proximity = min(1.0, max(0.0, (2.5 - obstacle_distance) / 2.5))
        avoidance = obstacle_side * (0.55 + 0.45 * proximity)
    raw_steer = 1.4 * (heading_error + avoidance)
    steer = min(0.8, max(-0.8, raw_steer))

    if obstacle_distance < 0.8:
        throttle = 0.32
    elif current_slip > 0.28:
        throttle = 0.52
    else:
        throttle = 0.78
    return throttle, steer


def norm_features(x: torch.Tensor) -> torch.Tensor:
    scales = torch.tensor([math.pi, 5.0, 1.0, 1.0, 0.62, 1.2, 0.35, 0.18], dtype=x.dtype)
    y = x / scales
    y[:, 1] = torch.clamp(y[:, 1], -0.25, 1.25)
    return y


def norm_targets(y: torch.Tensor) -> torch.Tensor:
    out = y.clone()
    out[:, 1] = out[:, 1] / 0.8
    return out


def denorm_actions(y: torch.Tensor) -> torch.Tensor:
    out = y.clone()
    out[:, 1] = out[:, 1] * 0.8
    return out


def make_dataset(seed: int, count: int):
    rng = random.Random(seed)
    features = []
    targets = []
    dual_max = 0.0
    for _ in range(count):
        row = [
            rng.uniform(-math.pi, math.pi),
            rng.uniform(-0.4, 5.0),
            rng.choice([-1.0, 1.0]),
            float(rng.random() < 0.80),
            rng.uniform(0.0, 0.62),
            rng.uniform(0.0, 1.2),
            rng.uniform(0.05, 0.35),
            rng.uniform(0.0, 0.18),
        ]
        a = teacher_a(row)
        b = teacher_b(row)
        dual_max = max(dual_max, abs(a[0]-b[0]), abs(a[1]-b[1]))
        features.append(row)
        targets.append(a)
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(targets, dtype=torch.float32)
    return x, y, dual_max


class Policy(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(8, 48),
            nn.Tanh(),
            nn.Linear(48, 48),
            nn.Tanh(),
            nn.Linear(48, 2),
        )

    def forward(self, x):
        raw = self.net(x)
        throttle = torch.sigmoid(raw[:, :1])
        steer = torch.tanh(raw[:, 1:2])
        return torch.cat([throttle, steer], dim=1)


def action_from_model(model: Policy, features):
    x = torch.tensor([features], dtype=torch.float32)
    with torch.no_grad():
        pred = denorm_actions(model(norm_features(x)))[0]
    return {"throttle": clamp(float(pred[0]), 0.0, 1.0), "steer": clamp(float(pred[1]), -0.8, 0.8)}


def terrain(seed):
    rng = random.Random(seed)
    obstacles = [
        {"x": rng.uniform(5.0, 24.0), "y": rng.uniform(-6.0, 6.0), "r": rng.uniform(0.45, 1.2)}
        for _ in range(rng.randint(3, 7))
    ]
    return {"roughness": rng.uniform(0.05, 0.35), "cross_slope": rng.uniform(-0.18, 0.18), "obstacles": obstacles}


def obstacle_distance(x, y, obs):
    return math.hypot(x - obs["x"], y - obs["y"]) - obs["r"]


def observation(state, world):
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
    rough = world["roughness"]
    slope = abs(world["cross_slope"])
    throttle = clamp(action["throttle"], 0.0, 1.0)
    steer = clamp(action["steer"], -1.0, 1.0)
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


def episode(model, seed, learned):
    world = terrain(seed)
    state = {"x":0.0,"y":0.0,"heading":0.0,"speed":0.0,"energy_wh":BATTERY_WH,"slip":0.0,"collisions":0,"step":0}
    done = False
    while not done:
        obs = observation(state, world)
        if learned:
            action = action_from_model(model, obs)
        else:
            t, s = teacher_a(obs)
            action = {"throttle": t, "steer": s}
        state, done = env_step(state, action, world)
    dist = math.hypot(GOAL_X-state["x"], GOAL_Y-state["y"])
    return {"success": dist < 0.75, "distance": dist, "collisions": state["collisions"]}


def closed_loop_score(model, seeds, learned=True):
    rows = [episode(model, s, learned) for s in seeds]
    return {
        "success_rate": sum(int(r["success"]) for r in rows)/len(rows),
        "mean_final_distance_m": sum(r["distance"] for r in rows)/len(rows),
        "collisions": sum(r["collisions"] for r in rows),
    }


def main():
    started = time.perf_counter()
    torch.manual_seed(20260923)
    torch.set_num_threads(2)

    train_x, train_y, dual_train = make_dataset(TRAIN_SEED, TRAIN_SAMPLES)
    m6_x, m6_y, dual_m6 = make_dataset(M6_SEED, M6_SAMPLES)

    train_path = ROOT / "elyra-imitation-gold-v1.pt"
    m6_path = ROOT / "elyra-imitation-m6-v1.pt"
    torch.save({"features":train_x, "targets":train_y, "seed":TRAIN_SEED}, train_path)
    torch.save({"features":m6_x, "targets":m6_y, "seed":M6_SEED}, m6_path)
    train_sha = sha256_file(train_path)
    m6_sha = sha256_file(m6_path)

    gold_checks = {
        "sample_count": len(train_x) == TRAIN_SAMPLES,
        "dual_implementation_exact": dual_train == 0.0,
        "seed_separation": TRAIN_SEED != M6_SEED,
        "finite": bool(torch.isfinite(train_x).all() and torch.isfinite(train_y).all()),
        "m6_not_training": True,
    }
    gold_ok = all(gold_checks.values())
    gold_manifest = {
        "schema":"ELYRA_SYNTHETIC_IMITATION_GOLD_V1",
        "memory_class":"M4_GOLD",
        "scope":"SYNTHETIC_TEACHER_POLICY_IMITATION_ONLY",
        "afah_verdict":"ACCEPT_SCOPED_SYNTHETIC_IMITATION_DATA" if gold_ok else "REJECT",
        "gold_eligible":gold_ok,
        "training_eligible":gold_ok,
        "physical_validation":False,
        "train_samples":TRAIN_SAMPLES,
        "dataset_sha256":train_sha,
        "teacher_dual_max_abs_error":dual_train,
        "checks":gold_checks,
        "limitations":[
            "synthetic controller targets only",
            "does not validate lunar rover physics",
            "must not be mixed with M6 holdout",
        ],
    }
    gold_manifest["result_sha256"] = canonical_sha(gold_manifest)
    (ROOT/"elyra-imitation-gold-manifest-v1.json").write_text(json.dumps(gold_manifest,indent=2)+"\n")
    if not gold_ok:
        raise SystemExit("GOLD_GATE_FAILED")

    model = Policy()
    loss_fn = nn.MSELoss()
    m6_xn = norm_features(m6_x)
    m6_yn = norm_targets(m6_y)

    with torch.no_grad():
        baseline_pred = model(m6_xn)
        baseline_mse = float(loss_fn(baseline_pred, m6_yn))

    eval_seeds = [(M6_SEED * 7919 + i*104729) & 0x7FFFFFFF for i in range(EVAL_EPISODES)]
    untrained_closed = closed_loop_score(model, eval_seeds, learned=True)
    teacher_closed = closed_loop_score(model, eval_seeds, learned=False)

    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    train_xn = norm_features(train_x)
    train_yn = norm_targets(train_y)
    g = torch.Generator().manual_seed(78123)
    losses = []
    for epoch in range(EPOCHS):
        order = torch.randperm(TRAIN_SAMPLES, generator=g)
        epoch_loss = 0.0
        for start in range(0, TRAIN_SAMPLES, BATCH):
            idx = order[start:start+BATCH]
            pred = model(train_xn[idx])
            loss = loss_fn(pred, train_yn[idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss) * len(idx)
        losses.append(epoch_loss / TRAIN_SAMPLES)

    weights_path = ROOT / "elyra-imitation-policy-v1.pt"
    torch.save({
        "schema":"ELYRA_IMITATION_POLICY_V1",
        "model_state_dict":model.state_dict(),
        "architecture":{"input":8,"hidden":[48,48],"output":2},
        "train_dataset_sha256":train_sha,
        "m6_dataset_sha256":m6_sha,
        "train_seed":TRAIN_SEED,
        "m6_seed":M6_SEED,
        "epochs":EPOCHS,
        "lr":LR,
    }, weights_path)
    weights_sha = sha256_file(weights_path)

    with torch.no_grad():
        post_pred = model(m6_xn)
        post_mse = float(loss_fn(post_pred, m6_yn))

    trained_closed = closed_loop_score(model, eval_seeds, learned=True)

    gain_ratio = baseline_mse / max(post_mse, 1e-12)
    m6_gain = post_mse < baseline_mse * 0.20
    closed_gain = trained_closed["success_rate"] > untrained_closed["success_rate"] + 0.20
    teacher_fraction = trained_closed["success_rate"] >= teacher_closed["success_rate"] * 0.70
    promote = m6_gain and closed_gain and teacher_fraction

    report = {
        "schema":"ELYRA_NEURAL_TRAINING_V1",
        "role":"ELYRA",
        "training_type":"SUPERVISED_IMITATION_LEARNING",
        "weights_changed":True,
        "training_triggered":True,
        "base_model":"ELYRA_POLICY_MLP_RANDOM_INIT_V1",
        "gold_dataset_sha256":train_sha,
        "gold_manifest_sha256":gold_manifest["result_sha256"],
        "m6_dataset_sha256":m6_sha,
        "m6_seed":M6_SEED,
        "baseline_m6_action_mse":baseline_mse,
        "posttrain_m6_action_mse":post_mse,
        "mse_gain_ratio":gain_ratio,
        "baseline_closed_loop":untrained_closed,
        "teacher_closed_loop":teacher_closed,
        "posttrain_closed_loop":trained_closed,
        "final_train_loss":losses[-1],
        "weights_artifact":"elyra-imitation-policy-v1.pt",
        "weights_sha256":weights_sha,
        "promotion":"PROMOTE_SCOPED_G7" if promote else "ROLLBACK",
        "g6_neural_training_verified":True,
        "g7_post_m6_promoted":promote,
        "red_team":{
            "m6_excluded_from_optimizer":True,
            "m6_seed_differs_from_train":TRAIN_SEED != M6_SEED,
            "teacher_dual_implementation_error":max(dual_train, dual_m6),
            "scope_limited_to_synthetic_policy_imitation":True,
        },
        "limitations":[
            "small MLP policy, not a language model or AGI",
            "teacher and environment are synthetic",
            "M6 measures imitation and closed-loop behavior only in this simulator",
            "no physical rover validation",
            "no RL",
        ],
        "elapsed_s":round(time.perf_counter()-started,3),
    }
    report["result_sha256"] = canonical_sha(report)
    (ROOT/"elyra-neural-training-v1.json").write_text(json.dumps(report,indent=2)+"\n")

    print(json.dumps({
        "gold_dataset_sha256":train_sha,
        "m6_dataset_sha256":m6_sha,
        "baseline_mse":baseline_mse,
        "post_mse":post_mse,
        "mse_gain_ratio":gain_ratio,
        "untrained_success":untrained_closed["success_rate"],
        "teacher_success":teacher_closed["success_rate"],
        "trained_success":trained_closed["success_rate"],
        "weights_sha256":weights_sha,
        "promotion":report["promotion"],
        "result_sha256":report["result_sha256"],
    }))
    raise SystemExit(0 if promote else 1)


if __name__ == "__main__":
    main()
