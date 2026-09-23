import hashlib
import json
import pathlib
import sys
import tempfile
import time
import unittest
from unittest import mock

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

import security
from security import Principal, SecurityError


class SecurityHardeningTests(unittest.TestCase):
    def test_audit_hash_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            path=pathlib.Path(td)/"audit.jsonl"
            with mock.patch.object(security,"AUDIT_LOG",path):
                security.audit(Principal("alice",("operator",)),"mission:create","ALLOW",{"id":"m1"})
                security.audit(Principal("alice",("operator",)),"mission:read","ALLOW",{"id":"m1"})
                ok=security.verify_audit_chain()
                self.assertTrue(ok["valid"])
                self.assertEqual(ok["events"],2)

                lines=path.read_text().splitlines()
                first=json.loads(lines[0])
                first["outcome"]="DENY"
                lines[0]=json.dumps(first,sort_keys=True)
                path.write_text("\n".join(lines)+"\n")
                bad=security.verify_audit_chain()
                self.assertFalse(bad["valid"])

    def test_legacy_audit_log_can_enter_hash_chain_without_loss(self):
        with tempfile.TemporaryDirectory() as td:
            path=pathlib.Path(td)/"audit.jsonl"
            legacy={"time":1.0,"action":"legacy","outcome":"ALLOW"}
            path.write_text(json.dumps(legacy,sort_keys=True)+"\n")
            with mock.patch.object(security,"AUDIT_LOG",path):
                security.audit(Principal("alice",("operator",)),"new","ALLOW",{})
                result=security.verify_audit_chain()
            self.assertTrue(result["valid"])
            self.assertEqual(result["legacy_events"],1)
            self.assertEqual(result["events"],2)

    def test_sqlite_rate_limit_persists_between_calls(self):
        with tempfile.TemporaryDirectory() as td:
            db=pathlib.Path(td)/"rate.db"
            with mock.patch.object(security,"RATE_DB",db):
                p=Principal("alice",("operator",))
                security.reset_rate_limits()
                security.rate_limit(p,"write",1,60)
                self.assertTrue(db.exists())
                with self.assertRaises(SecurityError) as ctx:
                    security.rate_limit(p,"write",1,60)
                self.assertEqual(ctx.exception.code,"RATE_LIMITED")

    def test_token_validity_windows_support_rotation(self):
        active="active-secret"
        expired="expired-secret"
        now=time.time()
        cfg=json.dumps([
            {
                "user_id":"alice","token_id":"alice-v2",
                "token_sha256":hashlib.sha256(active.encode()).hexdigest(),
                "roles":["operator"],"not_before":now-10,"expires_at":now+3600,
            },
            {
                "user_id":"alice","token_id":"alice-v1",
                "token_sha256":hashlib.sha256(expired.encode()).hexdigest(),
                "roles":["operator"],"expires_at":now-1,
            },
        ])
        with mock.patch.dict("os.environ",{"CEREBRON_RBAC_TOKENS_JSON":cfg},clear=False):
            self.assertEqual(security.authenticate("Bearer "+active).user_id,"alice")
            with self.assertRaises(SecurityError):
                security.authenticate("Bearer "+expired)


if __name__=="__main__":
    unittest.main()
