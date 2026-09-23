from __future__ import annotations

from coalition import registry as coalition_registry
from generative_backend import status as generative_status

ELYRA_EVIDENCE = {
    "policy": "ELYRA_IMITATION_POLICY_V1",
    "weights_sha256": "b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601",
    "training_run": 35904950828,
    "audit_run": 35905952407,
    "scope": "SYNTHETIC_ROVER_POLICY_ONLY",
}

LOGICAL_ROLES = (
    "SPIRALION",
    "ETHERION",
    "HYPERION",
    "ASTRION",
    "METRION",
    "AFAH",
    "AÉLYS",
)


def runtime_roles() -> dict:
    gen = generative_status()
    micro = coalition_registry()
    implemented = list(micro.get("implemented_initial", []))
    units = micro.get("units", [])
    planned = [u["id"] for u in units if u.get("status") == "PLANNED_UNAVAILABLE"]

    roles = [
        {
            "name": "CÉRÉBRON",
            "type": "CONTROL_PLANE",
            "status": "ACTIVE",
            "dedicated_model": False,
            "note": "orchestrator/control plane; not a farm",
        },
        {
            "name": "SAPHEA",
            "type": "LOGICAL_ORCHESTRATOR",
            "status": "ACTIVE_BOUNDED",
            "dedicated_model": False,
            "note": "selects and coordinates bounded specialist capabilities",
        },
    ]
    roles.extend(
        {
            "name": name,
            "type": "LOGICAL_ROLE",
            "status": "CONFIGURED_NO_DEDICATED_MODEL",
            "dedicated_model": False,
        }
        for name in LOGICAL_ROLES
    )
    roles.append(
        {
            "name": "ELYRA",
            "type": "SCOPED_TRAINED_POLICY",
            "status": "TRAINED_ARTIFACT_VERIFIED_NOT_LOADED_IN_CONTROL_PLANE",
            "dedicated_model": True,
            "runtime_loaded": False,
            "evidence": ELYRA_EVIDENCE,
        }
    )
    roles.append(
        {
            "name": "SAPHEA MICRO",
            "type": "SPECIALIST_POPULATION",
            "status": "PARTIALLY_IMPLEMENTED",
            "implemented_units": implemented,
            "planned_unavailable_units": planned,
            "implemented_count": len(implemented),
            "planned_count": len(planned),
            "generative_backend": {
                "model_id": gen.get("model_id"),
                "revision": gen.get("revision"),
                "status": gen.get("status"),
                "active_distinct_model_count": 1 if gen.get("status") == "ACTIVE_WORKER" else 0,
            },
            "independence_note": (
                "Multiple role calls sharing the same Qwen base model are correlated "
                "and are not counted as independent neural models."
            ),
        }
    )
    return {
        "schema": "CEREBRON_ROLE_RUNTIME_V1",
        "roles": roles,
        "logical_role_count": len(roles),
        "claim_ceiling": "RUNTIME_STATUS_ONLY",
    }
