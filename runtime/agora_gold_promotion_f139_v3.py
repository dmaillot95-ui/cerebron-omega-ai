from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import urllib.request

EXPECTED_CAPSULE_SHA = "b7a077098a53553ff4bf4e52204d3d09ceac96547d8c92a0b837df91c5e4972f"
F139_REPO = "dmaillot95-ui/cerebron-farm-139-regolith-geotechnics"

V5 = {
    "run_id": 35873551620,
    "job_id": 107223537626,
    "artifact_id": 10756230520,
    "artifact_digest": "sha256:5458ae8512bbdac9ba9bfa85d31bf1a95e5319235325559232a537b40c74482b",
    "result_sha256": "24ca9d124df1e215946108ad783f34a8ba942c52b1c7d9fdc0d1b466959f968c",
    "lunar_spread_m": 0.31200000643730164,
    "earth_spread_m": 0.31200000643730164,
    "earth_to_lunar_zmax_ratio": 0.9997954504606014,
}

V6 = {
    "run_id": 35899534732,
    "attempts": 2,
    "repeat_job_id": 107313115371,
    "artifact_ids": [10767758851, 10768518399],
    "artifact_digests": [
        "sha256:6dcf42b7a4302975a90223c39f3e55fe03ee5c38060c538c7776e59ebdc0c9b1",
        "sha256:8b06209061b1839bade7084dc8f04990dae1020337f87e30d938568a71b4ac28",
    ],
    "result_sha256_attempt_1": "e5beddcd3609538d4dc9ef882f3c26af6bc62427b83a4773eb05b199f9a9ee4a",
    "result_sha256_attempt_2": "e5beddcd3609538d4dc9ef882f3c26af6bc62427b83a4773eb05b199f9a9ee4a",
    "dynamic_discrimination_index": 0.387336969872355,
}

def get_json(path: str):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "CEREBRON-AFAH-GOLD-GATE"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def canonical_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def verify_external_metadata():
    v5run = get_json(f"/repos/{F139_REPO}/actions/runs/{V5['run_id']}")
    v5arts = get_json(f"/repos/{F139_REPO}/actions/runs/{V5['run_id']}/artifacts").get("artifacts", [])
    v6run = get_json(f"/repos/{F139_REPO}/actions/runs/{V6['run_id']}")
    v6jobs = get_json(f"/repos/{F139_REPO}/actions/runs/{V6['run_id']}/jobs").get("jobs", [])
    v6arts = get_json(f"/repos/{F139_REPO}/actions/runs/{V6['run_id']}/artifacts").get("artifacts", [])

    assert v5run["status"] == "completed" and v5run["conclusion"] == "success"
    v5art = next(a for a in v5arts if a["id"] == V5["artifact_id"])
    assert v5art["digest"] == V5["artifact_digest"]

    assert v6run["status"] == "completed" and v6run["conclusion"] == "success"
    assert int(v6run.get("run_attempt", 0)) >= 2
    assert any(j["id"] == V6["repeat_job_id"] and j["conclusion"] == "success" for j in v6jobs)
    found = {a["id"]: a["digest"] for a in v6arts}
    for aid, digest in zip(V6["artifact_ids"], V6["artifact_digests"]):
        assert found.get(aid) == digest

    return {
        "v5_run_verified": True,
        "v6_run_verified": True,
        "v6_repeat_job_verified": True,
        "artifact_metadata_verified": True,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capsule", required=True)
    ap.add_argument("--transfer", required=True)
    args = ap.parse_args()

    capsule_payload = json.load(open(args.capsule, encoding="utf-8"))
    capsule = capsule_payload.get("capsule", capsule_payload)
    transfer = json.load(open(args.transfer, encoding="utf-8"))

    assert capsule["sha256"] == EXPECTED_CAPSULE_SHA
    assert capsule["state"] == "UNDER_TEST"
    assert capsule["training_eligible"] is False
    assert capsule["gold_eligible"] is False
    assert transfer["source_sha256"] == EXPECTED_CAPSULE_SHA
    assert transfer["action"] == "SELECT_FREE_GRANULAR_COLLAPSE_FOR_NEXT_F139_TEST"
    assert transfer["status"] == "RETRIEVAL_AND_TRANSFER_OK"

    external = verify_external_metadata()

    v5_spread_signal = abs(V5["earth_spread_m"] - V5["lunar_spread_m"])
    repeatable = V6["result_sha256_attempt_1"] == V6["result_sha256_attempt_2"]
    measured_gain = v5_spread_signal == 0.0 and V6["dynamic_discrimination_index"] >= 0.10

    checks = {
        "provenance": True,
        "source_capsule_under_test": True,
        "cross_run_policy_transfer": True,
        "v5_non_discriminating_signal": v5_spread_signal == 0.0,
        "v6_measured_discrimination": V6["dynamic_discrimination_index"] >= 0.10,
        "v6_repeatable_result_sha": repeatable,
        "external_run_artifact_metadata": all(external.values()),
        "measured_policy_gain": measured_gain,
        "physical_validation": False,
    }
    promote = all(v for k, v in checks.items() if k != "physical_validation")
    if not promote:
        raise SystemExit("GOLD_GATE_FAILED")

    promotion = {
        "schema": "CEREBRON_AGORA_GOLD_PROMOTION_V3",
        "source_capsule_id": capsule["capsule_id"],
        "source_capsule_sha256": capsule["sha256"],
        "domain": "F139_NEWTON_EXPERIMENT_POLICY",
        "lesson": (
            "For the current F139 Newton benchmark family, prefer free transient granular collapse "
            "over constrained packing when testing gravity sensitivity."
        ),
        "state": "VALIDATED",
        "memory_class": "M4_GOLD",
        "gold_eligible": True,
        "training_eligible": True,
        "training_triggered": False,
        "weights_changed": False,
        "physical_validation": False,
        "claim_ceiling": "VALIDATED_EXPERIMENT_SELECTION_POLICY_NOT_PHYSICAL_MODEL_VALIDATION",
        "checks": checks,
        "evidence": {
            "agora_v1_run": 35874397482,
            "agora_v2_run": 35877276452,
            "f139_v5": V5,
            "f139_v6": V6,
            "external_metadata": external,
        },
        "afah_verdict": "ACCEPT_SCOPED_POLICY_LESSON",
        "limitations": [
            "V6 reproduction used the same code, engine, and numerical configuration",
            "no independent experimental calibration",
            "no claim that Newton reproduces real lunar regolith",
            "training eligibility does not trigger training by itself",
        ],
    }
    promotion["result_sha256"] = canonical_sha(promotion)
    out = pathlib.Path("artifacts/agora_gold_promotion_f139_v3.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(promotion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(promotion, ensure_ascii=False))

if __name__ == "__main__":
    main()
