import math
import unittest
from tools.pi_response_sweep import circle_sweep, fibonacci_sphere, refine_circle, coverage_manifest

class PiSweepTests(unittest.TestCase):
    def test_full_circle(self):
        pts=circle_sweep(16)
        self.assertEqual(len(pts),16)
        self.assertAlmostEqual(pts[8]["theta_rad"],math.pi,places=12)
        self.assertAlmostEqual(pts[0]["unit_vector"][0],1.0,places=12)

    def test_unit_sphere(self):
        for p in fibonacci_sphere(64):
            x,y,z=p["unit_vector"]
            self.assertAlmostEqual(x*x+y*y+z*z,1.0,places=12)

    def test_refinement(self):
        pts=refine_circle(math.pi,math.pi/8,9)
        self.assertEqual(len(pts),9)

    def test_runtime_frozen(self):
        m=coverage_manifest(16,32)
        self.assertFalse(m["runtime_changed"])
        self.assertEqual(m["math"]["full_rotation_deg"],360.0)

if __name__=="__main__":
    unittest.main()
