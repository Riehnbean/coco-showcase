import importlib.util,json,unittest,copy,contextlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 spec=importlib.util.spec_from_file_location('tested',ROOT/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Lifecycle(unittest.TestCase):
 def test_discovery_scope_and_denied_tombstone(self):
  m=load('discover-models.py');r={'models':[{'model_id':'old','provider':'openrouter','current_status':'active'},{'model_id':'denied','provider':'openrouter','current_status':'deny-listed'},{'model_id':'other','provider':'other','current_status':'active'}]}
  d=m.diff_and_report(r,[{'model_id':'new','provider':'openrouter','current_status':'not-yet-evaluated'},{'model_id':'denied','provider':'openrouter'}]);self.assertEqual(d['new'],['new']);self.assertEqual(d['removed'],['old']);m.apply_diff(r,d);self.assertEqual(r['models'][0]['current_status'],'deprecated');self.assertEqual(r['models'][1]['current_status'],'deny-listed');self.assertEqual(r['models'][2]['current_status'],'active')
 def test_evaluation_dry_run_preserves_registry(self):
  m=load('evaluate-models.py');r={'models':[{'model_id':next(iter(m.SEED_SCORES))}]};before=copy.deepcopy(r)
  with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(m.apply_seed(r,dry_run=True),1)
  self.assertEqual(r,before)
 def test_evaluation_marks_provenance(self):
  m=load('evaluate-models.py');r={'models':[{'model_id':next(iter(m.SEED_SCORES))}]}
  with contextlib.redirect_stdout(io.StringIO()):m.apply_seed(r)
  self.assertIn('Layer 3 seed score',r['models'][0]['notes']);self.assertTrue(r['models'][0]['last_tested'])
