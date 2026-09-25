import json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class TestF173(unittest.TestCase):
    def test_project(self):
        p=json.loads((R/"config/project.json").read_text())
        self.assertEqual(p["farm_id"],173)
        self.assertEqual(p["status"],"LOCAL_LIVE_LOOP_CANARY_PASS_EXTERNAL_RUNTIME_UNQUALIFIED")
        self.assertTrue(p["target_repo_initialized"])
        self.assertEqual(p["dedicated_repo_selftest_run_id"],36162643249)
        self.assertEqual(p["master_plugin_bus_status"],"DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED")
        self.assertEqual(p["training_status"],"NOT_TRAINED")
        self.assertEqual(p["local_live_loop_canary"]["run_id"],36162553038)
        self.assertFalse(p["local_live_loop_canary"]["external_calls_executed"])
        self.assertFalse(p["local_live_loop_canary"]["production_live_claimed"])
        self.assertEqual(p["external_runtime_status"],"UNQUALIFIED")
if __name__=="__main__":
    unittest.main()
