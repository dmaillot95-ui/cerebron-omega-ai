#!/usr/bin/env python3
import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/"config/micro-model-benchmark-v1.json").read_text())
out=ROOT/"artifacts"/"micro_model_benchmark"
out.mkdir(parents=True,exist_ok=True)
manifest={"schema":"MICRO_MODEL_BENCHMARK_MANIFEST_V1","execution":"NOT_EXECUTED","candidates":[]}
for c in cfg["candidates"]:
    manifest["candidates"].append({"id":c["id"],"model":c["model"],"license":c["license"],"state":"READY_FOR_RUNTIME_PROBE","results":None})
raw=json.dumps(manifest,sort_keys=True).encode()
manifest["sha256"]=hashlib.sha256(raw).hexdigest()
(out/"manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
