import pathlib
import sys
import unittest
from unittest import mock

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from role_runtime import ELYRA_EVIDENCE, runtime_roles


class RoleRuntimeTests(unittest.TestCase):
    def test_runtime_roles_are_not_falsely_all_unavailable(self):
        with mock.patch.dict("os.environ", {"CEREBRON_ENABLE_LOCAL_GENERATIVE": ""}, clear=False):
            payload = runtime_roles()
        by_name = {r["name"]: r for r in payload["roles"]}
        self.assertEqual(by_name["CÉRÉBRON"]["status"], "ACTIVE")
        self.assertEqual(by_name["SAPHEA"]["status"], "ACTIVE_BOUNDED")
        self.assertEqual(by_name["AÉLYS"]["status"], "CONFIGURED_NO_DEDICATED_MODEL")
        self.assertEqual(by_name["ELYRA"]["status"], "TRAINED_ARTIFACT_VERIFIED_NOT_LOADED_IN_CONTROL_PLANE")
        self.assertEqual(by_name["SAPHEA MICRO"]["implemented_count"], 7)
        self.assertEqual(by_name["SAPHEA MICRO"]["planned_count"], 13)

    def test_elyra_evidence_is_pinned(self):
        self.assertEqual(
            ELYRA_EVIDENCE["weights_sha256"],
            "b4799a695795fece1db392150876b9fd037bb90d2cfdbdfe6dc70765f33a8601",
        )
        self.assertEqual(ELYRA_EVIDENCE["training_run"], 35904950828)
        self.assertEqual(ELYRA_EVIDENCE["audit_run"], 35905952407)


if __name__ == "__main__":
    unittest.main()
