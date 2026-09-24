import unittest
from tools.pi_needle import manifest, sample_needles, select_diverse

class PiNeedleTests(unittest.TestCase):
    def test_reproducible(self):
        a=manifest("ABC",256)
        b=manifest("ABC",256)
        self.assertEqual(a["seed"],b["seed"])
        self.assertEqual(a["result_sha256"],b["result_sha256"])

    def test_runtime_frozen(self):
        self.assertFalse(manifest("ABC",32)["runtime_changed"])

    def test_unit_vectors(self):
        rows,_=sample_needles("ABC",64)
        for p in rows:
            x,y=p["unit_vector"]
            self.assertAlmostEqual(x*x+y*y,1.0,places=12)

    def test_diversity_selector(self):
        rows,_=sample_needles("ABC",128)
        scores=[i for i in range(len(rows))]
        out=select_diverse(rows,scores,k=8,min_sep_deg=10)
        self.assertLessEqual(len(out),8)
        self.assertGreater(len(out),0)

if __name__=="__main__":
    unittest.main()
