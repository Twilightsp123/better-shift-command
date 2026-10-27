"""R82 root/member context trace: synthetic gates + private EXE optional."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('a82',ROOT/'audit_r82_context.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r82_context_manifest.json').read_text())
class R82(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(M['pins']),43)
 def test_E8(self):self.assertEqual(len(M['e8_edges']),8)
 def test_pe_functions(self):self.assertEqual(len(M['function_ranges']),9)
 def test_leaf(self):self.assertEqual(M['no_unwind_leaf'],['group_context_copy'])
 def test_root_rsi(self):self.assertEqual(M['pins']['03012f6c']['hex'],'488bf1')
 def test_root_member_descriptor(self):self.assertEqual(M['pins']['03013235']['hex'],'488d5630')
 def test_member_ctor_rdx(self):self.assertEqual(M['pins']['03052bd5']['hex'],'4c8bfa')
 def test_member_core_from_descriptor(self):self.assertEqual(M['pins']['03141803']['hex'],'488b4208')
 def test_member_context_store(self):self.assertEqual(M['pins']['03141814']['hex'],'48894158')
 def test_controller_inherits(self):self.assertEqual(M['pins']['03052f6d']['hex'],'48898320070000')
 def test_group_same_root(self):self.assertEqual(M['pins']['03020a17']['hex'],'4c8bc6')
 def test_group_ctor_root(self):self.assertEqual(M['pins']['030c7cd2']['hex'],'488b5208')
 def test_group_context_copy(self):self.assertEqual(M['pins']['030c7dca']['hex'],'48894110')
 def test_group_backref(self):self.assertEqual(M['pins']['030c7cf9']['hex'],'488983100a0000')
 def test_group_published_late(self):self.assertEqual(M['pins']['03020a75']['hex'],'48899ef8320000')
 def test_positive_construction(self):self.assertTrue(a.scenario('ctx')['construction_source_same'])
 def test_pointer_altered(self):self.assertFalse(a.scenario('ctx',member_now='new')['current_pointer_same'])
 def test_shared_ctx_not_same_generation(self):self.assertFalse(a.scenario('ctx')['queued_move_generation_proven'])
 def test_distinct_root_same_context_unknown(self):self.assertFalse(a.scenario('shared')['queued_move_generation_proven'])
 def test_empty_ctx_reject(self):
  with self.assertRaisesRegex(a.Drift,'EMPTY_CONTEXT'):a.scenario('')
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.Drift,'SHA_SIZE'):a.verify(b'MZ'+bytes(20),M)
 def test_optional_exact_exe(self):
  p=os.getenv('BSC_EXE')
  if not p:self.skipTest('Original licensed game EXE absent in public CI')
  self.assertTrue(a.verify(Path(p).read_bytes(),M)['constructor_source_proven'])
