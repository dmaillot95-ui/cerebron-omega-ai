from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import time


class HuggingFaceMemoryError(RuntimeError):
    pass


def _token() -> str:
    return os.getenv("HF_TOKEN","").strip() or os.getenv("HUGGING_FACE_HUB_TOKEN","").strip()


def _repo() -> str:
    return os.getenv("CEREBRON_HF_SIGMA_REPO","").strip()


def status() -> dict:
    token=bool(_token())
    repo=_repo()
    deps=importlib.util.find_spec("huggingface_hub") is not None
    if not token:
        state="CREDENTIAL_REQUIRED"
    elif not deps:
        state="DEPENDENCY_MISSING"
    elif not repo:
        state="AUTHENTICATION_PROBE_READY_REPO_NOT_CONFIGURED"
    else:
        state="READY_TO_PROBE"
    return {
        "schema":"CEREBRON_HF_MEMORY_STATUS_V1",
        "backend":"huggingface_private",
        "status":state,
        "token_present":token,
        "repo_id":repo or None,
        "dependencies_available":deps,
        "allowed_classes":["M1","M2","M3","M4","M5","M7"],
        "training_forbidden_class":"M6",
        "secret_policy":"TOKEN_ENV_ONLY_NEVER_COMMIT",
    }


def probe() -> dict:
    st=status()
    if not st["token_present"]:
        return {**st,"probe":"NOT_EXECUTED","reason":"HF_TOKEN_MISSING"}
    if not st["dependencies_available"]:
        return {**st,"probe":"NOT_EXECUTED","reason":"HUGGINGFACE_HUB_DEPENDENCY_MISSING"}
    from huggingface_hub import HfApi
    api=HfApi(token=_token())
    me=api.whoami()
    result={**st,"probe":"AUTHENTICATED","account":me.get("name") or me.get("fullname") or "AUTHENTICATED_USER"}
    if st["repo_id"]:
        try:
            info=api.repo_info(repo_id=st["repo_id"],repo_type="dataset")
            result.update({"probe":"AUTHENTICATED_REPO_ACCESSIBLE","repo_sha":getattr(info,"sha",None)})
        except Exception as exc:
            result.update({"probe":"AUTHENTICATED_REPO_UNAVAILABLE","repo_error":type(exc).__name__})
    return result


def push_json(relative_path: str, payload: dict, memory_class: str, provenance: dict) -> dict:
    if memory_class=="M6":
        raise HuggingFaceMemoryError("M6_TRAINING_MEMORY_WRITE_FORBIDDEN")
    if memory_class not in {"M1","M2","M3","M4","M5","M7"}:
        raise HuggingFaceMemoryError("MEMORY_CLASS_NOT_ALLOWED")
    st=status()
    if st["status"]!="READY_TO_PROBE":
        raise HuggingFaceMemoryError(st["status"])
    if not provenance or not provenance.get("sha256"):
        raise HuggingFaceMemoryError("PROVENANCE_SHA_REQUIRED")
    from huggingface_hub import HfApi
    api=HfApi(token=_token())
    body={
        "schema":"CEREBRON_SIGMA_MEMORY_OBJECT_V1",
        "memory_class":memory_class,
        "provenance":provenance,
        "payload":payload,
        "created_at":time.time(),
    }
    raw=json.dumps(body,ensure_ascii=False,sort_keys=True,indent=2).encode()
    sha=hashlib.sha256(raw).hexdigest()
    tmp=pathlib.Path("/tmp")/f"sigma-{sha}.json"
    tmp.write_bytes(raw)
    api.upload_file(
        path_or_fileobj=str(tmp),
        path_in_repo=relative_path,
        repo_id=_repo(),
        repo_type="dataset",
        commit_message=f"SIGMA memory {memory_class} {sha[:12]}",
    )
    return {"status":"WRITTEN","repo_id":_repo(),"path":relative_path,"sha256":sha,"memory_class":memory_class}
