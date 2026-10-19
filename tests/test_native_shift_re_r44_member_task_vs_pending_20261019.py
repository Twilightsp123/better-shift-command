#!/usr/bin/env python3
"""R44 read-only regression; private EXE cases skip on GitHub CI."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
TOOLS=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(TOOLS))
import audit_r44_member_task_vs_pending_20261019 as a

class R44TaskVsPending(unittest.TestCase):
 def setUp(self):self.records=a.manifest();self.pins={p:b for g in self.records.values() for p,b in g['pins'].items()}
 def test_01_group_count(self):self.assertEqual(len(self.records),11)
 def test_02_opcode_count(self):self.assertEqual(len(self.pins),111)
 def test_03_all_pin_lengths_in_instruction_range(self):
  self.assertTrue(all(0<len(raw)<=15 for raw in self.pins.values()))
 def test_04_function_owner_bounds_positive(self):
  self.assertTrue(all(g['lo']<g['hi'] for g in self.records.values()))
 def test_05_direct_e8_sites_are_complete(self):
  self.assertEqual(len(a.CALLS),13)
  for at,tgt in a.CALLS.items():
   raw=self.pins[at]
   self.assertEqual(raw[0],0xe8)
   self.assertEqual(at+5+int.from_bytes(raw[1:5],'little',signed=True),tgt)
 def test_06_branch_target_contract(self):
  self.assertEqual(len(a.BRANCHES),9)
  for at,tgt in a.BRANCHES.items():self.assertEqual(a.branch_dest(at,self.pins[at]),tgt)
 def test_07_two_typed_vtables(self):
  self.assertEqual(len(a.TABLE),7)
  self.assertEqual(a.TABLE[(a.TASK_TABLE,0x8)],0x0325E4B4)
  self.assertEqual(a.TABLE[(a.MEMBER_TABLE,0x550)],0x0306F594)
 def test_08_owner_initialized_from_member(self):
  self.assertEqual(self.pins[0x03052EEE].hex(),'48891e')
  self.assertEqual(self.pins[0x03053640].hex(),'48894108')
 def test_09_buffered_vector_three_components(self):
  for addr in (0x0324DBC8,0x0324DBD0,0x0324DBD8):
   self.assertIn(addr,self.pins)
 def test_10_live_goal_snapshot_is_separate_source(self):
  self.assertEqual(self.pins[0x0325E50F].hex(),'4c8d4738')
  self.assertEqual(self.pins[0x0325E530].hex(),'488d91e0010000')
 def test_11_task_first_virtual_then_second(self):
  self.assertLess(0x03085FC1,0x03085FD4)
  self.assertEqual(self.pins[0x03085FC1].hex(),'ff5008')
  self.assertEqual(self.pins[0x03085FD4].hex(),'ff5010')
 def test_12_exact_handler_caller_inventory_expected(self):
  self.assertEqual(a.DIRECT_EXPECTED[0x03065DB8],(0x030728C1,0x03087013,0x0308DA71,0x0325E544))
 def test_13_member_tick_state16_dispatch(self):
  self.assertEqual(a.BRANCHES[0x030872DA],0x0308731B)
  self.assertEqual(a.CALLS[0x03087322],0x03085F9C)
 def test_14_steering_then_conditional_helper(self):
  self.assertLess(0x03087349,0x03087351)
  self.assertEqual(a.CALLS[0x0308DA71],0x03065DB8)
 def test_15_three_non_pending_handler_callers(self):
  others=set(a.DIRECT_EXPECTED[0x03065DB8])-{0x03087013}
  self.assertEqual(others,{0x030728C1,0x0308DA71,0x0325E544})
  self.assertEqual(a.SHA,'9bd58c63bd7fc5c9909b3d3d9b6b7a6ae4eac784369bf91a9e53c3e9f42be496')
 def test_16_reject_wrong_exe_even_optimized(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/'bad.exe';fake.write_bytes(b'MZ'+bytes(512))
   for flags in ([],['-O']):
    proc=subprocess.run([sys.executable,*flags,str(a.__file__),'--exe',str(fake)],capture_output=True,text=True)
    self.assertNotEqual(proc.returncode,0)
    self.assertIn('EXE_SIZE_DRIFT',proc.stderr)
 def test_17_refuse_to_overwrite_input(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'game.exe';path.write_bytes(b'not-an-exe')
   proc=subprocess.run([sys.executable,str(a.__file__),'--exe',str(path),'--out',str(path)],capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0)
   self.assertEqual(path.read_bytes(),b'not-an-exe')
 @unittest.skipUnless(os.environ.get('WH3_NEW_EXE'),'private WH3 EXE not present in public CI')
 def test_18_real_new_exe_all_evidence(self):
  result=a.audit(os.environ['WH3_NEW_EXE'])
  self.assertEqual(result['verified_full_opcodes'],111)
  self.assertEqual(result['verified_direct_calls'],13)
  self.assertEqual(result['verified_conditional_edges'],9)
  self.assertEqual(result['verified_typed_vtable_slots'],7)
  self.assertEqual(len(result['all_direct_e8_to_goal_delta_handler']['0x3065db8']),4)
  self.assertIn('buffered_vector_live_goal_temporal_seam',result)
  self.assertFalse(result['root_cause_proven'])
  self.assertFalse(result['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
