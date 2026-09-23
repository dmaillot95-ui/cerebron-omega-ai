from __future__ import annotations

import json
import pathlib
import time

from coalition_tools import execute as coalition_execute
from generative_backend import MODEL_ID, REVISION, generate, status
from mission_engine import create_mission, rows


def require_answer(prompt: str, expected: str):
    result = coalition_execute(prompt)
    answer = str(result.get("answer", "")).strip()
    if answer != expected:
        raise AssertionError({"prompt": prompt, "expected": expected, "answer": answer, "result": result})
    return {
        "prompt": prompt,
        "answer": answer,
        "mode": result.get("execution_mode"),
        "selected_units": result.get("plan", {}).get("selected_units", []),
        "claim_ceiling": result.get("claim_ceiling"),
    }


def wait_mission(mission_id: str):
    for _ in range(240):
        row = rows("SELECT * FROM missions WHERE mission_id=?", (mission_id,))[0]
        if row["status"] in {"COMPLETED", "FAILED"}:
            return row
        time.sleep(0.05)
    raise TimeoutError(mission_id)


def main():
    backend = status()
    if backend["status"] != "ACTIVE_WORKER":
        raise SystemExit(f"GEN_BACKEND_NOT_ACTIVE:{backend}")

    tool_results = [
        require_answer("Give only the product of 18 and 27.", "486"),
        require_answer(
            "A mass of 12 kg accelerates at 3.5 m/s^2. "
            "Using force equals mass times acceleration, give only the force.",
            "42",
        ),
        require_answer(
            "FACTS: alpha is 0.250; beta is 0.750; gamma is 1.500. "
            "Based only on FACTS, give the value of beta.",
            "0.750",
        ),
        require_answer(
            "Choose only A, B, or C. K must be first; L must occur before M. "
            "Candidate orders: A: L > K > M | B: K > M > L | C: K > L > M",
            "C",
        ),
        require_answer(
            "Which claim is incorrect? Reply only with its letter. "
            "A) 4+4=8; B) 9-3=6; C) 5*5=24",
            "C",
        ),
    ]

    model = generate("Reply with exactly READY.", max_new_tokens=12)
    if not str(model["generation"]).strip():
        raise AssertionError("EMPTY_QWEN_GENERATION")

    created = create_mission("Give only the product of 18 and 27.", owner_id="main-live-e2e")
    mission = wait_mission(created["mission_id"])
    if mission["status"] != "COMPLETED":
        raise AssertionError(mission)
    result = json.loads(mission["result_json"])
    if str(result.get("answer", "")).strip() != "486":
        raise AssertionError(result)

    out = {
        "schema": "CEREBRON_MAIN_LIVE_E2E_V1",
        "status": "PASS",
        "model_id": MODEL_ID,
        "revision": REVISION,
        "backend_status": backend["status"],
        "model_generation": model["generation"],
        "model_output_sha": model["output_sha"],
        "semantic_tool_checks": tool_results,
        "mission_id": created["mission_id"],
        "mission_status": mission["status"],
        "mission_answer": result["answer"],
        "mission_claim_ceiling": result.get("claim_ceiling"),
        "limitations": [
            "CI CPU execution",
            "bounded synthetic/tool tasks",
            "model text is not independent evidence",
            "not public deployment or physical validation",
        ],
    }
    path = pathlib.Path("platform/artifacts/main-live-e2e-v1.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
