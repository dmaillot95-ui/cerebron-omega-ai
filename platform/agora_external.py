from __future__ import annotations
import hashlib, json, time

REQUIRED={"participant_id","provider","model","session_id","message_id","content","content_sha256","timestamp","provenance"}

def canonical_content_sha(content: str) -> str:
    return hashlib.sha256(str(content).encode("utf-8")).hexdigest()

def admit(payload: dict) -> dict:
    missing=sorted(REQUIRED-set(payload))
    if missing:
        raise ValueError("MISSING_EXTERNAL_AGORA_FIELDS:"+",".join(missing))
    actual=canonical_content_sha(payload["content"])
    if actual != str(payload["content_sha256"]):
        raise ValueError("EXTERNAL_AGORA_SHA_MISMATCH")
    if not payload.get("provenance"):
        raise ValueError("EXTERNAL_AGORA_PROVENANCE_REQUIRED")
    return {
        "schema":"CEREBRON_AGORA_EXTERNAL_RECEIPT_V1",
        "status":"UNDER_TEST_EXTERNAL",
        "participant_id":payload["participant_id"],
        "provider":payload["provider"],
        "model":payload["model"],
        "session_id":payload["session_id"],
        "message_id":payload["message_id"],
        "content_sha256":actual,
        "received_at":time.time(),
        "independent_evidence":False,
        "promotion":"AUDIT_REQUIRED",
        "memory_backend":"cerebron-omega/cerebron-private-memory",
    }
