#!/usr/bin/env python3
import json, pathlib, os, sys, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/"config/engine-bindings-v1.json").read_text())
name=sys.argv[1].upper()
b=cfg["bindings"].get(name)
if not b: raise SystemExit("UNKNOWN_IDENTITY")
if b["provider"]=="ORCHESTRATOR":
    print(json.dumps({"identity":name,"state":"ROUTER_ONLY","farm":b.get("farm"),"neural_execution":False}))
    raise SystemExit(0)
if b["provider"]=="UNBOUND":
    print(json.dumps({"identity":name,"state":"BLOCKED_UNBOUND","neural_execution":False}))
    raise SystemExit(2)
required=[b.get("endpoint_env"),b.get("model_env")]
missing=[x for x in required if x and not os.getenv(x)]
if missing:
    print(json.dumps({"identity":name,"state":"BLOCKED_MISSING_ENV","missing":missing,"neural_execution":False}))
    raise SystemExit(3)
print(json.dumps({"identity":name,"state":"BINDING_CONFIGURED_NOT_EXECUTED","provider":b["provider"],"neural_execution":False}))
