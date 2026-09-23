from __future__ import annotations

import argparse
import json
import mimetypes
import pathlib
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from mission_engine import ARTIFACTS, ROOT, create_mission, rows
from model_router import catalog, infer

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

    def do_POST(self):
        try:
            if self.path == "/api/missions":
                data = self._body()
                prompt = str(data.get("prompt", "")).strip()
                if not prompt:
                    return self._json({"error": "prompt required"}, 400)
                return self._json(create_mission(prompt, data.get("session_id")), 202)
            if self.path == "/api/models/infer":
                data = self._body()
                return self._json(infer(str(data.get("text", ""))))
            return self._json({"error": "not found"}, 404)
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json({"error": str(exc)}, 400)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            farms = load_json(ROOT / "config/farms.json")["farms"]
            return self._json({"status": "healthy", "time": time.time(), "farm_count": len(farms),
                               "model": catalog()[0], "database": "sqlite", "cost_policy": "ZERO_PAID_OVERAGE_DEFAULT"})
        if path == "/api/farms":
            farms = load_json(ROOT / "config/farms.json")["farms"]
            enriched = [{**farm, "farm_id": f"F{farm['id']:03d}", "worker": "UNAVAILABLE",
                         "health": "DECLARED", "engine": None} for farm in farms]
            return self._json({"count": len(enriched), "farms": enriched})
        if path == "/api/models":
            return self._json({"models": catalog()})
        if path == "/api/roles":
            names = ["CÉRÉBRON", "SAPHEA", "SPIRALION", "ETHERION", "HYPERION", "ASTRION", "METRION", "AFAH", "AÉLYS", "ELYRA", "SAPHEA MICRO"]
            return self._json({"roles": [{"name": n, "type": "LOGICAL_ROLE", "model": None, "status": "UNAVAILABLE"} for n in names]})
        if path == "/api/missions":
            return self._json({"missions": rows("SELECT * FROM missions ORDER BY created_at DESC LIMIT 50")})
        if path.startswith("/api/missions/"):
            mission_id = path.split("/")[3]
            mission = rows("SELECT * FROM missions WHERE mission_id=?", (mission_id,))
            if not mission:
                return self._json({"error": "not found"}, 404)
            data = mission[0]
            if data.get("result_json"):
                data["result"] = json.loads(data.pop("result_json"))
            data["tasks"] = rows("SELECT * FROM tasks WHERE mission_id=? ORDER BY start_time", (mission_id,))
            data["events"] = rows("SELECT * FROM events WHERE mission_id=? ORDER BY id", (mission_id,))
            data["evidence"] = rows("SELECT * FROM evidence WHERE mission_id=?", (mission_id,))
            data["agora"] = rows("SELECT * FROM agora WHERE mission_id=?", (mission_id,))
            return self._json(data)
        if path == "/api/agora":
            return self._json({"capsules": rows("SELECT * FROM agora ORDER BY created_at DESC LIMIT 100")})
        if path == "/api/evidence":
            return self._json({"evidence": rows("SELECT * FROM evidence ORDER BY created_at DESC LIMIT 100")})
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
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CÉRÉBRON AI Platform: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

