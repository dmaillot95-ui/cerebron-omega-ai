from __future__ import annotations

import argparse
import json
import mimetypes
import os
import pathlib
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from mission_engine import ARTIFACTS, ROOT, create_mission, rows
from model_router import catalog, infer
from farm_bridge import PILOTS
from security import SecurityError, audit as security_audit, authenticate, check_origin, rate_limit, require

HERE = pathlib.Path(__file__).resolve().parent
STATIC = HERE / "static"


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    server_version = "CerebronMVP/1.0"

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 1_000_000:
            raise ValueError("payload too large")
        return json.loads(self.rfile.read(size) or b"{}")

    def _principal(self):
        return authenticate(self.headers.get("Authorization"))

    def _guard(self, permission: str, bucket: str, limit: int):
        principal = self._principal()
        require(principal, permission)
        check_origin(self.headers.get("Origin"), self.headers.get("Host"))
        rate_limit(principal, bucket, limit)
        return principal

    def _security_error(self, exc: SecurityError):
        security_audit(None, self.command + " " + self.path, exc.code)
        return self._json({"error": exc.code}, exc.status)

    def do_POST(self):
        principal = None
        try:
            principal = self._guard("mission:create" if self.path == "/api/missions" else "model:infer", "write", 20)
            if self.path == "/api/missions":
                data = self._body()
                prompt = str(data.get("prompt", "")).strip()
                if not prompt:
                    return self._json({"error": "prompt required"}, 400)
                created = create_mission(prompt, data.get("session_id"), principal.user_id)
                security_audit(principal, "mission:create", "ALLOW", {"mission_id": created["mission_id"]})
                return self._json(created, 202)
            if self.path == "/api/models/infer":
                data = self._body()
                return self._json(infer(str(data.get("text", ""))))
            return self._json({"error": "not found"}, 404)
        except SecurityError as exc:
            return self._security_error(exc)
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json({"error": str(exc)}, 400)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            principal = self._guard("read", "read", 120)
        except SecurityError as exc:
            return self._security_error(exc)
        if path == "/api/control-plane":
            cfg = load_json(ROOT / "config/platform-control-plane-v1.json")
            return self._json({"control_plane": cfg, "runtime": {"bind_policy": "LOOPBACK_ONLY", "farm_count_effect": 0}})
        if path == "/api/health":
            farms = load_json(ROOT / "config/farms.json")["farms"]
            token_ready = bool(os.getenv("CEREBRON_GITHUB_TOKEN", "").strip())
            bridge_state = "READY" if token_ready else "CONFIGURED_TOKEN_REQUIRED"
            return self._json({"status": "healthy", "time": time.time(), "farm_count": len(farms),
                               "model": catalog()[0], "database": "sqlite", "cost_policy": "ZERO_PAID_OVERAGE_DEFAULT",
                               "farm_bridge": bridge_state})
        if path == "/api/farms":
            farms = load_json(ROOT / "config/farms.json")["farms"]
            token_ready = bool(os.getenv("CEREBRON_GITHUB_TOKEN", "").strip())
            enriched = []
            for farm in farms:
                pilot = farm["id"] in PILOTS
                enriched.append({
                    **farm,
                    "farm_id": f"F{farm['id']:03d}",
                    "status": "BRIDGE_PILOT_CONFIGURED" if pilot else farm.get("status", "DECLARED"),
                    "worker": "github-actions-farm-worker" if pilot else "UNAVAILABLE",
                    "health": ("READY" if token_ready else "CREDENTIAL_REQUIRED") if pilot else "DECLARED",
                    "engine": "CEREBRON_FARM_BRIDGE_V1" if pilot else None,
                })
            return self._json({"count": len(enriched), "farms": enriched})
        if path == "/api/models":
            return self._json({"models": catalog()})
        if path == "/api/roles":
            names = ["CÉRÉBRON", "SAPHEA", "SPIRALION", "ETHERION", "HYPERION", "ASTRION", "METRION", "AFAH", "AÉLYS", "ELYRA", "SAPHEA MICRO"]
            return self._json({"roles": [{"name": n, "type": "LOGICAL_ROLE", "model": None, "status": "UNAVAILABLE"} for n in names]})
        if path == "/api/missions":
            if principal.is_admin:
                missions = rows("SELECT * FROM missions ORDER BY created_at DESC LIMIT 50")
            else:
                missions = rows("SELECT * FROM missions WHERE owner_id=? ORDER BY created_at DESC LIMIT 50", (principal.user_id,))
            return self._json({"missions": missions})
        if path.startswith("/api/missions/"):
            mission_id = path.split("/")[3]
            mission = rows("SELECT * FROM missions WHERE mission_id=?", (mission_id,))
            if not mission:
                return self._json({"error": "not found"}, 404)
            data = mission[0]
            if not principal.is_admin and data.get("owner_id") != principal.user_id:
                security_audit(principal, "mission:read", "DENY", {"mission_id": mission_id})
                return self._json({"error": "not found"}, 404)
            if data.get("result_json"):
                data["result"] = json.loads(data.pop("result_json"))
            data["tasks"] = rows("SELECT * FROM tasks WHERE mission_id=? ORDER BY start_time", (mission_id,))
            data["events"] = rows("SELECT * FROM events WHERE mission_id=? ORDER BY id", (mission_id,))
            data["evidence"] = rows("SELECT * FROM evidence WHERE mission_id=?", (mission_id,))
            data["agora"] = rows("SELECT * FROM agora WHERE mission_id=?", (mission_id,))
            return self._json(data)
        if path == "/api/agora":
            if principal.is_admin:
                capsules = rows("SELECT * FROM agora ORDER BY created_at DESC LIMIT 100")
            else:
                capsules = rows("""SELECT a.* FROM agora a JOIN missions m ON m.mission_id=a.mission_id
                                  WHERE m.owner_id=? ORDER BY a.created_at DESC LIMIT 100""", (principal.user_id,))
            return self._json({"capsules": capsules})
        if path == "/api/evidence":
            if principal.is_admin:
                evidence = rows("SELECT * FROM evidence ORDER BY created_at DESC LIMIT 100")
            else:
                evidence = rows("""SELECT e.* FROM evidence e JOIN missions m ON m.mission_id=e.mission_id
                                 WHERE m.owner_id=? ORDER BY e.created_at DESC LIMIT 100""", (principal.user_id,))
            return self._json({"evidence": evidence})
        if path == "/api/memory":
            cfg = load_json(ROOT / "config/memory-fabric-v1.json")
            return self._json({"config": cfg, "levels": [
                {"id": "M0", "name": "EPHEMERAL", "status": "ACTIVE"}, {"id": "M1", "name": "TRACE", "status": "ACTIVE"},
                {"id": "M2", "name": "REPLAY", "status": "CONFIGURED"}, {"id": "M3", "name": "WARM", "status": "CONFIGURED"},
                {"id": "M4", "name": "GOLD", "status": "GATED"}, {"id": "M5", "name": "MODEL", "status": "UNAVAILABLE"},
                {"id": "M6", "name": "COLD BENCHMARK", "status": "CONFIGURED"}, {"id": "M7", "name": "EVIDENCE", "status": "ACTIVE"}]})
        if path.startswith("/api/artifacts/"):
            name = pathlib.Path(path).name
            target = ARTIFACTS / name
            if not target.exists() or target.parent != ARTIFACTS:
                return self._json({"error": "not found"}, 404)
            if not principal.is_admin:
                allowed = rows("""SELECT e.evidence_id FROM evidence e JOIN missions m ON m.mission_id=e.mission_id
                                 WHERE m.owner_id=? AND e.source LIKE ? LIMIT 1""",
                               (principal.user_id, "%" + name))
                if not allowed:
                    security_audit(principal, "artifact:read", "DENY", {"artifact": name})
                    return self._json({"error": "not found"}, 404)
            payload = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        target = STATIC / ("index.html" if path == "/" else path.lstrip("/"))
        if not target.exists() or STATIC not in target.resolve().parents:
            return self._json({"error": "not found"}, 404)
        payload = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(json.dumps({"time": time.time(), "client": self.client_address[0], "message": fmt % args}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("REMOTE_BIND_BLOCKED: authentication/RBAC/isolation are not implemented; use loopback only")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CÉRÉBRON AI Platform: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

