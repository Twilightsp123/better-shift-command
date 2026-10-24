"""BSC R69: synthetic/contract CI; private EXE test requires BSC_EXE."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_r69_projection_gate as r
M=json.loads((ROOT/'r69_projection_pins.json').read_text())
class R69(unittest.TestCase):
 def test_count(self):self.assertEqual(len(M['pins']),76)
 def test_e8_count(self):self.assertEqual(len(M['e8_edges']),12)
 def test_unwind_ranges(self):self.assertEqual(len(M['unwind_functions']),4)
 def test_setter_handler(self):self.assertEqual(M['e8_edges']['0307d9f8'],'0307db60')
 def test_distinct_functions(self):self.assertNotEqual(M['unwind_functions']['setter_immediate_handler'][1],M['unwind_functions']['separate_projection_gate'][0])
 def test_projection_reset(self):self.assertEqual(M['pins']['0307d9d9']['hex'],'21913c020000')
 def test_second_field_reset(self):self.assertEqual(M['pins']['0307d9df']['hex'],'2191c8010000')
 def test_threshold_comparison(self):self.assertEqual(M['pins']['0307e1d6']['hex'],'0f2f873c020000')
 def test_gate_jump(self):self.assertEqual(M['pins']['0307e1dd']['hex'],'0f87ae050000')
 def test_previous_projection_copy(self):self.assertEqual(M['pins']['031000a5']['hex'],'898138020000')
 def test_integrator_before_goal(self):self.assertLess(0x0310014c,0x03100247)
 def test_refresh_one(self):self.assertEqual(M['pins']['031002a8']['hex'],'f30f118b3c020000')
 def test_refresh_two(self):self.assertEqual(M['pins']['031002cf']['hex'],'f30f11833c020000')
 def test_old1_to0_synthetic(self):self.assertTrue(r.synthetic_gate(1,0,0.5)['below_threshold'])
 def test_old2_to0_synthetic(self):self.assertTrue(r.synthetic_gate(2,0,0.5)['below_threshold'])
 def test_old3_to0_synthetic(self):self.assertFalse(r.synthetic_gate(3,0,0.5)['below_threshold'])
 def test_no_change_synthetic(self):self.assertEqual(r.synthetic_gate(1,1,0.5)['value'],0.5)
 def test_no_patch_permission(self):self.assertFalse(M['runtime_patch_authorized'])
 def test_exe_optional(self):
    if 'BSC_EXE' not in os.environ:self.skipTest('Commercial WH3 EXE excluded from public CI')
    result=r.verify(Path(os.environ['BSC_EXE']).read_bytes(),M)
    self.assertFalse(result['root_cause_proven'])
 def test_bad_sha_fails_closed(self):
    with self.assertRaisesRegex(r.EvidenceError,'FAIL_CLOSED_SHA_SIZE'):r.verify(b'MZ'+bytes(200),M)
if __name__=='__main__':unittest.main()
