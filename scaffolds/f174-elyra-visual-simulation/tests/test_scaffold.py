import json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class TestF174(unittest.TestCase):
    def test_project(self):
        p=json.loads((R/"config/project.json").read_text())
        self.assertEqual(p["farm_id"],174)
        self.assertEqual(p["status"],"VISUAL_STATE_SEQUENCE_CANARY_EXECUTED")
        self.assertTrue(p["target_repo_initialized"])
        self.assertTrue(p["visual_simulation_executed"])
        self.assertEqual(p["dedicated_repo_selftest_run_id"],36160671044)
if __name__=="__main__":
    unittest.main()

# Canary boundary checks are validated by validate_architecture.py and dedicated repo workflows.
