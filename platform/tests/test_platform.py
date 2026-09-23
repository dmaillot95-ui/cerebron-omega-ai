import json
import hashlib
import json
import os
import pathlib
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from mission_engine import ARTIFACTS, create_mission, rows, sha256_bytes
from model_router import MODEL_REVISION, infer
from farm_bridge import FarmBridgeError, PILOTS, submit
from security import SecurityError, authenticate, check_origin, rate_limit, reset_rate_limits, require
from server import Handler
from generative_backend import MODEL_ID as GENERATIVE_MODEL_ID, REVISION as GENERATIVE_REVISION, status as generative_status
from coalition import execute as coalition_execute, plan as coalition_plan, registry as coalition_registry


class PlatformTests(unittest.TestCase):
    def test_neural_router_is_real_and_versioned(self):
        result = infer("rover lunaire en orbite")
        self.assertEqual(result["label"], "space")
        self.assertEqual(result["revision"], MODEL_REVISION)
        self.assertAlmostEqual(sum(result["scores"].values()), 1.0, places=5)

    def test_registry_has_exactly_144_unique_farms(self):
        root = PLATFORM.parent
        farms = json.loads((root / "config/farms.json").read_text())["farms"]
        self.assertEqual(len(farms), 144)
        self.assertEqual({f["id"] for f in farms}, set(range(1, 145)))

    def test_rover_mission_produces_evidence_and_artifact(self):
        created = create_mission("Concevoir un rover lunaire autonome et calculer sa traction")
        for _ in range(100):
            mission = rows("SELECT * FROM missions WHERE mission_id=?", (created["mission_id"],))[0]
            if mission["status"] in {"COMPLETED", "FAILED"}:
                break
            time.sleep(0.03)
        self.assertEqual(mission["status"], "COMPLETED")
        tasks = rows("SELECT * FROM tasks WHERE mission_id=?", (created["mission_id"],))
        self.assertGreaterEqual(len(tasks), 5)
        self.assertTrue(all(t["status"] == "COMPLETED" for t in tasks))
        evidence = rows("SELECT * FROM evidence WHERE mission_id=?", (created["mission_id"],))
        self.assertEqual(len(evidence), 1)
        artifact = ARTIFACTS / pathlib.Path(evidence[0]["source"]).name
        self.assertTrue(artifact.exists())
        self.assertEqual(sha256_bytes(artifact.read_bytes()), evidence[0]["sha"])
        agora = rows("SELECT * FROM agora WHERE mission_id=?", (created["mission_id"],))
        self.assertEqual(agora[0]["state"], "UNDER_TEST")


    def test_f123_bridge_contract_is_registered(self):
        self.assertIn(123, PILOTS)
        self.assertEqual(PILOTS[123]["workflow"], "control-plane-bridge-v1.yml")
        self.assertIn("hohmann_reference", PILOTS[123]["operations"])

    def test_farm_bridge_fails_closed_without_token(self):
        with mock.patch.dict(os.environ, {"CEREBRON_GITHUB_TOKEN": ""}, clear=False):
            with self.assertRaises(FarmBridgeError) as ctx:
                submit(123, "hohmann_reference", {}, "mis_test", "task_test")
        self.assertEqual(str(ctx.exception), "GITHUB_TOKEN_UNAVAILABLE")

    def test_orbital_mission_does_not_fake_farm_execution_without_token(self):
        with mock.patch.dict(os.environ, {"CEREBRON_GITHUB_TOKEN": ""}, clear=False):
            created = create_mission("Calculer un transfert Hohmann orbital avec F123")
            for _ in range(100):
                mission = rows("SELECT * FROM missions WHERE mission_id=?", (created["mission_id"],))[0]
                if mission["status"] in {"COMPLETED", "FAILED"}:
                    break
                time.sleep(0.03)
        self.assertEqual(mission["status"], "COMPLETED")
        result = json.loads(mission["result_json"])
        self.assertEqual(result["farm_bridge"]["status"], "ROUTED_ONLY")
        bridge_tasks = rows("SELECT * FROM tasks WHERE mission_id=? AND farm_id=123", (created["mission_id"],))
        self.assertEqual(len(bridge_tasks), 1)
        self.assertEqual(bridge_tasks[0]["status"], "ROUTED_ONLY")


    def test_security_local_mode_is_admin(self):
        with mock.patch.dict(os.environ, {"CEREBRON_RBAC_TOKENS_JSON": ""}, clear=False):
            principal = authenticate(None)
        self.assertTrue(principal.is_admin)
        require(principal, "mission:create")

    def test_security_token_hash_and_rbac(self):
        import hashlib
        token = "unit-test-secret"
        cfg = json.dumps([{
            "user_id": "alice",
            "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "roles": ["viewer"],
        }])
        with mock.patch.dict(os.environ, {"CEREBRON_RBAC_TOKENS_JSON": cfg}, clear=False):
            principal = authenticate("Bearer " + token)
            self.assertEqual(principal.user_id, "alice")
            require(principal, "read")
            with self.assertRaises(SecurityError):
                require(principal, "mission:create")
            with self.assertRaises(SecurityError):
                authenticate("Bearer wrong")

    def test_security_origin_and_rate_limit_fail_closed(self):
        check_origin("http://127.0.0.1:8787", "127.0.0.1:8787")
        with self.assertRaises(SecurityError):
            check_origin("https://evil.example", "127.0.0.1:8787")
        reset_rate_limits()
        with mock.patch.dict(os.environ, {"CEREBRON_RBAC_TOKENS_JSON": ""}, clear=False):
            principal = authenticate(None)
        rate_limit(principal, "test", 1, 60)
        with self.assertRaises(SecurityError):
            rate_limit(principal, "test", 1, 60)

    def test_mission_owner_is_persisted(self):
        created = create_mission("simple request", owner_id="owner-test")
        for _ in range(100):
            mission = rows("SELECT * FROM missions WHERE mission_id=?", (created["mission_id"],))[0]
            if mission["status"] in {"COMPLETED", "FAILED"}:
                break
            time.sleep(0.03)
        self.assertEqual(mission["owner_id"], "owner-test")


    def test_http_auth_rbac_and_owner_isolation(self):
        admin_token = "admin-unit-secret"
        viewer_token = "viewer-unit-secret"
        operator_token = "operator-unit-secret"
        cfg = json.dumps([
            {"user_id": "admin", "token_sha256": hashlib.sha256(admin_token.encode()).hexdigest(), "roles": ["admin"]},
            {"user_id": "viewer", "token_sha256": hashlib.sha256(viewer_token.encode()).hexdigest(), "roles": ["viewer"]},
            {"user_id": "operator", "token_sha256": hashlib.sha256(operator_token.encode()).hexdigest(), "roles": ["operator"]},
        ])
        reset_rate_limits()
        with mock.patch.dict(os.environ, {"CEREBRON_RBAC_TOKENS_JSON": cfg}, clear=False):
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(base + "/", timeout=2) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
                    self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
                    self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
                    self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy", ""))

                with self.assertRaises(urllib.error.HTTPError) as unauth:
                    urllib.request.urlopen(base + "/api/missions", timeout=2)
                self.assertEqual(unauth.exception.code, 401)

                req = urllib.request.Request(
                    base + "/api/missions",
                    headers={"Authorization": "Bearer " + viewer_token},
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                    self.assertEqual(response.status, 200)

                body = json.dumps({"prompt": "owner isolation test"}).encode()
                req = urllib.request.Request(
                    base + "/api/missions",
                    data=body,
                    method="POST",
                    headers={"Authorization": "Bearer " + viewer_token, "Content-Type": "application/json"},
                )
                with self.assertRaises(urllib.error.HTTPError) as forbidden:
                    urllib.request.urlopen(req, timeout=2)
                self.assertEqual(forbidden.exception.code, 403)

                req = urllib.request.Request(
                    base + "/api/missions",
                    data=body,
                    method="POST",
                    headers={"Authorization": "Bearer " + operator_token, "Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                    created = json.loads(response.read())
                mission_id = created["mission_id"]

                req = urllib.request.Request(
                    base + "/api/missions/" + mission_id,
                    headers={"Authorization": "Bearer " + viewer_token},
                )
                with self.assertRaises(urllib.error.HTTPError) as isolated:
                    urllib.request.urlopen(req, timeout=2)
                self.assertEqual(isolated.exception.code, 404)

                req = urllib.request.Request(
                    base + "/api/missions/" + mission_id,
                    headers={"Authorization": "Bearer " + operator_token},
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                    owned = json.loads(response.read())
                self.assertEqual(owned["owner_id"], "operator")

                req = urllib.request.Request(
                    base + "/api/missions",
                    headers={
                        "Authorization": "Bearer " + operator_token,
                        "Origin": "https://evil.example",
                    },
                )
                with self.assertRaises(urllib.error.HTTPError) as origin:
                    urllib.request.urlopen(req, timeout=2)
                self.assertEqual(origin.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


    def test_qualified_generative_model_is_registered_but_fail_closed_by_default(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            st = generative_status()
        self.assertEqual(st["model_id"], GENERATIVE_MODEL_ID)
        self.assertEqual(st["revision"], GENERATIVE_REVISION)
        self.assertEqual(st["benchmark_evidence"]["score"], 5)
        self.assertEqual(st["status"], "CONFIGURED_DISABLED")


    def test_saphea_micro_registry_has_20_units_and_only_7_implemented_initially(self):
        reg = coalition_registry()
        self.assertEqual(len(reg["units"]), 20)
        self.assertEqual(
            set(reg["implemented_initial"]),
            {"SM00", "SM02", "SM05", "SM08", "SM11", "SM15", "SM18"},
        )
        planned = [u for u in reg["units"] if u["status"] == "PLANNED_UNAVAILABLE"]
        self.assertEqual(len(planned), 13)

    def test_minimal_coalition_does_not_launch_20_units(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            plan = coalition_plan("Démontrer une équation mathématique")
        self.assertIn("SM02", plan["selected_units"])
        self.assertIn("SM15", plan["selected_units"])
        self.assertIn("SM18", plan["selected_units"])
        self.assertLess(len(plan["selected_units"]), 20)
        self.assertEqual(plan["independent_model_count"], 0)

    def test_coalition_fails_closed_when_generative_runtime_disabled(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            result = coalition_execute("Démontrer une équation mathématique")
        self.assertEqual(result["status"], "ROUTED_ONLY")
        self.assertIsNone(result["answer"])
        self.assertEqual(result["claim_ceiling"], "NO_MODEL_OUTPUT")


    def test_memory_worker_is_not_executed_when_not_selected(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            result = coalition_execute("Démontrer une équation mathématique")
        self.assertNotIn("SM11", result["workers"])
        self.assertNotIn("SM11", result["plan"]["selected_units"])

    def test_memory_hint_selects_sm11(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            plan = coalition_plan("Rappelle le checkpoint mémoire AGORA précédent")
        self.assertIn("SM11", plan["selected_units"])

    def test_general_route_uses_base_generator_not_fusion_as_generator(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            plan = coalition_plan("Bonjour, explique simplement ce sujet")
        if plan["route"]["label"] == "general":
            self.assertEqual(plan["primary"], "BASE_QWEN")
            self.assertIn("SM18", plan["selected_units"])


if __name__ == "__main__":
    unittest.main()

