#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

failure=load("memory/failure-bank-v1.json")
routing=load("config/cerebron-failure-curriculum-routing-v1.json")
coverage=load("config/all-ai-neural-training-coverage-v1.json")

available={e["identity"] for e in coverage["entries"] if e.get("available") is True}
classes={e["FAILURE_CLASS"] for e in failure["entries"]}
routes=routing.get("class_routes",{})
max_specs=int(routing.get("max_specialists_per_failure",5))
errors=[]

missing=sorted(classes-set(routes))
if missing:
    errors.append("UNROUTED_FAILURE_CLASSES:"+",".join(missing))

unknown=[]
oversized=[]
for cls,cfg in routes.items():
    specs=cfg.get("specialists",[])
    if len(specs)>max_specs:
        oversized.append(cls)
    for ident in specs:
        if ident not in available:
            unknown.append(cls+":"+ident)

if unknown:
    errors.append("UNAVAILABLE_ROUTE_TARGETS:"+",".join(sorted(unknown)))
if oversized:
    errors.append("ROUTE_EXCEEDS_MAX_SPECIALISTS:"+",".join(sorted(oversized)))

for fid,override in routing.get("explicit_failure_overrides",{}).items():
    if not any(e["FAILURE_ID"]==fid for e in failure["entries"]):
        errors.append("ORPHAN_OVERRIDE:"+fid)
    if len(override.get("specialists",[]))>max_specs:
        errors.append("OVERRIDE_EXCEEDS_MAX:"+fid)
    for ident in override.get("specialists",[]):
        if ident not in available:
            errors.append("OVERRIDE_UNAVAILABLE:"+fid+":"+ident)

report={
    "schema":"CEREBRON_FAILURE_CURRICULUM_ROUTING_GUARD_V1",
    "status":"PASS" if not errors else "FAIL",
    "failure_count":len(failure["entries"]),
    "failure_classes":sorted(classes),
    "route_classes":sorted(routes),
    "available_ai_count":len(available),
    "max_specialists_per_failure":max_specs,
    "errors":errors
}
out=ROOT/"artifacts/failure-curriculum-routing-guard.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,sort_keys=True))
if errors:
    raise SystemExit(1)
