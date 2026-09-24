import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"training"))
from source_gate import admit
class T(unittest.TestCase):
 def test_arch(self):
  a=json.loads((ROOT/"architecture"/"NU_ARCHITECTURE_V1.json").read_text());self.assertFalse(a["runtime_changed"]);self.assertEqual(a["campaign"]["passes"],10);self.assertEqual(a["role_id"],"NULL_MODEL_CHALLENGER");self.assertEqual(a["farm_id"],162)
 def test_m6(self):self.assertFalse(admit({"memory_class":"M6_COLD_BENCHMARK","validated":True,"object_path":"x/M6/x"})[0])
 def test_gold(self):self.assertTrue(admit({"memory_class":"M4_GOLD","validated":True,"object_path":"x/M4/x"})[0])
if __name__=="__main__":unittest.main()
