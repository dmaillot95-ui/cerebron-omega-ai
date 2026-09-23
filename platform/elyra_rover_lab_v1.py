from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import random
import statistics
import time

EPISODES = 500
MAX_STEPS = 180
DT = 0.25
GOAL_X = 28.0
GOAL_Y = 0.0
BATTERY_WH = 1800.0
REPLAY = pathlib.Path("platform/artifacts/elyra-rover-replay-v1.jsonl")
SUMMARY = pathlib.Path("platform/artifacts/elyra-rover-lab-v1.json")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def angle_wrap(x):
    while x > math.pi:
        x -= 2 * math.pi
    while x < -math.pi:
        x += 2 * math.pi
    return x


def terrain(seed: int):
    rng = random.Random(seed)
    obstacles = []
    for _ in range(rng.randint(3, 7)):
        obstacles.append({
            "x": rng.uniform(5.0, 24.0),
            "y": rng.uniform(-6.0, 6.0),
            "r": rng.uniform(0.45, 1.2),
        })
    return {
        "roughness": rng.uniform(0.05, 0.35),
        "cross_slope": rng.uniform(-0.18, 0.18),
        "obstacles": obstacles,
    }


def obstacle_distance(x, y, obs):
    return math.hypot(x - obs["x"], y - obs["y"]) - obs["r"]


def controller(state, world):
    desired = math.atan2(GOAL_Y - state["y"], GOAL_X - state["x"])
    nearest = min(world["obstacles"], key=lambda o: obstacle_distance(state["x"], state["y"], o))
    d = obstacle_distance(state["x"], state["y"], nearest)
    if d < 2.5 and nearest["x"] > state["x"] - 0.5:
        side = -1.0 if nearest["y"] >= state["y"] else 1.0
        desired += side * (0.55 + 0.45 * clamp((2.5 - d) / 2.5, 0.0, 1.0))
    heading_error = angle_wrap(desired - state["heading"])
    steer = clamp(heading_error * 1.4, -0.8, 0.8)
    throttle = 0.78
    if state["slip"] > 0.28:
        throttle = 0.52
    if d < 0.8:
        throttle = 0.32
    return {"throttle": throttle, "steer": steer}


def step(state, action, world):
    rough = world["roughness"]
    slope = abs(world["cross_slope"])
    throttle = clamp(action["throttle"], 0.0, 1.0)
    steer = clamp(action["steer"], -1.0, 1.0)

    slip = clamp(
        0.035 + rough * 0.55 + slope * 0.35 + throttle * 0.07 + abs(steer) * 0.05,
        0.0,
        0.62,
    )
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

    traction_w = 72.0 + 165.0 * throttle + 210.0 * slip + 55.0 * abs(steer)
    if collision:
        traction_w += 90.0
    energy_delta = traction_w * DT / 3600.0
    energy_wh = max(0.0, state["energy_wh"] - energy_delta)

    prev_dist = math.hypot(GOAL_X - x0, GOAL_Y - y0)
    dist = math.hypot(GOAL_X - x, GOAL_Y - y)
    progress = prev_dist - dist
    reward = progress * 8.0 - energy_delta * 0.08 - slip * 0.05 - (2.0 if collision else 0.0)

    new_state = {
        "x": x,
        "y": y,
        "heading": heading,
        "speed": speed,
        "energy_wh": energy_wh,
        "slip": slip,
        "collisions": state["collisions"] + int(collision),
        "step": state["step"] + 1,
    }
    done = dist < 0.75 or energy_wh <= 0.0 or new_state["step"] >= MAX_STEPS
    return new_state, reward, done, collision


def run_episode(seed: int, replay_handle):
    world = terrain(seed)
    state = {
        "x": 0.0,
        "y": 0.0,
        "heading": 0.0,
        "speed": 0.0,
        "energy_wh": BATTERY_WH,
        "slip": 0.0,
        "collisions": 0,
        "step": 0,
    }
    total_reward = 0.0
    transitions = 0
    done = False
    while not done:
        action = controller(state, world)
        next_state, reward, done, collision = step(state, action, world)
        row = {
            "episode_seed": seed,
            "t": transitions,
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "collision": collision,
        }
        replay_handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        total_reward += reward
        transitions += 1
        state = next_state

    final_distance = math.hypot(GOAL_X - state["x"], GOAL_Y - state["y"])
    return {
        "seed": seed,
        "success": final_distance < 0.75,
        "steps": transitions,
        "reward": total_reward,
        "collisions": state["collisions"],
        "energy_used_wh": BATTERY_WH - state["energy_wh"],
        "final_distance_m": final_distance,
        "mean_terminal_slip": state["slip"],
    }


def main():
    started = time.perf_counter()
    base_seed = int(os.getenv("ELYRA_LAB_SEED", "20260923"))
    REPLAY.parent.mkdir(parents=True, exist_ok=True)
    episodes = []
    with REPLAY.open("w", encoding="utf-8") as handle:
        for i in range(EPISODES):
            episode_seed = (base_seed * 1009 + i * 9176) & 0x7FFFFFFF
            episodes.append(run_episode(episode_seed, handle))

    replay_bytes = REPLAY.read_bytes()
    replay_sha = sha256_bytes(replay_bytes)
    successes = sum(int(e["success"]) for e in episodes)
    collisions = sum(e["collisions"] for e in episodes)
    rewards = [e["reward"] for e in episodes]
    energy = [e["energy_used_wh"] for e in episodes]
    distances = [e["final_distance_m"] for e in episodes]

    checks = {
        "episode_count": len(episodes) == EPISODES,
        "all_finite": all(math.isfinite(v) for v in rewards + energy + distances),
        "nonempty_replay": len(replay_bytes) > 0,
        "positive_energy_use": all(v > 0 for v in energy),
        "bounded_collisions": collisions <= EPISODES * MAX_STEPS,
    }
    verified = all(checks.values())

    summary = {
        "schema": "ELYRA_ROVER_LAB_V1",
        "role": "ELYRA",
        "status": "SIMULATION_EXECUTED_VERIFIED" if verified else "SIMULATION_CHECK_FAILED",
        "maturity": "E3_SIMULATION_VERIFIED" if verified else "E2_OR_LOWER",
        "episodes": EPISODES,
        "max_steps": MAX_STEPS,
        "dt_s": DT,
        "base_seed": base_seed,
        "controller": "deterministic_obstacle_aware_baseline",
        "training_triggered": False,
        "weights_changed": False,
        "replay_sha256": replay_sha,
        "replay_bytes": len(replay_bytes),
        "metrics": {
            "successes": successes,
            "success_rate": successes / EPISODES,
            "total_collisions": collisions,
            "mean_reward": statistics.fmean(rewards),
            "median_reward": statistics.median(rewards),
            "mean_energy_used_wh": statistics.fmean(energy),
            "mean_final_distance_m": statistics.fmean(distances),
        },
        "checks": checks,
        "limitations": [
            "synthetic CPU rover environment",
            "deterministic hand-written controller; no learned policy",
            "terrain/contact/slip model is simplified and uncalibrated",
            "E3 simulation does not imply real lunar rover performance",
            "replay is eligible only as candidate data, not GOLD training data by default",
        ],
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    summary["result_sha256"] = sha256_bytes(
        json.dumps(summary, sort_keys=True, separators=(",", ":")).encode()
    )
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    raise SystemExit(0 if verified else 1)


if __name__ == "__main__":
    main()
