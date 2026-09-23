from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
WEIGHTS_PATH = HERE / "models" / "elyra-imitation-policy-v1.pt"
WEIGHTS_SHA256 = "b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601"
POLICY_NAME = "ELYRA_IMITATION_POLICY_V1"
TRAINING_RUN = 35904950828
AUDIT_RUN = 35905952407

_LOCK = threading.Lock()
_MODEL = None


class ElyraPolicyError(RuntimeError):
    pass


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status() -> dict:
    enabled = os.getenv("CEREBRON_ENABLE_ELYRA_POLICY", "").strip() == "1"
    deps = importlib.util.find_spec("torch") is not None
    weights_present = WEIGHTS_PATH.exists()
    weights_valid = weights_present and _sha256(WEIGHTS_PATH) == WEIGHTS_SHA256
    if not weights_present:
        state = "WEIGHTS_MISSING"
    elif not weights_valid:
        state = "WEIGHTS_SHA_MISMATCH"
    elif not enabled:
        state = "CONFIGURED_DISABLED"
    elif not deps:
        state = "RUNTIME_DEPENDENCY_MISSING"
    else:
        state = "READY_TO_LOAD"
    return {
        "policy": POLICY_NAME,
        "status": "ACTIVE_WORKER" if state == "READY_TO_LOAD" else state,
        "enabled": enabled,
        "dependencies_available": deps,
        "weights_present": weights_present,
        "weights_valid": weights_valid,
        "weights_sha256": WEIGHTS_SHA256,
        "training_run": TRAINING_RUN,
        "independent_audit_run": AUDIT_RUN,
        "scope": "SYNTHETIC_ROVER_POLICY_ONLY",
        "claim_ceiling": "E3_SIMULATION_POLICY_NOT_PHYSICAL_VALIDATION",
    }


def _load():
    global _MODEL
    st = status()
    if not st["weights_present"]:
        raise ElyraPolicyError("ELYRA_WEIGHTS_MISSING")
    if not st["weights_valid"]:
        raise ElyraPolicyError("ELYRA_WEIGHTS_SHA_MISMATCH")
    if not st["enabled"]:
        raise ElyraPolicyError("ELYRA_POLICY_DISABLED")
    if not st["dependencies_available"]:
        raise ElyraPolicyError("ELYRA_TORCH_MISSING")

    with _LOCK:
        if _MODEL is None:
            import torch
            nn = torch.nn

            class Policy(nn.Module):
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
                    throttle = torch.sigmoid(raw[:, :1])
                    steer = torch.tanh(raw[:, 1:2])
                    return torch.cat([throttle, steer], dim=1)

            payload = torch.load(WEIGHTS_PATH, map_location="cpu")
            if payload.get("schema") != POLICY_NAME:
                raise ElyraPolicyError("ELYRA_WEIGHTS_SCHEMA_MISMATCH")
            if payload.get("architecture") != {"input": 8, "hidden": [64, 64, 32], "output": 2}:
                raise ElyraPolicyError("ELYRA_ARCHITECTURE_MISMATCH")
            model = Policy()
            model.load_state_dict(payload["model_state_dict"])
            model.eval()
            _MODEL = model
    return _MODEL


def infer(features: list[float]) -> dict:
    if not isinstance(features, list) or len(features) != 8:
        raise ElyraPolicyError("ELYRA_FEATURE_VECTOR_MUST_HAVE_8_VALUES")
    try:
        values = [float(x) for x in features]
    except (TypeError, ValueError) as exc:
        raise ElyraPolicyError("ELYRA_FEATURE_VECTOR_INVALID") from exc
    if not all(math.isfinite(x) for x in values):
        raise ElyraPolicyError("ELYRA_FEATURE_VECTOR_NONFINITE")

    model = _load()
    import torch
    started = time.perf_counter()
    x = torch.tensor([values], dtype=torch.float32)
    scales = torch.tensor([math.pi, 5.0, 1.0, 1.0, 0.62, 1.2, 0.35, 0.18], dtype=x.dtype)
    x = x / scales
    x[:, 1] = torch.clamp(x[:, 1], -0.25, 1.25)
    with torch.no_grad():
        raw = model(x)[0]
    raw_throttle = max(0.0, min(1.0, float(raw[0])))
    throttle = min((0.32, 0.52, 0.78), key=lambda v: abs(v - raw_throttle))
    steer = max(-0.8, min(0.8, float(raw[1]) * 0.8))
    core = {
        "schema": "ELYRA_POLICY_INFERENCE_V1",
        "policy": POLICY_NAME,
        "weights_sha256": WEIGHTS_SHA256,
        "features": values,
        "action": {"throttle": throttle, "steer": steer},
        "latency_s": round(time.perf_counter() - started, 6),
        "claim_ceiling": "E3_SIMULATION_POLICY_NOT_PHYSICAL_VALIDATION",
    }
    core["output_sha256"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return core


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="JSON list of 8 floats")
    args=ap.parse_args()
    result=infer(json.loads(args.features))
    print(json.dumps(result))


if __name__=="__main__":
    main()
