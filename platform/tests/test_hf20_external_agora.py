import hashlib
import pathlib
import sys
import unittest

PLATFORM=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PLATFORM))

import hf_agent_pool
import agora_external

class IntegrationTests(unittest.TestCase):
    def test_hf_pool_has_twenty_slots(self):
        s=hf_agent_pool.status()
        self.assertEqual(s["max_slots"],20)
        r=hf_agent_pool.select([74,139],20)
        self.assertEqual(r["count"],20)
        self.assertEqual(r["status"],"ROUTED_SLOTS_NOT_EXECUTED")

    def test_external_agora_sha_gate(self):
        content="assistant external contribution"
        payload={
            "participant_id":"chatgpt-external-1",
            "provider":"OpenAI",
            "model":"unknown-until-receipt",
            "session_id":"session-x",
            "message_id":"msg-x",
            "content":content,
            "content_sha256":hashlib.sha256(content.encode()).hexdigest(),
            "timestamp":"2026-09-23T00:00:00Z",
            "provenance":{"source":"external-session"},
        }
        r=agora_external.admit(payload)
        self.assertEqual(r["status"],"UNDER_TEST_EXTERNAL")
        self.assertFalse(r["independent_evidence"])

if __name__=="__main__":
    unittest.main()
