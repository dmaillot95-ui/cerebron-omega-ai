import json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class TestF173(unittest.TestCase):
    def test_project(self):
        p=json.loads((R/"config/project.json").read_text())
        self.assertEqual(p["farm_id"],173)
        self.assertEqual(p["status"],"LOCAL_FALLBACK_SCAFFOLD_DEDICATED_REPOSITORY_INITIALIZED")
        self.assertTrue(p["target_repo_initialized"])
        self.assertEqual(p["dedicated_repo_selftest_run_id"],36155830169)
        self.assertEqual(p["master_plugin_bus_status"],"DECLARED_GUARD_PASS_RUNTIME_UNQUALIFIED")
        self.assertEqual(p["training_status"],"NOT_TRAINED")
if __name__=="__main__":
    unittest.main()
