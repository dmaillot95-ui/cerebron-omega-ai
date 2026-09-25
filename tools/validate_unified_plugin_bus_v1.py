#!/usr/bin/env python3
import json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
bus=json.loads((R/"config/cerebron-unified-plugin-bus-v1.json").read_text())
farms=json.loads((R/"config/farms.json").read_text())
by_id={f["id"]:f for f in farms["farms"]}

assert bus["schema"]=="CEREBRON_UNIFIED_PLUGIN_BUS_V1"
assert bus["automatic_external_calls"] is False
assert bus["automatic_training"] is False
assert bus["paid_provider_auto_activation"] is False

assert by_id[152]["identity"]=="BETA"
assert bus["routes"]["rdx.search"]=="RDX_EXCHANGE"
assert bus["routes"]["rdx.fetch"]=="RDX_EXCHANGE"
assert "F152_RDX" not in bus["providers"]
assert bus["providers"]["RDX_EXCHANGE"]["repository"]=="dmaillot95-ui/cerebron-rdx-exchange"
assert bus["providers"]["RDX_EXCHANGE"]["runtime_status"]=="UNBOUND"

assert by_id[173]["identity"]=="AELYS"
assert by_id[173]["repository_initialized"] is True
assert bus["providers"]["AELYS"]["farm_id"]==173
assert bus["providers"]["AELYS"]["runtime_status"]=="BASE_INSTALLED_ADAPTERS_UNQUALIFIED"

for capability, provider in bus["routes"].items():
    assert provider in bus["providers"], (capability,provider)
    assert capability in bus["providers"][provider]["capabilities"], (capability,provider)

assert bus["invariants"]["f152_identity"]=="BETA"
assert bus["invariants"]["f152_must_not_route_rdx"] is True
assert bus["invariants"]["unknown_capability"]=="DENY"

print(json.dumps({
  "status":"PASS",
  "rdx_provider":"RDX_EXCHANGE",
  "rdx_runtime":"UNBOUND",
  "f152_identity":"BETA",
  "f173_runtime":"BASE_INSTALLED_ADAPTERS_UNQUALIFIED",
  "automatic_external_calls":False,
  "automatic_training":False
},sort_keys=True))
