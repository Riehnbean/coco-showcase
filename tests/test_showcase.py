import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 s=importlib.util.spec_from_file_location('m',ROOT/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 def setUp(self):self.m=module('promote-models.py');self.r=json.loads((ROOT/'model-registry.json').read_text())
 def test_qualified_promotion(self):self.assertEqual([x['candidate_id'] for x in self.m.find_promotion_candidates(self.r)],['example/code-candidate'])
 def test_denied_candidate(self):
  self.r['models'][1]['current_status']='deny-listed';self.assertEqual(list(self.m.find_promotion_candidates(self.r)),[])
 def test_no_quality_regression(self):
  self.r['models'][1]['quality_score_by_capability']['code']=69;self.assertEqual(list(self.m.find_promotion_candidates(self.r)),[])
 def test_capability_filter(self):self.assertEqual(list(self.m.find_promotion_candidates(self.r,'reason')),[])
 def test_workflows_inactive_no_credentials(self):
  for p in (ROOT/'workflows').glob('*.json'):
   w=json.loads(p.read_text());self.assertFalse(w['active']);self.assertNotIn('credentials',p.read_text());self.assertTrue(all('webhook' not in n['type'].lower() for n in w['nodes']))
if __name__=='__main__':unittest.main()
