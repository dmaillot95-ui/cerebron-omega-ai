import json
import os
import pathlib
import sys
import unittest
from unittest import mock

PLATFORM=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PLATFORM))

import elyra_policy_runtime as epr


class ElyraPolicyRuntimeTests(unittest.TestCase):
    def test_status_pins_verified_evidence(self):
        with mock.patch.dict(os.environ,{"CEREBRON_ENABLE_ELYRA_POLICY":""},clear=False):
            st=epr.status()
        self.assertEqual(st["weights_sha256"],"b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601")
        self.assertEqual(st["training_run"],35904950828)
        self.assertEqual(st["independent_audit_run"],35905952407)

    def test_feature_contract_fails_closed(self):
        with self.assertRaises(epr.ElyraPolicyError):
            epr.infer([1,2,3])


if __name__=="__main__":
    unittest.main()
