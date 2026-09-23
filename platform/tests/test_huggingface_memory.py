import os
import pathlib
import sys
import unittest
from unittest import mock

PLATFORM=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PLATFORM))

import huggingface_memory as hf


class HuggingFaceMemoryTests(unittest.TestCase):
    def test_missing_token_fails_closed(self):
        with mock.patch.dict(os.environ,{"HF_TOKEN":"","HUGGING_FACE_HUB_TOKEN":"","CEREBRON_HF_SIGMA_REPO":""},clear=False):
            st=hf.status()
            self.assertEqual(st["status"],"CREDENTIAL_REQUIRED")
            self.assertFalse(st["token_present"])

    def test_m6_write_is_forbidden_before_any_network_call(self):
        with self.assertRaises(hf.HuggingFaceMemoryError) as ctx:
            hf.push_json("m6.json",{}, "M6", {"sha256":"x"})
        self.assertEqual(str(ctx.exception),"M6_TRAINING_MEMORY_WRITE_FORBIDDEN")


if __name__=="__main__":
    unittest.main()
