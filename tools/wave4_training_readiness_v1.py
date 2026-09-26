#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/wave4-specialist-training-readiness-v1.json").read_text())
COVER = json.loads((ROOT / "config/all-ai-neural-training-coverage-v1.json").read_text())

ROLES = list(CFG["roles"])
ACCEPTED = {x.upper() for x in CFG["accepted_validation_states"]}
TRAIN_SPLITS = {x.upper() for x in CFG["accepted_train_splits"]}
FORBIDDEN = {x.upper() for x in CFG["forbidden_train_splits"]}
PROV_FIELDS = set(CFG["required_record_fields_any"])


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def walk(obj, path="$"):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def norm(v):
    return str(v).strip().upper() if v is not None else ""


def role_matches(d, role):
    values = []
    for k in ("role", "target_role", "target_ai", "ai_id", "identity", "worker_id"):
        if k in d:
            v = d[k]
            if isinstance(v, list):
                values.extend(norm(x) for x in v)
            else:
                values.append(norm(v))
    return role in values


def split_of(d):
    for k in ("split", "source_split", "dataset_split", "benchmark_split"):
        if k in d:
            return norm(d[k])
    return ""


def validation_of(d):
    for k in ("validation_status", "lesson_status", "evidence_class", "class", "status", "tier"):
        if k in d:
            return norm(d[k])
    return ""


def has_provenance(d):
    return any(k in d and d[k] not in (None, "", [], {}) for k in PROV_FIELDS)


def audit_source(rel):
    p = ROOT / rel
    if not p.exists():
        return {"path": rel, "exists": False, "sha256": None, "json_valid": False, "objects": []}
    raw = p.read_bytes()
    try:
        obj = json.loads(raw)
    except Exception as e:
        return {"path": rel, "exists": True, "sha256": sha256_bytes(raw), "json_valid": False, "error": type(e).__name__, "objects": []}
    objects = []
    for jp, d in walk(obj):
        if not isinstance(d, dict):
            continue
        matched = [r for r in ROLES if role_matches(d, r)]
        if not matched:
            continue
        objects.append({
            "json_path": jp,
            "roles": matched,
            "split": split_of(d),
            "validation": validation_of(d),
            "has_provenance": has_provenance(d)
        })
    return {"path": rel, "exists": True, "sha256": sha256_bytes(raw), "json_valid": True, "role_targeted_objects": objects}


def main():
    entries = {e.get("identity"): e for e in COVER.get("entries", [])}
    sources = [audit_source(p) for p in CFG["candidate_sources"]]
    role_results = {}
    for role in ROLES:
        cov = entries.get(role)
        coverage_ok = bool(
            cov
            and cov.get("available") is True
            and cov.get("planned_wave") == "WAVE4"
            and cov.get("coverage_state") == "PENDING_SPECIALIST_NEURAL_PIPELINE"
        )
        seen = 0
        eligible = 0
        forbidden_seen = 0
        diagnostics = []
        fingerprints = set()
        for s in sources:
            for o in s.get("role_targeted_objects", []):
                if role not in o["roles"]:
                    continue
                seen += 1
                sp = o["split"]
                va = o["validation"]
                if sp in FORBIDDEN:
                    forbidden_seen += 1
                    diagnostics.append({"source": s["path"], "path": o["json_path"], "decision": "DENY_EVAL_SPLIT", "split": sp})
                    continue
                record_ok = sp in TRAIN_SPLITS and va in ACCEPTED and o["has_provenance"]
                if record_ok:
                    fp = sha256_bytes((s["sha256"] + "|" + o["json_path"] + "|" + role).encode())
                    if fp not in fingerprints:
                        fingerprints.add(fp)
                        eligible += 1
                else:
                    diagnostics.append({"source": s["path"], "path": o["json_path"], "decision": "CANDIDATE_NOT_ADMISSIBLE", "split": sp, "validation": va, "has_provenance": o["has_provenance"]})
        min_n = CFG["minimum_validated_train_records_per_role"]
        data_ready = eligible >= min_n
        status = "READY_FOR_DATASET_ADMISSION" if coverage_ok and data_ready else "BLOCKED_DATA"
        role_results[role] = {
            "coverage_ok": coverage_ok,
            "coverage_state": cov.get("coverage_state") if cov else None,
            "planned_wave": cov.get("planned_wave") if cov else None,
            "training_mode": cov.get("training_mode") if cov else None,
            "specialization_tags": cov.get("specialization_tags") if cov else CFG["roles"][role],
            "role_targeted_objects_seen": seen,
            "eligible_validated_train_records": eligible,
            "minimum_required": min_n,
            "forbidden_eval_objects_seen": forbidden_seen,
            "status": status,
            "training_released": False,
            "weights_changed": False,
            "diagnostics": diagnostics[:40]
        }

    ready = [r for r, x in role_results.items() if x["status"] == "READY_FOR_DATASET_ADMISSION"]
    report = {
        "schema": "CEREBRON_WAVE4_TRAINING_READINESS_AUDIT_V1",
        "wave": "WAVE4",
        "status": "READY_CANDIDATE_ADMISSION" if ready else "BLOCKED_DATA",
        "roles": role_results,
        "candidate_sources": sources,
        "ready_roles": ready,
        "candidate_build_priority": ROLES[:4],
        "max_parallel_training_after_release": CFG["max_parallel_training_after_release"],
        "training_released": False,
        "training_executed": False,
        "weights_changed": False,
        "protected_surfaces_mutated": False,
        "next_action": "BUILD_AND_AUDIT_ROLE_SPECIFIC_TRAIN_DATA" if not ready else "RUN_DATASET_ADMISSION_GATE",
        "claim_boundary": "READINESS_AUDIT_ONLY_NOT_NEURAL_TRAINING"
    }
    report["report_sha256"] = sha256_bytes(json.dumps(report, sort_keys=True, separators=(",", ":")).encode())
    out = ROOT / "artifacts/wave4-training-readiness-v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": report["status"],
        "ready_roles": ready,
        "candidate_build_priority": report["candidate_build_priority"],
        "eligible_counts": {r: role_results[r]["eligible_validated_train_records"] for r in ROLES},
        "report_sha256": report["report_sha256"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
