import os
import pathlib
import sys
import unittest
from unittest import mock

PLATFORM=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PLATFORM))

import sigma_manager


class SigmaManagerTests(unittest.TestCase):
    def test_full_council_has_eight_named_delegates(self):
        roles=sigma_manager.select_delegates("hard mission",full_council=True)
        self.assertEqual(len(roles),8)
        self.assertEqual(roles,["SAPHEA","SPIRALION","ETHERION","HYPERION","ASTRION","METRION","AFAH","AELYS"])

    def test_minimal_coalition_keeps_audit_and_human_interface(self):
        roles=sigma_manager.select_delegates("Calculate orbital transfer and validate evidence")
        self.assertIn("ASTRION",roles)
        self.assertIn("METRION",roles)
        self.assertIn("AFAH",roles)
        self.assertIn("AELYS",roles)
        self.assertLessEqual(len(roles),8)

    def test_status_does_not_claim_eight_independent_models(self):
        st=sigma_manager.status()
        self.assertEqual(st["council_seats"],8)
        self.assertEqual(st["independent_general_neural_models"],1)


if __name__=="__main__":
    unittest.main()
