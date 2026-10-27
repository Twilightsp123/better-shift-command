"""R85 static/synthetic regressions; original licensed WH3 EXE optional."""
import json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(P))
import audit_r85_type_alias as a
M=json.loads((P/'r85_type_alias_pins.json').read_text())
def at(r):return M['pins'][r]['hex']
class R85(unittest.TestCase):
 def test_pins(self):self.assertEqual(len(M['pins']),49)
 def test_bounds(self):self.assertEqual(len(M['bounds']),10)
 def test_calls(self):self.assertEqual(len(M['calls']),4)
 def test_foreign_vtable(self):self.assertEqual(at('02f9c9fa'),'48894120')
 def test_foreign_ctor_zero(self):self.assertEqual(at('02f9d16c'),'49898638070000')
 def test_another_RDX_object(self):self.assertEqual(at('02fa6088'),'4c8bf2')
 def test_foreign_vector_address(self):self.assertEqual(at('02fa66f8'),'498d8e38070000')
 def test_append_E8(self):self.assertEqual(M['calls']['02fa6734'],'02f93abc')
 def test_vector_capacity(self):self.assertEqual(at('02f93acb'),'8b01')
 def test_vector_count(self):self.assertEqual(at('02f93ad7'),'394104')
 def test_vector_pointer(self):self.assertEqual(at('02f93b02'),'48894308')
 def test_vector_stride(self):self.assertEqual(at('02f93b96'),'488944cf08')
 def test_true_member_ctor(self):self.assertEqual(at('03052f82'),'4c89a338070000')
 def test_true_member_reader(self):self.assertEqual(at('03075202'),'488b8b38070000')
 def test_candidate_read(self):self.assertEqual(at('0311f405'),'488b4720')
 def test_other_dword(self):self.assertEqual(at('0300bb6a'),'898738070000')
 def test_stack_pointer(self):self.assertEqual(at('0329b276'),'48898538070000')
 def test_pointer_same_isnt_leg(self):self.assertFalse(a.typecheck('ordinary_member')['same_shift_generation_proven'])
 def test_foreign_isnt_member(self):self.assertFalse(a.typecheck('other_vector')['actual_member'])
 def test_unknown_type_reject(self):
    with self.assertRaisesRegex(a.Drift,'TYPE_UNKNOWN'):a.typecheck('other')
 def test_failclosed_exe(self):
    with self.assertRaisesRegex(a.Drift,'EXACT_SHA_SIZE'):a.verify(b'MZ'+bytes(100),M)
 def test_private_exe(self):
    fn=os.environ.get('BSC_EXE')
    if not fn:self.skipTest('Original commercial EXE not included in public Actions')
    self.assertFalse(a.verify(Path(fn).read_bytes(),M)['member_runtime_writer_proven'])
