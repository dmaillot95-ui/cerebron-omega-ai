from __future__ import annotations
import argparse, hashlib, json, pathlib
from typing import Any, Dict

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = ROOT / "config"

REQUIRED = {
    "schema", "rdx_id", "object_id", "object_type", "content",
    "provenance", "rights", "validated", "dedup_pass",
    "license_origin_pass", "m6_contamination", "afah_pass"
}
ALLOWED_TYPES = {
    "RDX_RESEARCH","QUESTION","HYPOTHESIS","CLAIM","SOURCE","CALCULATION",
    "TEST","RESULT","COUNTEREXAMPLE","FAILURE","ALTERNATIVE",
    "SIMULATION_RECEIPT","LIMITATION","EVIDENCE_LEVEL","CONCLUSION","VERSION"
}

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha256(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()

def load_config(name: str) -> Dict[str, Any]:
    return json.loads((CFG / name).read_text())

def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    policy = load_config("memory-promotion-policy-v1.json")
    loop = load_config("rdx-knowledge-training-loop-v1.json")
    errors = []

    missing = sorted(REQUIRED - set(record))
    if missing:
        errors.append("MISSING_FIELDS:" + ",".join(missing))

    object_type = record.get("object_type")
    if object_type not in ALLOWED_TYPES:
        errors.append("OBJECT_TYPE_NOT_ALLOWED")

    provenance = record.get("provenance") or {}
    provenance_pass = bool(
        provenance.get("source_ids")
        and provenance.get("origin")
        and provenance.get("producer")
    )
    if not provenance_pass:
        errors.append("PROVENANCE_FAIL")

    if record.get("dedup_pass") is not True:
        errors.append("DEDUP_FAIL")

    rights = record.get("rights") or {}
    rights_class = rights.get("class", "UNKNOWN")
    explicit_training_right = rights.get("shared_training_allowed") is True
    tenant_id = rights.get("tenant_id")

    secret = rights_class == "SECRET"
    client_private = rights_class == "CLIENT_PRIVATE"
    public_or_owned = rights_class in {"PUBLIC", "OWNED"}

    if secret:
        errors.append("SECRET_DENY")
    if client_private and not tenant_id:
        errors.append("CLIENT_PRIVATE_TENANT_REQUIRED")

    m6_contamination = record.get("m6_contamination") is True
    if m6_contamination:
        errors.append("M6_CONTAMINATION")

    basic_ok = not missing and object_type in ALLOWED_TYPES and provenance_pass and record.get("dedup_pass") is True
    memory_allowed = basic_ok and not secret and not m6_contamination
    shared_memory = memory_allowed and public_or_owned
    tenant_memory = memory_allowed and client_private and bool(tenant_id)

    f72 = policy.get("live_gates", {}).get("F72", {})
    f72_pass = f72.get("current") == "PASS"
    afah_pass = record.get("afah_pass") is True
    validated = record.get("validated") is True
    license_origin_pass = record.get("license_origin_pass") is True

    rights_train_ok = public_or_owned or (client_private and explicit_training_right and bool(tenant_id))
    global_promotion_open = (
        f72_pass
        and policy.get("global_promotion_state", "").startswith("PASS")
    )

    train_eligible = all([
        basic_ok,
        validated,
        license_origin_pass,
        not m6_contamination,
        not secret,
        rights_train_ok,
        f72_pass,
        afah_pass,
        global_promotion_open,
    ])

    blockers = []
    checks = {
        "schema": not missing and object_type in ALLOWED_TYPES,
        "provenance": provenance_pass,
        "dedup": record.get("dedup_pass") is True,
        "validated": validated,
        "license_origin": license_origin_pass,
        "m6_clean": not m6_contamination,
        "rights_training": rights_train_ok and not secret,
        "f72": f72_pass,
        "afah": afah_pass,
        "global_promotion": global_promotion_open,
    }
    for name, ok in checks.items():
        if not ok:
            blockers.append(name.upper())

    payload_sha = sha256({
        "rdx_id": record.get("rdx_id"),
        "object_id": record.get("object_id"),
        "object_type": object_type,
        "content": record.get("content"),
        "provenance": provenance,
        "rights": rights,
    })
    namespace = "RDX_SHARED" if shared_memory else (
        f"RDX_TENANT/{tenant_id}" if tenant_memory else "RDX_QUARANTINE"
    )

    return {
        "schema": "CEREBRON_RDX_INGRESS_DECISION_V1",
        "rdx_id": record.get("rdx_id"),
        "object_id": record.get("object_id"),
        "object_type": object_type,
        "payload_sha256": payload_sha,
        "memory": {
            "admissible": memory_allowed,
            "shared": shared_memory,
            "tenant_only": tenant_memory,
            "namespace": namespace,
            "classes": ["M1", "M7"] if memory_allowed else [],
            "rag_available": memory_allowed,
        },
        "gold": {
            "eligible": train_eligible,
            "class": "M4" if train_eligible else None,
            "blockers": blockers,
        },
        "training": {
            "eligible": train_eligible,
            "auto_train": False,
            "route_targets": list(loop["training_route"]["targets"]) if train_eligible else [],
            "weights_changed": False,
            "claim": "NO_NEURAL_TRAINING_EXECUTED",
        },
        "gate_snapshot": {
            "f72_current": f72.get("current"),
            "global_promotion_state": policy.get("global_promotion_state"),
            "afah_record_pass": afah_pass,
        },
        "errors": errors,
        "claim_ceiling": (
            "MEMORY_AND_GOLD_ELIGIBILITY_DECISION_ONLY_NO_EXTERNAL_WRITE_NO_TRAINING"
        ),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output")
    args = ap.parse_args()
    record = json.loads(pathlib.Path(args.input).read_text())
    out = validate_record(record)
    raw = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        p = pathlib.Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(raw)
    print(raw, end="")
    return 0 if out["memory"]["admissible"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
