from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
AUDIT_LOG = HERE / "data" / "security-audit.jsonl"
_LOCK = threading.Lock()
_BUCKETS: dict[tuple[str, str], list[float]] = {}

ROLE_PERMISSIONS = {
    "viewer": {"read"},
    "operator": {"read", "mission:create", "model:infer"},
    "admin": {"read", "mission:create", "model:infer", "admin"},
}


class SecurityError(RuntimeError):
    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Principal:
    user_id: str
    roles: tuple[str, ...]

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def auth_configured() -> bool:
    return bool(os.getenv("CEREBRON_RBAC_TOKENS_JSON", "").strip())


def _records() -> list[dict]:
    raw = os.getenv("CEREBRON_RBAC_TOKENS_JSON", "").strip()
    if not raw:
        return []
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SecurityError("AUTH_CONFIG_INVALID", 500) from exc
    if not isinstance(records, list):
        raise SecurityError("AUTH_CONFIG_INVALID", 500)
    clean = []
    for rec in records:
        if not isinstance(rec, dict):
            raise SecurityError("AUTH_CONFIG_INVALID", 500)
        user_id = str(rec.get("user_id", "")).strip()
        token_sha256 = str(rec.get("token_sha256", "")).strip().lower()
        roles = tuple(sorted({str(r).strip() for r in rec.get("roles", []) if str(r).strip()}))
        if not user_id or len(token_sha256) != 64 or not roles or any(r not in ROLE_PERMISSIONS for r in roles):
            raise SecurityError("AUTH_CONFIG_INVALID", 500)
        clean.append({"user_id": user_id, "token_sha256": token_sha256, "roles": roles})
    return clean


def authenticate(authorization: str | None) -> Principal:
    records = _records()
    if not records:
        return Principal("local-owner", ("admin",))
    if not authorization or not authorization.startswith("Bearer "):
        raise SecurityError("AUTH_REQUIRED", 401)
    token = authorization[7:].strip()
    if not token:
        raise SecurityError("AUTH_REQUIRED", 401)
    digest = _sha256(token)
    for rec in records:
        if hmac.compare_digest(digest, rec["token_sha256"]):
            return Principal(rec["user_id"], rec["roles"])
    raise SecurityError("AUTH_INVALID", 401)


def require(principal: Principal, permission: str) -> None:
    granted = set()
    for role in principal.roles:
        granted.update(ROLE_PERMISSIONS.get(role, set()))
    if permission not in granted:
        raise SecurityError("FORBIDDEN", 403)


def check_origin(origin: str | None, host: str | None) -> None:
    if not origin:
        return
    parsed = urlparse(origin)
    if not parsed.netloc or not host or parsed.netloc != host:
        raise SecurityError("ORIGIN_REJECTED", 403)


def rate_limit(principal: Principal, bucket: str, limit: int, window_s: int = 60) -> None:
    now = time.time()
    key = (principal.user_id, bucket)
    with _LOCK:
        values = [t for t in _BUCKETS.get(key, []) if now - t < window_s]
        if len(values) >= limit:
            raise SecurityError("RATE_LIMITED", 429)
        values.append(now)
        _BUCKETS[key] = values


def reset_rate_limits() -> None:
    with _LOCK:
        _BUCKETS.clear()


def audit(principal: Principal | None, action: str, outcome: str, details: dict | None = None) -> None:
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    event = {
        "time": time.time(),
        "user_id": principal.user_id if principal else None,
        "roles": list(principal.roles) if principal else [],
        "action": action,
        "outcome": outcome,
        "details": details or {},
    }
    with _LOCK:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
