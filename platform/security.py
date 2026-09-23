from __future__ import annotations

import hashlib
import hmac
import json
import os
import pathlib
import sqlite3
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

HERE = pathlib.Path(__file__).resolve().parent
AUDIT_LOG = HERE / "data" / "security-audit.jsonl"
RATE_DB = HERE / "data" / "security-rate-limit.db"
_LOCK = threading.Lock()
ZERO_HASH = "0" * 64

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


def _canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


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
        token_id = str(rec.get("token_id", user_id)).strip()
        roles = tuple(sorted({str(r).strip() for r in rec.get("roles", []) if str(r).strip()}))
        try:
            not_before = None if rec.get("not_before") is None else float(rec["not_before"])
            expires_at = None if rec.get("expires_at") is None else float(rec["expires_at"])
        except (TypeError, ValueError) as exc:
            raise SecurityError("AUTH_CONFIG_INVALID", 500) from exc
        if (
            not user_id
            or not token_id
            or len(token_sha256) != 64
            or not roles
            or any(r not in ROLE_PERMISSIONS for r in roles)
            or (not_before is not None and expires_at is not None and not_before >= expires_at)
        ):
            raise SecurityError("AUTH_CONFIG_INVALID", 500)
        clean.append({
            "user_id": user_id,
            "token_id": token_id,
            "token_sha256": token_sha256,
            "roles": roles,
            "not_before": not_before,
            "expires_at": expires_at,
        })
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
    now = time.time()
    for rec in records:
        if not hmac.compare_digest(digest, rec["token_sha256"]):
            continue
        if rec["not_before"] is not None and now < rec["not_before"]:
            raise SecurityError("AUTH_INVALID", 401)
        if rec["expires_at"] is not None and now >= rec["expires_at"]:
            raise SecurityError("AUTH_INVALID", 401)
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


def _rate_connect():
    RATE_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(RATE_DB, timeout=5)
    con.execute(
        "CREATE TABLE IF NOT EXISTS rate_events("
        "user_id TEXT NOT NULL,bucket TEXT NOT NULL,ts REAL NOT NULL)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_rate_events ON rate_events(user_id,bucket,ts)")
    return con


def rate_limit(principal: Principal, bucket: str, limit: int, window_s: int = 60) -> None:
    if limit < 1 or window_s < 1:
        raise SecurityError("RATE_LIMIT_CONFIG_INVALID", 500)
    now = time.time()
    cutoff = now - window_s
    with _LOCK:
        con = _rate_connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute("DELETE FROM rate_events WHERE ts < ?", (cutoff,))
            count = con.execute(
                "SELECT COUNT(*) FROM rate_events WHERE user_id=? AND bucket=? AND ts>=?",
                (principal.user_id, bucket, cutoff),
            ).fetchone()[0]
            if count >= limit:
                con.rollback()
                raise SecurityError("RATE_LIMITED", 429)
            con.execute(
                "INSERT INTO rate_events(user_id,bucket,ts) VALUES(?,?,?)",
                (principal.user_id, bucket, now),
            )
            con.commit()
        finally:
            con.close()


def reset_rate_limits() -> None:
    with _LOCK:
        con = _rate_connect()
        try:
            con.execute("DELETE FROM rate_events")
            con.commit()
        finally:
            con.close()


def _last_audit_hash() -> str:
    if not AUDIT_LOG.exists():
        return ZERO_HASH
    last = None
    with AUDIT_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = line
    if last is None:
        return ZERO_HASH
    try:
        value = json.loads(last)
    except json.JSONDecodeError:
        return "INVALID"
    return str(value.get("event_hash", "INVALID"))


def audit(principal: Principal | None, action: str, outcome: str, details: dict | None = None) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        event = {
            "time": time.time(),
            "user_id": principal.user_id if principal else None,
            "roles": list(principal.roles) if principal else [],
            "action": action,
            "outcome": outcome,
            "details": details or {},
            "previous_hash": _last_audit_hash(),
        }
        event["event_hash"] = hashlib.sha256(_canonical(event)).hexdigest()
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def verify_audit_chain(path: pathlib.Path | None = None) -> dict:
    target = path or AUDIT_LOG
    if not target.exists():
        return {"valid": True, "events": 0, "last_hash": ZERO_HASH}
    previous = ZERO_HASH
    count = 0
    with target.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return {"valid": False, "events": count, "line": lineno, "reason": "INVALID_JSON"}
            saved_hash = str(event.pop("event_hash", ""))
            if event.get("previous_hash") != previous:
                return {"valid": False, "events": count, "line": lineno, "reason": "PREVIOUS_HASH_MISMATCH"}
            calculated = hashlib.sha256(_canonical(event)).hexdigest()
            if not hmac.compare_digest(saved_hash, calculated):
                return {"valid": False, "events": count, "line": lineno, "reason": "EVENT_HASH_MISMATCH"}
            previous = saved_hash
            count += 1
    return {"valid": True, "events": count, "last_hash": previous}
