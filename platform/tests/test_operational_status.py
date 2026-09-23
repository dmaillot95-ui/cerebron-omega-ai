import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]

class OperationalStatusTests(unittest.TestCase):
    def test_manifest_is_bounded_and_remote_blocked(self):
        d=json.loads((ROOT/"config"/"operational-status-v1.json").read_text())
        self.assertEqual(d["status"],"OPERATIONAL_SCOPED_LOCAL_VERIFIED")
        self.assertEqual(d["farm_cap"],144)
        self.assertFalse(d["control_plane_is_farm"])
        self.assertEqual(d["public_remote_deployment"],"BLOCKED")
        self.assertEqual(d["gates"]["G11"]["status"],"OPEN")
        self.assertTrue(d["gates"]["G6"]["status"].startswith("PASS_SCOPED"))
        self.assertTrue(d["gates"]["G7"]["status"].startswith("PASS_SCOPED"))
        self.assertTrue(d["gates"]["G8"]["status"].startswith("PASS_SCOPED"))

    def test_pinned_evidence_shapes(self):
        d=json.loads((ROOT/"config"/"operational-status-v1.json").read_text())
        self.assertEqual(d["evidence"]["semantic_v5"]["adaptive_score"],53)
        self.assertEqual(d["evidence"]["semantic_v5"]["domains_improved"],6)
        self.assertEqual(len(d["evidence"]["elyra_neural"]["weights_sha256"]),64)

if __name__=="__main__":
    unittest.main()
