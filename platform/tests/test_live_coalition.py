import json
import os
import pathlib
import sys
import time
import unittest
from unittest import mock

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from mission_engine import create_mission, rows


class LiveCoalitionTests(unittest.TestCase):
    def test_live_math_mission_uses_deterministic_coalition_without_model(self):
        with mock.patch.dict(os.environ, {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            created = create_mission("Return only the number. Compute: 17*23")
            mission = None
            for _ in range(150):
                mission = rows("SELECT * FROM missions WHERE mission_id=?", (created["mission_id"],))[0]
                if mission["status"] in {"COMPLETED", "FAILED"}:
                    break
                time.sleep(0.02)

        self.assertIsNotNone(mission)
        self.assertEqual(mission["status"], "COMPLETED")
        result = json.loads(mission["result_json"])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["answer"], "391")
        self.assertEqual(result["claim_ceiling"], "DETERMINISTIC_TOOL_RESULT")
        self.assertEqual(result["coalition"]["execution_mode"], "DETERMINISTIC_SPECIALIST_TOOL")
        self.assertEqual(result["coalition"]["plan"]["independent_model_count"], 0)

        tasks = rows("SELECT * FROM tasks WHERE mission_id=?", (created["mission_id"],))
        self.assertTrue(any(t["role"] == "CEREBRON_COALITION" and t["status"] == "COMPLETED" for t in tasks))
        self.assertTrue(any(t["role"] == "SM02" and t["status"] == "COMPLETED" for t in tasks))
        self.assertTrue(any(t["role"] == "SM15" and t["status"] == "COMPLETED" for t in tasks))
        self.assertTrue(any(t["role"] == "SM18" and t["status"] == "COMPLETED" for t in tasks))

        evidence = rows("SELECT * FROM evidence WHERE mission_id=?", (created["mission_id"],))
        deterministic = [e for e in evidence if e["kind"] == "DETERMINISTIC_TOOL_EXECUTION"]
        self.assertEqual(len(deterministic), 1)
        self.assertEqual(deterministic[0]["maturity"], "E2_COMPUTATION")


if __name__ == "__main__":
    unittest.main()
