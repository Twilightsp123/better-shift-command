"""Native MOVE->member action switch forensic contracts; game EXE is read-only."""
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO_SCRIPT=HERE.parent/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(REPO_SCRIPT if REPO_SCRIPT.exists() else HERE))
import audit_move_actor_action as a

class NativeActionLinkTests(unittest.TestCase):
 def test_original_packet_constants(self):
  p=a.decode_packet()
  self.assertEqual(p['packet_flag50'],0x26)
  self.assertEqual(p['command_code34'],0)
  self.assertEqual(p['option_51_low2_guaranteed'],3)
  self.assertTrue(p['option_51_full_value_unknown'])
  self.assertFalse(p['deferred_member_task'])
  self.assertTrue(p['receiver_uses_optional_transformed_packet'])
  self.assertTrue(p['member_action_zero_code_replacement'])
 def test_machine_branch_flags(self):
  self.assertTrue(0x26&0x20)
  self.assertEqual(0xd600 & 1,0)
  self.assertFalse(bool((0xd600>>0)&1))
  self.assertTrue(bool((0xd600>>9)&1))
 def test_member_subtype_census(self):
  self.assertEqual(sum(a.EXPECTED_COMMON_E8.values()),36)
  self.assertEqual(a.EXPECTED_COMMON_E8[0x03073224],28)
  self.assertEqual(a.EXPECTED_COMMON_E8[0x02F4F910],4)
 def test_action_class_different_from_contact(self):
  self.assertNotEqual(0x03914618,0x03ACD208)
  self.assertNotEqual(0x03914618,0x03ACD468)
  self.assertEqual(a.VTABLES['new_status_class_v10'][1],0x0325C818)
 def test_clear_old_action_only_if_owned(self):
  self.assertEqual(a.GUARDS['cleanup_check_owned_action'][0],0x02DB0A1E)
  self.assertEqual(a.GUARDS['cleanup_virtual_dispose'][0],0x02DB0A2F)
  self.assertEqual(a.GUARDS['cleanup_clear_owned_action_flag'][0],0x02DB0A31)
 def test_optional_member_target_conversion_is_enabled(self):
  self.assertEqual(a.GUARDS['fanout_enable_target_adjustment'][1],'c644242001')
  self.assertEqual(a.EDGES['packet_ctor_actor_adjustment'],(0x02F5F8CD,0x02F72520))
  self.assertEqual(a.EDGES['receiver_member_target_adjustment'],(0x0306BA75,0x0307F5C8))
  self.assertEqual(a.GUARDS['member_heading_reads_scale'][0],0x0307F494)
 def test_packet_zero_initialized_in_30_qword(self):
  self.assertEqual(a.GUARDS['packet_zero_qword_30'][1],'48894b30')
  self.assertEqual(a.GUARDS['packet_code_26'][1],'c6435026')
 def test_retirement_installs_new_class(self):
  self.assertEqual(a.EDGES['reset_old_member_subaction'],(0x0306BBAE,0x02DB0A10))
  self.assertEqual(a.EDGES['build_new_0x81_subaction'],(0x0306BBD5,0x03248B0C))
 def test_direct_call_decoding_signed_offsets(self):
  self.assertEqual(a.direct_target(0x1000,bytes.fromhex('e805000000')),0x100a)
  self.assertEqual(a.direct_target(0x1000,bytes.fromhex('e8fbffffff')),0x1000)
  with self.assertRaises(ValueError):a.direct_target(0x1000,b'\x90'*5)
 def test_rmb_and_shift_not_separate_member_dispatchers(self):
  self.assertIn('fanout_copy',a.EDGES)
  self.assertIn('common_actor_cache_tail',a.EDGES)
  self.assertIn('conditional_bridge',a.EDGES)
 def test_wrong_exe_sha_rejected_without_mutation(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'sample.exe';b=b'MZ\x00\x00not correct';f.write_bytes(b)
   with self.assertRaisesRegex(ValueError,'WRONG_EXE_SHA'):a.audit(f)
   self.assertEqual(f.read_bytes(),b)
 def test_cannot_write_report_over_exe(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'sample.exe';f.write_bytes(b'MZwrong')
   run=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(run.returncode,0)
   self.assertEqual(f.read_bytes(),b'MZwrong')
 def test_no_memory_patching_calls(self):
  src=Path(a.__file__).read_text('utf8')
  for token in ['WriteProcessMemory(','VirtualProtect(','MinHook','native_patch_authorized\':True']:
   self.assertNotIn(token,src)
 def test_exact_original_binary(self):
  env=os.environ.get('WH3_903_EXE')
  if not env:self.skipTest('No original pinned binary in portable CI')
  r=a.audit(Path(env))
  self.assertGreaterEqual(r['opcode_guards'],30)
  self.assertGreaterEqual(r['direct_call_edges'],10)
  self.assertEqual(r['common_receiver_count'],36)
  self.assertEqual(r['total_member_vtables'],38)
  self.assertFalse(r['native_patch_authorized'])
 def test_report_clarifies_conditional_scope(self):
  f=os.environ.get('WH3_903_EXE')
  if not f:self.skipTest('No pinned EXE')
  r=a.audit(Path(f))
  self.assertTrue(any('V3' in s for s in r['limits']))
  self.assertTrue(any('not prove the full motor' in s for s in r['limits']))
 def test_no_universal_assertion(self):
  src=Path(a.__file__).read_text('utf8')
  self.assertIn('not proof that V3 took',src)
  self.assertIn('member_action_zero_code_replacement',src)

if __name__=='__main__':unittest.main()