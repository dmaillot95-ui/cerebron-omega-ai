import unittest
from tools.pi_search import build_search_packet, refine_sector

class PiSearchTests(unittest.TestCase):
    def test_same_task_same_packet(self):
        a=build_search_packet("X",16,64,16)
        b=build_search_packet("X",16,64,16)
        self.assertEqual(a["seed"],b["seed"])
        self.assertEqual(a["result_sha256"],b["result_sha256"])

    def test_counts(self):
        p=build_search_packet("Y",16,64,16)
        self.assertEqual(p["modes"]["sweep"]["count"],16)
        self.assertEqual(p["modes"]["needle"]["count"],64)
        self.assertEqual(p["modes"]["sphere"]["count"],16)

    def test_refine(self):
        self.assertEqual(len(refine_sector(90.0,10.0,9)),9)

    def test_runtime_frozen(self):
        self.assertFalse(build_search_packet("Z",8,32,8)["runtime_changed"])

if __name__=="__main__":
    unittest.main()
