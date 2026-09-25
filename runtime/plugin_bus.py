#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class PluginBusError(RuntimeError):
    """Fail-closed error for the CEREBRON plugin bus."""


@dataclass(frozen=True)
class Provider:
    provider_id: str
    capabilities: tuple[str, ...]
    raw: dict[str, Any]


class CerebronPluginBus:
    """Read-only discovery/router for CEREBRON plugin-like capabilities.

    This layer does not execute remote providers by itself. It gives every
    component one typed contract and one authoritative registry, while
    provider-specific adapters remain responsible for authenticated calls.
    Unknown capabilities and blocked training routes fail closed.
    """

    def __init__(self, registry_path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[1]
        self.registry_path = Path(registry_path) if registry_path else (
            root / "config" / "cerebron-unified-plugin-bus-v1.json"
        )
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self._validate_registry()

    def _validate_registry(self) -> None:
        if self.registry.get("schema") != "CEREBRON_UNIFIED_PLUGIN_BUS_V1":
            raise PluginBusError("REGISTRY_SCHEMA_MISMATCH")
        if self.registry.get("authority") != "AFAH":
            raise PluginBusError("AUTHORITY_MISMATCH")

        data_plane = self.registry.get("private_data_plane", {})
        if data_plane.get("visibility") != "PRIVATE":
            raise PluginBusError("HF_DATA_PLANE_MUST_BE_PRIVATE")
        if data_plane.get("secret_commit_policy") != "NEVER_COMMIT":
            raise PluginBusError("SECRET_POLICY_MISMATCH")

        gates = self.registry.get("gates", {})
        if gates.get("m6_training") != "DENY":
            raise PluginBusError("M6_MUST_DENY_TRAINING")
        if gates.get("secrets_training") != "NEVER_TRAIN":
            raise PluginBusError("SECRETS_MUST_NEVER_TRAIN")

        declared = set(self.registry.get("plugin_contract", {}).get("capabilities", []))
        if not declared:
            raise PluginBusError("NO_CAPABILITIES_DECLARED")

        provided: set[str] = set()
        for raw in self.registry.get("providers", []):
            provider_id = str(raw.get("id", "")).strip()
            if not provider_id:
                raise PluginBusError("PROVIDER_ID_MISSING")
            caps = raw.get("capabilities", [])
            if not isinstance(caps, list) or not caps:
                raise PluginBusError(f"PROVIDER_CAPABILITIES_MISSING:{provider_id}")
            provided.update(map(str, caps))

        missing = sorted(declared - provided)
        if missing:
            raise PluginBusError("UNBOUND_CAPABILITIES:" + ",".join(missing))

    @property
    def capabilities(self) -> tuple[str, ...]:
        return tuple(self.registry["plugin_contract"]["capabilities"])

    def providers_for(self, capability: str) -> tuple[Provider, ...]:
        if capability not in self.capabilities:
            raise PluginBusError(f"UNKNOWN_CAPABILITY:{capability}")
        out: list[Provider] = []
        for raw in self.registry["providers"]:
            caps = tuple(str(x) for x in raw.get("capabilities", []))
            if capability in caps:
                out.append(Provider(str(raw["id"]), caps, raw))
        if not out:
            raise PluginBusError(f"NO_PROVIDER:{capability}")
        return tuple(out)

    def provider(self, provider_id: str) -> Provider:
        for raw in self.registry["providers"]:
            if raw.get("id") == provider_id:
                return Provider(
                    provider_id=str(raw["id"]),
                    capabilities=tuple(str(x) for x in raw.get("capabilities", [])),
                    raw=raw,
                )
        raise PluginBusError(f"UNKNOWN_PROVIDER:{provider_id}")

    def namespace(self, namespace_id: str) -> dict[str, Any]:
        namespaces = self.registry.get("namespaces", {})
        if namespace_id not in namespaces:
            raise PluginBusError(f"UNKNOWN_NAMESPACE:{namespace_id}")
        return dict(namespaces[namespace_id])

    def assert_route_allowed(self, capability: str) -> None:
        if capability.startswith("training.") or capability.startswith("gold."):
            raise PluginBusError("TRAINING_OR_GOLD_ROUTE_NOT_EXPOSED")
        self.providers_for(capability)

    def build_request(
        self,
        *,
        request_id: str,
        caller_id: str,
        capability: str,
        namespace: str,
        payload_ref_or_query: Any,
        provenance_ref: Any = None,
        evidence_requirement: str = "CLAIM_LE_EVIDENCE",
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        self.assert_route_allowed(capability)
        self.namespace(namespace)
        request = {
            "request_id": request_id,
            "caller_id": caller_id,
            "capability": capability,
            "namespace": namespace,
            "payload_ref_or_query": payload_ref_or_query,
            "provenance_ref": provenance_ref,
            "evidence_requirement": evidence_requirement,
            "timestamp": timestamp,
        }
        encoded = json.dumps(
            request, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        request["request_sha256"] = hashlib.sha256(encoded).hexdigest()
        return request

    def live_route(self) -> tuple[str, ...]:
        route = tuple(str(x) for x in self.registry.get("live_route", []))
        if "AELYS_PRESENTER" not in route or "ELYRA_AVATAR" not in route:
            raise PluginBusError("LIVE_ROUTE_INCOMPLETE")
        return route

    def self_test(self) -> dict[str, Any]:
        checked: dict[str, list[str]] = {}
        for capability in self.capabilities:
            checked[capability] = [p.provider_id for p in self.providers_for(capability)]

        gates = self.registry["gates"]
        if gates["global_f72"] != "FAIL":
            raise PluginBusError("SELFTEST_EXPECTED_CURRENT_F72_FAIL")
        if gates["m4_gold"] != "BLOCKED":
            raise PluginBusError("SELFTEST_GOLD_MUST_REMAIN_BLOCKED")
        if not str(gates["rdx_neural_training"]).startswith("DENY"):
            raise PluginBusError("SELFTEST_RDX_TRAINING_MUST_REMAIN_DENIED")

        sample = self.build_request(
            request_id="PLUGIN-BUS-SELFTEST-001",
            caller_id="AELYS_PRESENTER",
            capability="rdx.search",
            namespace="aelys_live",
            payload_ref_or_query={"query": "self-test only"},
            provenance_ref={"type": "SELF_TEST"},
            timestamp="SELF_TEST",
        )
        return {
            "schema": "CEREBRON_PLUGIN_BUS_SELFTEST_V1",
            "status": "PASS",
            "registry": str(self.registry_path),
            "capability_count": len(self.capabilities),
            "bindings": checked,
            "live_route": list(self.live_route()),
            "sample_request_sha256": sample["request_sha256"],
            "hf_private_repo": self.registry["private_data_plane"]["repo_id"],
            "hf_namespace": self.registry["namespaces"]["aelys_live"]["root"],
            "global_f72": gates["global_f72"],
            "m4_gold": gates["m4_gold"],
            "rdx_neural_training": gates["rdx_neural_training"],
            "claim_ceiling": "PLUGIN_DISCOVERY_AND_TYPED_ROUTING_CONTRACT_ONLY_NO_REMOTE_EXECUTION_CLAIM",
        }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    bus = CerebronPluginBus(args.registry)
    if args.self_test:
        print(json.dumps(bus.self_test(), ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(json.dumps({
            "schema": "CEREBRON_PLUGIN_BUS_STATUS_V1",
            "status": "READY",
            "capabilities": list(bus.capabilities),
            "live_route": list(bus.live_route()),
        }, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
