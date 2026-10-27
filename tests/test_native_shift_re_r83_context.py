"""R83 contract tests: disallow treating offset collisions as typed writer proof."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('r83',ROOT/'audit_r83_context.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r83_context_manifest.json').read_text())
def val(s):return M['pins'][s]['hex']
class R83(unittest.TestCase):
 def test_49(self):self.assertEqual(len(M['pins']),49)
 def test_5_E8(self):self.assertEqual(len(M['e8_edges']),5)
 def test_ten_scopes(self):self.assertEqual(len(M['ranges']),10)
 def test_one_leaf(self):self.assertEqual(M['leaf_names'],['group_leaf'])
 def test_root_ctx_read(self):self.assertEqual(val('03012fe7'),'488b4638')
 def test_member_ctor_ctx(self):self.assertEqual(val('03052f6d'),'48898320070000')
 def test_ctor_input(self):self.assertEqual(val('03052f62'),'488b4358')
 def test_group_context_copy(self):self.assertEqual(val('030c7dca'),'48894110')
 def test_group_rebind_not_context(self):self.assertEqual(val('03020a75'),'48899ef8320000')
 def test_auxiliary_object(self):
  self.assertEqual(val('0300b19f'),'488bda')
  self.assertEqual(val('0300b1a9'),'488bf9')
 def test_false_root_writer(self):self.assertEqual(val('0300b23a'),'4c894938')
 def test_false_member_byte_writer(self):self.assertEqual(val('0300bad6'),'888720070000')
 def test_same_context_not_epoch(self):
  r=a.temporal('C','C','C')
  self.assertTrue(r['same_context']);self.assertFalse(r['actual_queued_shift_identity_proven'])
 def test_known_epoch_mismatch(self):self.assertFalse(a.temporal('C','C','C',1,2)['epoch_matches_if_known'])
 def test_pointer_rebind_synthetic(self):self.assertFalse(a.temporal('old','new','new')['same_context'])
 def test_missing_rejected(self):
  with self.assertRaisesRegex(a.Reject,'MISSING_CONTEXT'):a.temporal('',None,None)
 def test_no_global_immutability_claim(self):self.assertIn('does NOT prove global',M['scope'])
 def test_no_patch(self):self.assertFalse(M['gameplay_patch_authorized'])
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.Reject,'SHA_SIZE_DRIFT'):a.verify(b'MZ'+bytes(100),M)
 def test_original_exe_if_available(self):
  p=os.getenv('BSC_EXE')
  if not p:self.skipTest('Licensed WH3 original EXE excluded from public CI')
  self.assertEqual(a.verify(Path(p).read_bytes(),M)['pins'],49)
