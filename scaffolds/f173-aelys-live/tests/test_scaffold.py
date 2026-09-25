import json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class TestF173(unittest.TestCase):
    def test_project(self):
        p=json.loads((R/"config/project.json").read_text())
        self.assertEqual(p["farm_id"],173)
        self.assertEqual(p["status"],"PREPARED_NOT_DEPLOYED_REPOSITORY_EMPTY")
        self.assertFalse(p["target_repo_initialized"])
        self.assertEqual(p["training_status"],"NOT_TRAINED")
if __name__=="__main__":
    unittest.main()
