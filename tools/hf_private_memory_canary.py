#!/usr/bin/env python3
"""CEREBRON Hugging Face private-memory write/read/SHA canary.

This canary is deliberately fail-closed. It never creates a Hugging Face
repository, never trains a model, and never writes model weights. It writes a
small synthetic JSON object to an explicitly supplied existing PRIVATE repo,
reads the exact object back, and requires SHA-256 equality.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-id", required=True)
    p.add_argument("--repo-type", choices=("dataset", "model"), default="dataset")
    p.add_argument("--canary-id", required=True)
    p.add_argument("--receipt", default="artifacts/hf-private-memory-canary-receipt.json")
    return p.parse_args()


def attr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)


def main() -> int:
    args = parse_args()
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise SystemExit("FAIL_CLOSED: HF_TOKEN is missing")

    api = HfApi(token=token)
    info = api.repo_info(repo_id=args.repo_id, repo_type=args.repo_type, token=token)
    if not bool(attr(info, "private", False)):
        raise SystemExit("FAIL_CLOSED: target Hugging Face repository is not private")

    payload = {
        "schema": "CEREBRON_HF_PRIVATE_MEMORY_CANARY_V1",
        "canary_id": args.canary_id,
        "content_kind": "SYNTHETIC_MEMORY_CANARY",
        "contains_user_data": False,
        "contains_raw_agora": False,
        "contains_m6_cold_bench": False,
        "training_data": False,
        "training_executed": False,
        "weights_changed": False,
        "memory_ne_training": True,
    }
    payload_bytes = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    source_sha = sha256_bytes(payload_bytes)
    path_in_repo = f"cerebron-private-memory-canary/{source_sha}.json"

    work = Path("artifacts/hf-private-memory-canary")
    work.mkdir(parents=True, exist_ok=True)
    local_path = work / f"{source_sha}.json"
    local_path.write_bytes(payload_bytes)

    commit_info = api.upload_file(
        path_or_fileobj=str(local_path),
        path_in_repo=path_in_repo,
        repo_id=args.repo_id,
        repo_type=args.repo_type,
        token=token,
        commit_message=f"CEREBRON private-memory canary {args.canary_id}",
    )
    commit_oid = attr(commit_info, "oid")

    downloaded_path = hf_hub_download(
        repo_id=args.repo_id,
        filename=path_in_repo,
        repo_type=args.repo_type,
        revision=commit_oid or "main",
        token=token,
        force_download=True,
    )
    downloaded_bytes = Path(downloaded_path).read_bytes()
    downloaded_sha = sha256_bytes(downloaded_bytes)
    sha_match = source_sha == downloaded_sha and downloaded_bytes == payload_bytes
    if not sha_match:
        raise SystemExit("FAIL_CLOSED: write/read SHA mismatch")

    post_info = api.repo_info(repo_id=args.repo_id, repo_type=args.repo_type, token=token)
    if not bool(attr(post_info, "private", False)):
        raise SystemExit("FAIL_CLOSED: repository privacy check failed after write/read")

    receipt = {
        "schema": "CEREBRON_HF_PRIVATE_MEMORY_CANARY_RECEIPT_V1",
        "status": "PASS",
        "canary_id": args.canary_id,
        "repo_id": args.repo_id,
        "repo_type": args.repo_type,
        "private_verified_before": True,
        "private_verified_after": True,
        "repository_created": False,
        "automatic_paid_service": False,
        "path_in_repo": path_in_repo,
        "commit_oid": commit_oid,
        "sha256_before_write": source_sha,
        "sha256_after_read": downloaded_sha,
        "write_executed": True,
        "read_executed": True,
        "sha_match": True,
        "memory_backend_validated": True,
        "contains_user_data": False,
        "contains_raw_agora": False,
        "contains_m6_cold_bench": False,
        "training_executed": False,
        "weights_changed": False,
        "huggingface_hub_version": importlib.metadata.version("huggingface_hub"),
        "claim_boundary": "PRIVATE_REPO_WRITE_READ_SHA_CANARY_ONLY; MEMORY_NE_TRAINING",
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "write_executed": True,
        "read_executed": True,
        "sha_match": True,
        "training_executed": False,
        "weights_changed": False,
        "receipt": str(receipt_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
