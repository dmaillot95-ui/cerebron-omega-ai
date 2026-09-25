import json, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class TestF173(unittest.TestCase):
    def test_project(self):
        p=json.loads((R/"config/project.json").read_text())
        self.assertEqual(p["farm_id"],173)
        self.assertEqual(p["status"],"LOCAL_LOOP_TTS_REPLAY_HTTP_CANARIES_PASS_EXTERNAL_RUNTIME_UNQUALIFIED")
        self.assertTrue(p["target_repo_initialized"])
        self.assertEqual(p["dedicated_repo_selftest_run_id"],36164296182)
        self.assertEqual(p["training_status"],"NOT_TRAINED")
        self.assertEqual(p["live_production_status"],"NOT_DEPLOYED")
        self.assertEqual(p["external_runtime_status"],"UNQUALIFIED")
        self.assertEqual(p["local_live_loop_canary"]["run_id"],36162553038)
        self.assertFalse(p["local_live_loop_canary"]["external_calls_executed"])
        self.assertEqual(p["local_tts_canary"]["run_id"],36163338754)
        self.assertEqual(p["local_tts_canary"]["wav_bytes"],166854)
        self.assertFalse(p["local_tts_canary"]["external_service_used"])
        self.assertEqual(p["local_session_replay_canary"]["run_id"],36163483531)
        self.assertEqual(p["local_session_replay_canary"]["events"],3)
        self.assertFalse(p["local_session_replay_canary"]["external_calls_executed"])
        self.assertEqual(p["local_http_loopback_canary"]["run_id"],36164204308)
        self.assertEqual(p["local_http_loopback_canary"]["http_status"],200)
        self.assertFalse(p["local_http_loopback_canary"]["external_endpoint_used"])
        self.assertFalse(p["local_http_loopback_canary"]["production_live_claimed"])
if __name__=="__main__":
    unittest.main()
