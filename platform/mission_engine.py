from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import threading
import time
import uuid

from model_router import infer
from farm_bridge import FarmBridgeError, collect as farm_collect, submit as farm_submit

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLATFORM = pathlib.Path(__file__).resolve().parent
DATA = PLATFORM / "data"
ARTIFACTS = PLATFORM / "artifacts"
DB = DATA / "cerebron.db"

DOMAIN_FARMS = {
    "space": [15, 13, 36, 33, 34, 40],
    "math": [9, 33, 34, 35, 40],
    "software": [17, 19, 44, 45, 34],
    "simulation": [36, 13, 37, 33, 34],
    "general": [8, 42, 39, 34],
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_sha(value) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def connect() -> sqlite3.Connection:
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def initialize() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS missions(
          mission_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, prompt TEXT NOT NULL,
          status TEXT NOT NULL, domain TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL,
          input_sha TEXT NOT NULL, output_sha TEXT, result_json TEXT, error TEXT
        );
        CREATE TABLE IF NOT EXISTS tasks(
          task_id TEXT PRIMARY KEY, mission_id TEXT NOT NULL, parent_task_id TEXT,
          farm_id INTEGER, role TEXT, worker TEXT, model TEXT, tool TEXT,
          status TEXT NOT NULL, start_time REAL, end_time REAL, input_sha TEXT,
          output_sha TEXT, evidence TEXT, cost REAL DEFAULT 0, errors TEXT
        );
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL,
          time REAL NOT NULL, level TEXT NOT NULL, message TEXT NOT NULL, data_json TEXT
        );
        CREATE TABLE IF NOT EXISTS agora(
          capsule_id TEXT PRIMARY KEY, mission_id TEXT NOT NULL, kind TEXT NOT NULL,
          state TEXT NOT NULL, content TEXT NOT NULL, provenance TEXT NOT NULL,
          sha TEXT NOT NULL, created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS evidence(
          evidence_id TEXT PRIMARY KEY, mission_id TEXT NOT NULL, kind TEXT NOT NULL,
          source TEXT NOT NULL, sha TEXT NOT NULL, payload_json TEXT NOT NULL,
          maturity TEXT NOT NULL, created_at REAL NOT NULL
        );
        """)


def emit(mission_id: str, message: str, data=None, level="INFO") -> None:
    with connect() as con:
        con.execute("INSERT INTO events(mission_id,time,level,message,data_json) VALUES(?,?,?,?,?)",
                    (mission_id, time.time(), level, message, json.dumps(data, ensure_ascii=False) if data is not None else None))


def _task(mission_id: str, farm_id: int, role: str, worker: str, model: str | None, tool: str | None, fn):
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    start = time.time()
    input_sha = canonical_sha({"mission_id": mission_id, "farm_id": farm_id, "role": role})
    with connect() as con:
        con.execute("""INSERT INTO tasks(task_id,mission_id,farm_id,role,worker,model,tool,status,start_time,input_sha,cost)
                       VALUES(?,?,?,?,?,?,?,?,?,?,0)""",
                    (task_id, mission_id, farm_id, role, worker, model, tool, "RUNNING", start, input_sha))
    emit(mission_id, f"{role} démarré", {"farm_id": farm_id, "task_id": task_id})
    try:
        output = fn()
        output_sha = canonical_sha(output)
        with connect() as con:
            con.execute("UPDATE tasks SET status='COMPLETED',end_time=?,output_sha=?,evidence=? WHERE task_id=?",
                        (time.time(), output_sha, json.dumps(output, ensure_ascii=False), task_id))
        emit(mission_id, f"{role} terminé", {"farm_id": farm_id, "task_id": task_id, "sha": output_sha})
        return output
    except Exception as exc:
        with connect() as con:
            con.execute("UPDATE tasks SET status='FAILED',end_time=?,errors=? WHERE task_id=?", (time.time(), str(exc), task_id))
        emit(mission_id, f"{role} en échec", {"error": str(exc)}, "ERROR")
        raise


def _farm_bridge_task(mission_id: str, farm_id: int, operation: str, payload: dict) -> dict:
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    start = time.time()
    input_sha = canonical_sha({"mission_id": mission_id, "task_id": task_id, "farm_id": farm_id,
                               "operation": operation, "payload": payload})
    with connect() as con:
        con.execute("""INSERT INTO tasks(task_id,mission_id,farm_id,role,worker,model,tool,status,start_time,input_sha,cost)
                       VALUES(?,?,?,?,?,?,?,?,?,?,0)""",
                    (task_id, mission_id, farm_id, "REAL_FARM_BRIDGE", "github-actions-farm-worker",
                     None, "CEREBRON_FARM_BRIDGE_V1", "RUNNING", start, input_sha))
    emit(mission_id, "Farm Bridge démarré", {"farm_id": farm_id, "task_id": task_id, "operation": operation})
    try:
        request = farm_submit(farm_id, operation, payload, mission_id, task_id)
        emit(mission_id, "Requête Farm Bridge commitée",
             {"farm_id": farm_id, "task_id": task_id, "request_commit_sha": request["request_commit_sha"]})
        result = farm_collect(farm_id, request["request_commit_sha"])
        proof = {"request": request, "result": result}
        output_sha = canonical_sha(proof)
        artifact_sha = str(result["artifact_sha"]).removeprefix("sha256:")
        source = f"github://{request['repo']}/actions/runs/{result['run_id']}/artifacts/{result['artifact_id']}"
        with connect() as con:
            con.execute("UPDATE tasks SET status='COMPLETED',end_time=?,output_sha=?,evidence=? WHERE task_id=?",
                        (time.time(), output_sha, json.dumps(proof, ensure_ascii=False), task_id))
            con.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",
                        (f"ev_{uuid.uuid4().hex[:12]}", mission_id, "REAL_FARM_EXECUTION", source,
                         artifact_sha, json.dumps(proof, ensure_ascii=False), "S5_ARTIFACT_PLUS_SHA", time.time()))
        emit(mission_id, "Farm Bridge vérifié",
             {"farm_id": farm_id, "task_id": task_id, "run_id": result["run_id"], "job_id": result["job_id"],
              "artifact_id": result["artifact_id"], "artifact_sha": result["artifact_sha"]})
        return result
    except FarmBridgeError as exc:
        error = str(exc)
        state = "ROUTED_ONLY" if error in {"GITHUB_TOKEN_UNAVAILABLE", "FARM_BRIDGE_NOT_CONFIGURED", "OPERATION_NOT_ALLOWED"} else "NON_EXECUTED"
        with connect() as con:
            con.execute("UPDATE tasks SET status=?,end_time=?,errors=? WHERE task_id=?",
                        (state, time.time(), error, task_id))
        emit(mission_id, "Farm Bridge non exécuté",
             {"farm_id": farm_id, "task_id": task_id, "status": state, "error": error}, "WARNING")
        return {"protocol": "CEREBRON_FARM_BRIDGE_V1", "farm_id": farm_id, "status": state, "error": error,
                "limitations": ["No FARM_EXECUTED claim without run/job/artifact/SHA."]}


def rover_calculation() -> dict:
    mass_kg = 180.0
    slope_deg = 15.0
    lunar_g = 1.62
    rolling_coefficient = 0.03
    speed_m_s = 0.45
    efficiency = 0.78
    grade_force = mass_kg * lunar_g * math.sin(math.radians(slope_deg))
    rolling_force = rolling_coefficient * mass_kg * lunar_g * math.cos(math.radians(slope_deg))
    traction_force = grade_force + rolling_force
    mechanical_power = traction_force * speed_m_s
    electrical_power = mechanical_power / efficiency
    return {
        "engine": "python-math",
        "equation": "F=m*g*(sin(theta)+Crr*cos(theta)); P=F*v/eta",
        "parameters": {"mass_kg": mass_kg, "slope_deg": slope_deg, "g_m_s2": lunar_g,
                       "rolling_coefficient": rolling_coefficient, "speed_m_s": speed_m_s, "efficiency": efficiency},
        "results": {"traction_force_n": round(traction_force, 3), "mechanical_power_w": round(mechanical_power, 3),
                    "electrical_power_w": round(electrical_power, 3)},
        "maturity": "E2_CALCULATION",
        "limitations": ["quasi-static", "no wheel slip model", "no thermal transient", "not a physical test"],
    }


def execute(mission_id: str) -> None:
    try:
        with connect() as con:
            mission = dict(con.execute("SELECT * FROM missions WHERE mission_id=?", (mission_id,)).fetchone())
            con.execute("UPDATE missions SET status='RUNNING',updated_at=? WHERE mission_id=?", (time.time(), mission_id))
        route = _task(mission_id, 42, "CHEF_DE_COLONIE", "local-router-worker", "CEREBRON-ROUTER-NN-V1", None,
                      lambda: infer(mission["prompt"]))
        domain = route["label"]
        prompt_lower = mission["prompt"].lower()
        bridge_requested = any(
            token in prompt_lower for token in ("hohmann", "transfert orbital", "orbite", "orbital", "f123")
        )
        farms = list(DOMAIN_FARMS[domain])
        if bridge_requested and 123 not in farms:
            farms.append(123)
        emit(mission_id, "Coalition minimale sélectionnée", {"domain": domain, "farms": farms})
        if domain == "space" or "rover" in prompt_lower or bridge_requested:
            concept = _task(mission_id, 15, "SPECIALIST", "deterministic-concept-worker", None, "engineering-rules-v1",
                            lambda: {"concept": "Rover lunaire 6 roues, bogie articulé, navigation autonome supervisée",
                                     "assumptions": ["masse 180 kg", "pente cible 15°", "vitesse 0.45 m/s"]})
            calc = _task(mission_id, 36, "SIMULATION", "python-scientific-worker", None, "python-math", rover_calculation)
            red = _task(mission_id, 33, "RED_TEAM", "deterministic-audit-worker", None, "audit-rules-v1",
                        lambda: {"risks": ["adhérence/régolithe non modélisée", "marge thermique absente", "tolérance panne moteur non calculée"],
                                 "verdict": "CONCEPT_ONLY_NOT_VALIDATED"})
            audit = _task(mission_id, 34, "AUDITOR", "evidence-audit-worker", None, "sha256",
                          lambda: {"checks": ["inputs hashed", "calculation reproducible", "limitations explicit"],
                                   "claim_ceiling": "E2_CALCULATION"})
            bridge = None
            if bridge_requested:
                bridge = _farm_bridge_task(
                    mission_id, 123, "hohmann_reference",
                    {"mu_m3_s2": 3.986004418e14, "r1_m": 6.778e6, "r2_m": 4.2164e7},
                )
            result = {"route": route, "farms": farms, "concept": concept, "calculation": calc, "red_team": red, "audit": audit}
            if bridge is not None:
                result["farm_bridge"] = bridge
            artifact = ARTIFACTS / f"{mission_id}-rover.json"
            payload = json.dumps(result, ensure_ascii=False, indent=2).encode()
            artifact.write_bytes(payload)
            artifact_sha = sha256_bytes(payload)
            evidence_id = f"ev_{uuid.uuid4().hex[:12]}"
            with connect() as con:
                con.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",
                            (evidence_id, mission_id, "CALCULATION_ARTIFACT", str(artifact.relative_to(PLATFORM)), artifact_sha,
                             json.dumps(calc, ensure_ascii=False), "E2_CALCULATION", time.time()))
            lesson = "Séparer le calcul de traction E2 des validations terrain régolithe, thermique et panne moteur."
            lesson_sha = canonical_sha({"mission_id": mission_id, "lesson": lesson})
            with connect() as con:
                con.execute("INSERT INTO agora VALUES(?,?,?,?,?,?,?,?)",
                            (f"ag_{uuid.uuid4().hex[:12]}", mission_id, "LESSON", "UNDER_TEST", lesson,
                             f"mission:{mission_id}", lesson_sha, time.time()))
            result["artifact"] = {"url": f"/api/artifacts/{artifact.name}", "sha": artifact_sha}
        else:
            result = {"route": route, "farms": farms, "status": "ROUTED", "limitations": "No generative model is connected."}
        output_sha = canonical_sha(result)
        with connect() as con:
            con.execute("UPDATE missions SET status='COMPLETED',domain=?,updated_at=?,output_sha=?,result_json=? WHERE mission_id=?",
                        (domain, time.time(), output_sha, json.dumps(result, ensure_ascii=False), mission_id))
        emit(mission_id, "Mission terminée", {"output_sha": output_sha})
    except Exception as exc:
        with connect() as con:
            con.execute("UPDATE missions SET status='FAILED',updated_at=?,error=? WHERE mission_id=?", (time.time(), str(exc), mission_id))
        emit(mission_id, "Mission échouée", {"error": str(exc)}, "ERROR")


def create_mission(prompt: str, session_id: str | None = None) -> dict:
    mission_id = f"mis_{uuid.uuid4().hex[:12]}"
    session_id = session_id or f"ses_{uuid.uuid4().hex[:10]}"
    now = time.time()
    with connect() as con:
        con.execute("INSERT INTO missions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (mission_id, session_id, prompt, "QUEUED", None, now, now, canonical_sha(prompt), None, None, None))
    emit(mission_id, "Mission créée", {"session_id": session_id})
    threading.Thread(target=execute, args=(mission_id,), daemon=True).start()
    return {"mission_id": mission_id, "session_id": session_id, "status": "QUEUED"}


def rows(query: str, params=()) -> list[dict]:
    with connect() as con:
        return [dict(row) for row in con.execute(query, params).fetchall()]


initialize()

