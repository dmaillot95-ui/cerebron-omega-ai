import json
import pathlib
import sys
import time
import unittest

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from mission_engine import ARTIFACTS, create_mission, rows, sha256_bytes
from model_router import MODEL_REVISION, infer


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


if __name__ == "__main__":
    unittest.main()

