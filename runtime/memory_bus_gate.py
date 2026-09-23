import hashlib, json, pathlib, sys, datetime

CONFIG = pathlib.Path("config/memory-fabric-v1.json")
OUT = pathlib.Path("artifacts/memory_bus_state.json")
FARMS = {
  114: "ENCYCLOPEDIC_INDEX",
  115: "VECTOR_SEMANTIC",
  116: "DEDUP_FUSION",
  117: "SIMULATION_REPLAY",
  118: "GOLD_LIBRARY",
  119: "EVIDENCE_ARCHIVE",
  120: "GOVERNOR_FREEZE",
}

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(65536),b""): h.update(chunk)
    return h.hexdigest()

cfg=json.loads(CONFIG.read_text())
em=cfg["emergency"]
required_principles={"CONTENT_ADDRESSABLE","DOMAIN_ISOLATION","DEDUP_BEFORE_WRITE","BENCHMARK_DENY_TRAINING","FAIL_CLOSED","ZERO_PAID_OVERAGE"}
principles_ok=required_principles.issubset(set(cfg["principles"]))
cold_ok=cfg["classes"]["M6"].get("deny_training") is True
freeze_ok=cfg.get("freeze")=="DRAIN_CHECKPOINT_VERIFY_READ_ONLY"
thresholds_ok=em=={"soft_pct":70,"compress_pct":80,"raw_stop_pct":90,"freeze_pct":95}

# Until a real run+artifact is supplied for each farm, the bus MUST remain DEGRADED.
components={str(k):{"role":v,"execution":"UNVERIFIED","artifact":"UNVERIFIED","ready":False} for k,v in FARMS.items()}
checks={
 "config_sha256":sha256_file(CONFIG),
 "principles_ok":principles_ok,
 "cold_benchmark_isolated":cold_ok,
 "freeze_policy_ok":freeze_ok,
 "thresholds_ok":thresholds_ok,
 "all_components_executed":all(x["ready"] for x in components.values())
}
policy_ok=all([principles_ok,cold_ok,freeze_ok,thresholds_ok])
state="READY" if policy_ok and checks["all_components_executed"] else ("DEGRADED" if policy_ok else "FREEZE")
out={
 "schema":"CEREBRON_MEMORY_BUS_STATE_V1",
 "generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "state":state,
 "write_mode":"READ_ONLY" if state!="READY" else "CONTROLLED_WRITE",
 "components":components,
 "checks":checks,
 "rule":"NO_READY_WITHOUT_REAL_RUN_PLUS_ARTIFACT_FOR_F114_F120"
}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out))
sys.exit(0 if state in ("READY","DEGRADED") else 2)
