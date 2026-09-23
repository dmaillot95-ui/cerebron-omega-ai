from __future__ import annotations

import json
import pathlib
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from generative_backend import GenerativeBackendError, generate as generative_generate, status as generative_status
from model_router import infer

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "saphea-micro-v1.json"
DB = pathlib.Path(__file__).resolve().parent / "data" / "cerebron.db"

PRIMARY_BY_ROUTE = {
    "math": "SM02",
    "software": "SM05",
    "space": "SM08",
    "simulation": "SM08",
    "general": None,
}
BASE_GENERATOR = "BASE_QWEN"
MEMORY_HINTS = {"memory", "mémoire", "remember", "checkpoint", "agora", "previous", "précédent", "rappel"}
ROLE_INSTRUCTIONS = {
    "SM02": "Act as a math/logic specialist. Separate proof from heuristic and calculation from proof. Obey any explicit output-format constraint exactly; if the user requests only one number, token, or word, output only that.",
    "SM05": "Act as a code/calculation specialist. Be explicit about what is executed versus proposed. Obey any explicit output-format constraint exactly; if the user requests only one number, token, or word, output only that.",
    "SM08": "Act as a physics/engineering specialist. Separate calculation, simulation, test and validation. Obey any explicit output-format constraint exactly; if the user requests only one number, token, or word, output only that.",
    "SM18": "Act as a concise general synthesis worker. Do not invent evidence or execution. Obey any explicit output-format constraint exactly; if the user requests only one number, token, or word, output only that.",
}


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zA-ZÀ-ÿ0-9_-]+", text.lower()) if len(w) >= 4}


def memory_retrieve(prompt: str, limit: int = 5) -> dict:
    if not DB.exists():
        return {"unit": "SM11", "status": "EXECUTED_NO_LOCAL_DB", "matches": []}
    words = _words(prompt)
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(
            "SELECT capsule_id,kind,state,content,provenance,sha,created_at FROM agora ORDER BY created_at DESC LIMIT 200"
        ).fetchall()]
    except sqlite3.Error as exc:
        return {"unit": "SM11", "status": "NON_EXECUTED", "error": str(exc), "matches": []}
    finally:
        try:
            con.close()
        except Exception:
            pass
    scored = []
    for row in rows:
        hay = (str(row.get("content","")) + " " + str(row.get("provenance",""))).lower()
        score = sum(1 for word in words if word in hay)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: (item[0], item[1].get("created_at", 0)), reverse=True)
    return {
        "unit": "SM11",
        "status": "EXECUTED",
        "method": "local-sqlite-agora-keyword-retrieval",
        "matches": [row for _, row in scored[:limit]],
    }


def red_team(generation: dict | None) -> dict:
    text = str((generation or {}).get("generation", ""))
    lower = text.lower()
    risky = [term for term in ("proven", "validated", "certified", "physically verified", "run id", "artifact") if term in lower]
    return {
        "unit": "SM15",
        "status": "EXECUTED",
        "method": "deterministic-redteam-v1",
        "risk_terms": risky,
        "shared_model_independence": False,
        "claim_ceiling": "MODEL_OUTPUT_UNVERIFIED" if generation else "NO_MODEL_OUTPUT",
        "verdict": "REVIEW_REQUIRED" if risky else ("BOUNDED_OUTPUT" if generation else "NO_GENERATION"),
    }


def fusion(prompt: str, route: dict, generation: dict | None, memory: dict, audit: dict) -> dict:
    answer = (generation or {}).get("generation")
    return {
        "unit": "SM18",
        "status": "EXECUTED",
        "method": "deterministic-fusion-v1",
        "answer": answer,
        "route": route.get("label"),
        "memory_matches": len(memory.get("matches", [])),
        "audit_verdict": audit["verdict"],
        "claim_ceiling": audit["claim_ceiling"],
        "limitations": [
            "SAPHEA MICRO logical workers are not automatically independent neural models",
            "SM02/SM05/SM08 share the same Qwen base model when used",
            "final model text remains unverified unless external evidence tasks validate it",
        ],
    }


def plan(prompt: str, route: dict | None = None) -> dict:
    route = route or infer(prompt)
    primary = PRIMARY_BY_ROUTE.get(route["label"])
    selected = ["SM00"]
    if _words(prompt) & MEMORY_HINTS:
        selected.append("SM11")
    if primary and primary not in selected:
        selected.append(primary)
    selected.extend(["SM15", "SM18"])
    selected = list(dict.fromkeys(selected))
    gen = generative_status()
    units = {u["id"]: u for u in registry()["units"]}
    readiness = {}
    for uid in selected:
        unit = units[uid]
        if unit.get("model_id") == "Qwen/Qwen2.5-0.5B-Instruct":
            readiness[uid] = "READY" if gen["status"] == "ACTIVE_WORKER" else "RUNTIME_GATED"
        else:
            readiness[uid] = "READY"
    model_needed = primary is not None or route["label"] == "general"
    return {
        "schema": "CEREBRON_COALITION_PLAN_V1",
        "strategy": "SEARCH_GENERATE_VERIFY_MINIMAL_USEFUL_COALITION",
        "route": route,
        "primary": primary or BASE_GENERATOR,
        "selected_units": selected,
        "readiness": readiness,
        "base_generator_readiness": "READY" if gen["status"] == "ACTIVE_WORKER" else "RUNTIME_GATED",
        "logical_unit_count": len(selected),
        "independent_model_count": 1 if model_needed and gen["status"] == "ACTIVE_WORKER" else 0,
        "shared_dependencies": ["Qwen/Qwen2.5-0.5B-Instruct"] if model_needed else [],
        "warning": "Multiple role calls to the same base model are correlated and must not be counted as independent evidence.",
    }


def _generate_for_unit(unit_id: str, prompt: str) -> dict:
    if generative_status()["status"] != "ACTIVE_WORKER":
        return {"unit": unit_id, "status": "NON_EXECUTED", "error": generative_status()["status"]}
    instruction = ROLE_INSTRUCTIONS[unit_id]
    try:
        result = generative_generate(instruction + "\n\nUser request:\n" + prompt)
        return {"unit": unit_id, "status": "MODEL_EXECUTED", **result}
    except GenerativeBackendError as exc:
        return {"unit": unit_id, "status": "NON_EXECUTED", "error": str(exc)}


def _generate_base(prompt: str) -> dict:
    if generative_status()["status"] != "ACTIVE_WORKER":
        return {"unit": BASE_GENERATOR, "status": "NON_EXECUTED", "error": generative_status()["status"]}
    try:
        result = generative_generate(prompt)
        return {"unit": BASE_GENERATOR, "status": "MODEL_EXECUTED", **result}
    except GenerativeBackendError as exc:
        return {"unit": BASE_GENERATOR, "status": "NON_EXECUTED", "error": str(exc)}


def execute(prompt: str) -> dict:
    prompt = str(prompt).strip()
    if not prompt:
        raise ValueError("prompt required")

    route = infer(prompt)
    coalition = plan(prompt, route=route)
    primary = coalition["primary"]
    memory_selected = "SM11" in coalition["selected_units"]

    generator = _generate_base if primary == BASE_GENERATOR else lambda value: _generate_for_unit(primary, value)
    if memory_selected:
        with ThreadPoolExecutor(max_workers=2) as pool:
            memory_future = pool.submit(memory_retrieve, prompt)
            generation_future = pool.submit(generator, prompt)
            memory = memory_future.result()
            generation = generation_future.result()
    else:
        memory = {"unit": "SM11", "status": "NOT_SELECTED", "matches": []}
        generation = generator(prompt)

    audit = red_team(generation if generation.get("generation") else None)
    fused = fusion(prompt, route, generation if generation.get("generation") else None, memory, audit)
    workers = {
        "SM00": {"unit": "SM00", "status": "EXECUTED", "result": route},
        primary: generation,
        "SM15": audit,
        "SM18": fused,
    }
    if memory_selected:
        workers["SM11"] = memory

    return {
        "schema": "CEREBRON_COALITION_EXECUTION_V1",
        "status": "COMPLETED" if fused.get("answer") else "ROUTED_ONLY",
        "plan": coalition,
        "workers": workers,
        "answer": fused.get("answer"),
        "claim_ceiling": fused["claim_ceiling"],
    }
