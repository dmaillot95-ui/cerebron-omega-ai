from __future__ import annotations

import hashlib
import json
import pathlib
import time

from huggingface_memory import ensure_private_sigma_repo, probe, push_json


def main():
    ready=ensure_private_sigma_repo()
    seed={
        "schema":"CEREBRON_SIGMA_HF_BOOTSTRAP_V1",
        "sigma":"SIGMA",
        "farm_id":74,
        "purpose":"private GOLD/model/memory backend for SIGMA",
        "allowed_memory_classes":["M1","M2","M3","M4","M5","M7"],
        "training_forbidden_class":"M6",
        "created_at":time.time(),
    }
    provenance={
        "sha256":hashlib.sha256(json.dumps(seed,sort_keys=True).encode()).hexdigest(),
        "producer":"SIGMA_HF_BOOTSTRAP_V1",
        "evidence":"GitHub Actions authenticated HF_TOKEN",
    }
    written=push_json("bootstrap/sigma-connection-v1.json",seed,"M7",provenance)
    checked=probe()
    out={"ready":ready,"written":written,"probe":checked}
    path=pathlib.Path("platform/artifacts/sigma-hf-bootstrap-v1.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(out,ensure_ascii=False))
    if checked.get("probe")!="AUTHENTICATED_REPO_ACCESSIBLE":
        raise SystemExit("HF_REPO_PROBE_FAILED")


if __name__=="__main__":
    main()
