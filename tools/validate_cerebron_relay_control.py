#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "cerebron-relay-control-gates.json"

def load(path):
    return json.loads((ROOT / path).read_text())

farms = load("config/farms.json")
greek = load("config/greek-ai-constellation-v1.json")
colonies = load("config/greek-24-colony-master.json")
dual = load("config/cerebron-dual-core-contract-v1.json")
bus = load("config/cerebron-unified-plugin-bus-v1.json")
status_contract = load("config/cerebron-role-runtime-status-v1.json")
stop = load("config/cerebron-stop-resume-protocol-v1.json")
gate_contract = load("config/cerebron-measurable-gates-v1.json")

results = []
errors = []

def record(gate_id, ok, metrics, reason=None):
    state = "PASS" if ok else "FAIL"
    results.append({"gate_id": gate_id, "status": state, "metrics": metrics, "reason": reason})
    if not ok:
        errors.append(f"{gate_id}: {reason or 'criterion failed'}")

farm_by_id = {f["id"]: f for f in farms["farms"]}

# G01 — role / identity status
roles = greek["roles"]
names = [r["name"] for r in roles]
role_ids = [r["role_id"] for r in roles]
bindings = 0
for r in roles:
    f = farm_by_id.get(r["id"], {})
    if f.get("identity") == r["name"] and f.get("role_id") == r["role_id"] and f.get("greek_constellation") is True:
        bindings += 1
nu = farm_by_id.get(162, {})
g01_metrics = {
    "greek_roles_configured": len(roles),
    "unique_greek_names": len(set(names)),
    "unique_greek_role_ids": len(set(role_ids)),
    "registry_bindings": bindings,
    "nu_repository_exists": nu.get("repository_exists"),
    "nu_status": nu.get("status"),
    "known_unavailable": status_contract["greek_registry"]["known_unavailable"],
}
g01 = (
    len(roles) == 24
    and len(set(names)) == 24
    and len(set(role_ids)) == 24
    and bindings == 24
    and nu.get("repository_exists") is False
    and nu.get("status") == "PREPARED_NOT_DEPLOYED_REPOSITORY_MISSING"
)
record("G01_ROLE_IDENTITY_STATUS", g01, g01_metrics, None if g01 else "Greek role/identity accounting mismatch")

# G02 — colony structure
colony_list = colonies["colonies"]
team = set(colonies["team_template"])
required_team = set(status_contract["colony_status"]["required_core_roles"])
colony_names = {c["identity"] for c in colony_list}
g02_metrics = {
    "colonies_configured": len(colony_list),
    "required_core_roles_present": len(required_team & team),
    "required_core_roles_expected": len(required_team),
    "colony_identity_match": len(colony_names & set(names)),
}
g02 = len(colony_list) == 24 and required_team.issubset(team) and colony_names == set(names)
record("G02_COLONY_STRUCTURE", g02, g02_metrics, None if g02 else "Colony roster/team template mismatch")

# G03 — dual-core reality
candidates = dual["candidate_assignments"]
candidate_ids = {c["farm_id"] for c in candidates}
verified = dual.get("verified_assignments", [])
verified_ids = {x.get("farm_id") for x in verified if isinstance(x, dict) and x.get("farm_id") is not None}
required_full = set(status_contract["dual_core_status"]["full_validation_requires"])
fully_validated = 0
for c in candidates:
    gates = c.get("gate_status", {})
    if all(gates.get(k) == "PASS" for k in required_full):
        fully_validated += 1
g03_metrics = {
    "dual_core_candidates": len(candidates),
    "candidate_farm_ids": sorted(candidate_ids),
    "dual_core_verified_assignments": len(verified),
    "fully_validated_dual_core": fully_validated,
    "required_full_validation_gates": sorted(required_full),
}
g03 = (
    len(candidates) == 7
    and candidate_ids == set(range(145, 152))
    and verified_ids.issubset(candidate_ids)
)
record("G03_DUAL_CORE_REALITY", g03, g03_metrics, None if g03 else "Dual-core candidate/verified assignment accounting mismatch")

# G04 — anti-false-consensus
greek_rules = set(greek.get("hard_rules", []))
status_text = json.dumps(status_contract, sort_keys=True)
overlap_terms = ["source", "prompt", "memory", "dataset"]
overlap_count = sum(1 for x in overlap_terms if x in status_text.lower())
shared_lineage_rule = "SHARED_BASE!=INDEPENDENT_EVIDENCE" in greek_rules
consensus_rule = status_contract["accounting_rules"].get("consensus_is_not_independent_evidence") is True
g04_metrics = {
    "shared_lineage_rule_present": shared_lineage_rule,
    "consensus_rule_present": consensus_rule,
    "overlap_dimensions_defined": overlap_count,
}
g04 = shared_lineage_rule and consensus_rule and overlap_count >= 4
record("G04_ANTI_FALSE_CONSENSUS", g04, g04_metrics, None if g04 else "Independent-evidence safeguards incomplete")

# G05 — stop/resume
states = stop["states"]
required_states = {"RUN", "DRAIN", "CHECKPOINT", "VERIFY", "FROZEN", "RESUME_VERIFY"}
freeze_impl = (ROOT / stop["implementation"]["local_state_machine"]).exists()
freeze_canary = (ROOT / stop["implementation"]["canary_workflow"]).exists()
overclaim_blocked = stop["implementation"].get("systemwide_stop_claimed") is False
g05_metrics = {
    "protocol_states": states,
    "required_states_present": len(required_states & set(states)),
    "freeze_implementation_present": freeze_impl,
    "freeze_canary_present": freeze_canary,
    "systemwide_stop_overclaim_blocked": overclaim_blocked,
    "enforcement_scope_now": stop["implementation"]["enforcement_scope_now"],
}
g05 = required_states.issubset(set(states)) and freeze_impl and freeze_canary and overclaim_blocked
record("G05_STOP_RESUME", g05, g05_metrics, None if g05 else "Stop/resume protocol is not fail-closed or implementation is missing")

# G06 — F162/F173/F174 reality
f162, f173, f174 = farm_by_id[162], farm_by_id[173], farm_by_id[174]
g06_metrics = {
    "f162_status": f162.get("status"),
    "f162_repository_exists": f162.get("repository_exists"),
    "f173_external_runtime": f173.get("external_runtime_status"),
    "f173_production_status": f173.get("production_status"),
    "f173_http_loopback": f173.get("local_http_loopback_canary_status"),
    "f174_video_status": f174.get("simulation_status"),
    "f174_production_video_claimed": f174.get("production_video_claimed"),
    "f174_physical_validation_claimed": f174.get("physical_validation_claimed"),
    "f174_training_status": f174.get("training_status"),
}
g06 = (
    f162.get("repository_exists") is False
    and f173.get("external_runtime_status") == "UNQUALIFIED"
    and f173.get("production_status") == "NOT_DEPLOYED"
    and f173.get("local_http_loopback_canary_status") == "PASS"
    and f174.get("simulation_status") == "VIDEO_RENDER_CANARY_EXECUTED"
    and f174.get("production_video_claimed") is False
    and f174.get("physical_validation_claimed") is False
    and f174.get("training_status") == "NOT_TRAINED"
)
record("G06_EXTENSION_REALITY", g06, g06_metrics, None if g06 else "F162/F173/F174 claim boundary mismatch")

# G07 — bus/crystal
ids = [f["id"] for f in farms["farms"]]
routes = bus["routes"]
providers = bus["providers"]
g07_metrics = {
    "farm_count": len(ids),
    "registry_max_farms": farms.get("max_farms"),
    "ids_contiguous": ids == list(range(1, 175)),
    "rdx_search_provider": routes.get("rdx.search"),
    "rdx_fetch_provider": routes.get("rdx.fetch"),
    "f152_identity": farm_by_id[152].get("identity"),
    "f152_rdx_provider_present": "F152_RDX" in providers,
    "unknown_capability_policy": bus["invariants"].get("unknown_capability"),
}
g07 = (
    len(ids) == 174
    and farms.get("max_farms") == 174
    and ids == list(range(1, 175))
    and routes.get("rdx.search") == "RDX_EXCHANGE"
    and routes.get("rdx.fetch") == "RDX_EXCHANGE"
    and farm_by_id[152].get("identity") == "BETA"
    and "F152_RDX" not in providers
    and bus["invariants"].get("unknown_capability") == "DENY"
)
record("G07_BUS_CRYSTAL", g07, g07_metrics, None if g07 else "Registry continuity or plugin bus invariant mismatch")

expected_gate_ids = {g["id"] for g in gate_contract["gates"]}
actual_gate_ids = {r["gate_id"] for r in results}
if expected_gate_ids != actual_gate_ids:
    errors.append(f"GATE_CONTRACT_MISMATCH expected={sorted(expected_gate_ids)} actual={sorted(actual_gate_ids)}")

report = {
    "schema": "CEREBRON_RELAY_CONTROL_GATE_REPORT_V1",
    "status": "PASS" if not errors else "FAIL",
    "gate_count": len(results),
    "pass_count": sum(r["status"] == "PASS" for r in results),
    "fail_count": sum(r["status"] == "FAIL" for r in results),
    "results": results,
    "claim_limits": {
        "role_configured_is_not_model_running": True,
        "colony_configured_is_not_colony_executed": True,
        "dual_core_is_not_independent_evidence": True,
        "local_freeze_canary_is_not_global_stop": True,
        "memory_is_not_training": True,
        "simulation_is_not_physical_test": True,
    },
    "errors": errors,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, sort_keys=True))
if errors:
    raise SystemExit(1)
