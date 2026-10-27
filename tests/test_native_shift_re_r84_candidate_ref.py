"""R84 public offline regression; commercial EXE only with BSC_EXE."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
spec=importlib.util.spec_from_file_location('r84',ROOT/'audit_r84_candidate_ref.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
M=json.loads((ROOT/'r84_candidate_ref_pins.json').read_text())
def p(addr):return M['pins'][addr]['hex']
class R84(unittest.TestCase):
 def test_count(self):self.assertEqual(len(M['pins']),55)
 def test_calls(self):self.assertEqual(len(M['e8_edges']),4)
 def test_functions(self):self.assertEqual(len(M['function_owners']),7)
 def test_member_virtual(self):self.assertEqual(M['member_method_4a0'],'030751e4')
 def test_null_ctor(self):self.assertEqual(p('03052f82'),'4c89a338070000')
 def test_local_worker_read(self):self.assertEqual(p('030770cd'),'488b8338070000')
 def test_local_worker_read2(self):self.assertEqual(p('03077147'),'488b8338070000')
 def test_virtual_member_identity(self):self.assertEqual(p('030751ea'),'488bd9')
 def test_virtual_typed_pointer_read(self):self.assertEqual(p('03075202'),'488b8b38070000')
 def test_virtual_conditional(self):self.assertEqual(p('0307520c'),'7405')
 def test_processor_call(self):self.assertEqual(M['e8_edges']['0307520e'],'03126964')
 def test_processor_context(self):self.assertEqual(p('03126968'),'488b4108')
 def test_processor_flag(self):self.assertEqual(p('031269bf'),'41c680d100000001')
 def test_seven_builder_reads(self):self.assertEqual(len(M['builder_direct_read_sites']),7)
 def test_no_direct_builder_write(self):self.assertEqual(M['builder_direct_writes_in_bounded_function'],[])
 def test_builder_param(self):self.assertEqual(p('0311f410'),'448b88a0000000')
 def test_aux_dword_false_writer(self):self.assertEqual(p('0300bb6a'),'898738070000')
 def test_other_dword_false_writer(self):self.assertEqual(p('0303a16a'),'898638070000')
 def test_shared_ptr_not_epoch(self):self.assertFalse(a.simulate('p','p',1,1)['actual_shift_leg_proven'])
 def test_change_not_cause(self):self.assertFalse(a.simulate('a','b')['gameplay_patch_authorized'])
 def test_wrong_sha(self):
  with self.assertRaisesRegex(a.Drift,'SHA_SIZE'):a.verify(b'MZ'+bytes(128),M)
 def test_matching_exe_optional(self):
  fname=os.getenv('BSC_EXE')
  if not fname:self.skipTest('Licensed WH3 EXE excluded from public CI')
  self.assertFalse(a.verify(Path(fname).read_bytes(),M)['gameplay_patch_authorized'])
