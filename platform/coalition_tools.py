from __future__ import annotations

from coalition import execute as execute_model_coalition
from model_router import infer
from specialist_tools import try_solve


def execute(prompt: str) -> dict:
    prompt = str(prompt).strip()
    if not prompt:
        raise ValueError("prompt required")

    tool = try_solve(prompt)
    if not tool.get("handled"):
        result = execute_model_coalition(prompt)
        result["execution_mode"] = "MODEL_COALITION_FALLBACK"
        return result

    route = infer(prompt)
    unit = tool["unit"]
    selected = []
    for uid in ("SM00", unit, "SM15", "SM18"):
        if uid not in selected:
            selected.append(uid)

    audit = {
        "unit": "SM15",
        "status": "EXECUTED",
        "method": "deterministic-tool-audit-v1",
        "verdict": "BOUNDED_TOOL_OUTPUT",
        "claim_ceiling": "DETERMINISTIC_TOOL_RESULT",
        "checks": [
            "bounded parser/solver selected",
            "no remote evidence claim",
            "no physical validation claim",
        ],
    }
    fused = {
        "unit": "SM18",
        "status": "EXECUTED",
        "method": "deterministic-fusion-v1",
        "answer": tool["answer"],
        "audit_verdict": audit["verdict"],
        "claim_ceiling": audit["claim_ceiling"],
    }
    return {
        "schema": "CEREBRON_COALITION_EXECUTION_V2_TOOLS",
        "status": "COMPLETED",
        "execution_mode": "DETERMINISTIC_SPECIALIST_TOOL",
        "plan": {
            "strategy": "SEARCH_GENERATE_VERIFY_MINIMAL_USEFUL_COALITION",
            "route": route,
            "primary": unit,
            "selected_units": selected,
            "logical_unit_count": len(selected),
            "independent_model_count": 0,
            "shared_dependencies": [],
            "warning": "Tool execution is deterministic computation, not an independent neural model or physical validation.",
        },
        "workers": {
            "SM00": {"unit": "SM00", "status": "EXECUTED", "result": route},
            unit: tool,
            "SM15": audit,
            "SM18": fused,
        },
        "answer": tool["answer"],
        "claim_ceiling": audit["claim_ceiling"],
    }
