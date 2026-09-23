from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"config"/"remote-deployment-security-v1.json"
SERVER=ROOT/"platform"/"server.py"
SECURITY=ROOT/"platform"/"security.py"
OUT=ROOT/"platform"/"artifacts"/"remote-deployment-security-audit-v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cfg=json.loads(MANIFEST.read_text())
    server=SERVER.read_text()
    security=SECURITY.read_text()

    controls={
        "manifest_remote_blocked": cfg["status"]=="REMOTE_DEPLOYMENT_BLOCKED" and cfg["remote_exposure_authorized"] is False,
        "server_loopback_default": 'default="127.0.0.1"' in server,
        "server_rejects_non_loopback": "REMOTE_BIND_BLOCKED" in server and 'args.host not in {"127.0.0.1", "localhost", "::1"}' in server,
        "hashed_bearer_auth": "hmac.compare_digest" in security and "token_sha256" in security,
        "rbac_present": "ROLE_PERMISSIONS" in security and "require(" in security,
        "owner_isolation_present": "owner_id" in server,
        "origin_check_present": "check_origin" in security and "check_origin(" in server,
        "rate_limit_present": "rate_limit" in security and "rate_limit(" in server,
        "persistent_local_rate_limit": "sqlite3" in security and "RATE_DB" in security,
        "tamper_evident_local_audit": "verify_audit_chain" in security and "previous_hash" in security,
        "credential_validity_windows": "not_before" in security and "expires_at" in security,
        "body_limit_present": "1_000_000" in server,
        "base_security_headers_present": (
            "X-Content-Type-Options" in server
            and "X-Frame-Options" in server
            and "Content-Security-Policy" in server
            and "Referrer-Policy" in server
        ),
    }
    blockers={k:v for k,v in cfg["blockers"].items() if not str(v).startswith("PASS")}
    safe=all(controls.values()) and bool(blockers)
    result={
        "schema":"CEREBRON_REMOTE_DEPLOYMENT_SECURITY_AUDIT_V1",
        "status":"REMOTE_DEPLOYMENT_BLOCKED_AS_DESIGNED" if safe else "SECURITY_AUDIT_FAILED",
        "controls":controls,
        "blockers":blockers,
        "server_sha256":sha(SERVER),
        "security_sha256":sha(SECURITY),
        "manifest_sha256":sha(MANIFEST),
        "remote_exposure_authorized":False,
        "claim_ceiling":"LOCAL_SECURITY_CONTROLS_VERIFIED_REMOTE_NOT_READY",
    }
    raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result["result_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    raise SystemExit(0 if safe else 1)


if __name__=="__main__":
    main()
