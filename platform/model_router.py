"""Fail-closed model registry plus a real, tiny CPU neural classifier.

This is intentionally not advertised as a generative LLM. It performs actual
numeric inference to choose a mission domain and records its immutable model
revision. External providers stay UNAVAILABLE until credentials and health are
proven at runtime.
"""

from __future__ import annotations

import hashlib
import math
import os
import time

from generative_backend import status as generative_status


LABELS = ("space", "math", "software", "simulation", "general")
VOCAB = (
    "lunaire", "lune", "rover", "orbite", "spatial", "fusée",
    "preuve", "théorème", "collatz", "équation", "mathématique",
    "code", "logiciel", "api", "site", "application", "python",
    "simulation", "calcul", "modèle", "trajectoire", "moteur",
)

# Five output neurons x vocabulary. These versioned weights are deliberately
# small and inspectable. Inference is a real softmax linear neural classifier.
_GROUPS = {
    "space": {"lunaire", "lune", "rover", "orbite", "spatial", "fusée"},
    "math": {"preuve", "théorème", "collatz", "équation", "mathématique"},
    "software": {"code", "logiciel", "api", "site", "application", "python"},
    "simulation": {"simulation", "calcul", "modèle", "trajectoire", "moteur"},
}
WEIGHTS = tuple(
    tuple(2.4 if token in _GROUPS.get(label, set()) else -0.18 for token in VOCAB)
    for label in LABELS
)
BIAS = (-0.15, -0.15, -0.15, -0.15, 0.10)
MODEL_REVISION = hashlib.sha256(repr((LABELS, VOCAB, WEIGHTS, BIAS)).encode()).hexdigest()


def _tokens(text: str) -> set[str]:
    clean = "".join(ch.lower() if ch.isalnum() or ch in "éèêàùçîïô-" else " " for ch in text)
    return set(clean.split())


def infer(text: str) -> dict:
    started = time.perf_counter()
    tokens = _tokens(text)
    vector = [1.0 if word in tokens else 0.0 for word in VOCAB]
    logits = [BIAS[i] + sum(w * x for w, x in zip(WEIGHTS[i], vector)) for i in range(len(LABELS))]
    peak = max(logits)
    exps = [math.exp(value - peak) for value in logits]
    total = sum(exps)
    probabilities = [value / total for value in exps]
    index = max(range(len(LABELS)), key=probabilities.__getitem__)
    return {
        "provider": "local",
        "model_id": "CEREBRON-ROUTER-NN-V1",
        "revision": MODEL_REVISION,
        "runtime": "python-cpu",
        "label": LABELS[index],
        "confidence": round(probabilities[index], 6),
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "scores": {label: round(probabilities[i], 6) for i, label in enumerate(LABELS)},
    }


def catalog() -> list[dict]:
    local_probe = infer("concevoir un rover lunaire")
    hf_token = bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN"))
    return [
        {
            "provider": "local",
            "model_id": "CEREBRON-ROUTER-NN-V1",
            "revision": MODEL_REVISION,
            "license": "MIT",
            "runtime": "python-cpu",
            "endpoint": "/api/models/infer",
            "health": "PASS",
            "latency_ms": local_probe["latency_ms"],
            "cost": 0,
            "context": len(VOCAB),
            "capabilities": ["mission-classification", "farm-routing"],
            "status": "ACTIVE_WORKER",
            "limitations": "Non-generative classifier; not an LLM.",
        },
        {
            **generative_status(),
            "endpoint": "/api/models/generate",
            "latency_ms": None,
            "context": 32768,
            "capabilities": ["text-generation", "compact-general-assistance"],
        },
        {
            "provider": "huggingface-remote",
            "model_id": None,
            "revision": None,
            "license": None,
            "runtime": "remote-inference",
            "endpoint": None,
            "health": "NOT_PROBED",
            "latency_ms": None,
            "cost": "unknown",
            "context": None,
            "capabilities": [],
            "status": "CONFIGURED_NOT_QUALIFIED" if hf_token else "UNAVAILABLE",
        },
    ]

