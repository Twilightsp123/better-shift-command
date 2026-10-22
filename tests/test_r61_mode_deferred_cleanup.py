#!/usr/bin/env python3
import os,sys,unittest,tempfile,subprocess,hashlib,struct
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'maintenance_tools'/'native_shift_re'))
import audit_r61_mode_deferred_cleanup as a

class NativeModeAndDeferredCleanup(unittest.TestCase):
 def test_mode_helper_true_exact_set(self):
  self.assertEqual([n for n in range(40) if a.helper(n)], [0,3,5])
 def test_mode_helper_false_newest_modes(self):
  self.assertTrue(all(not a.helper(n) for n in range(6,33)))
 def test_bad_mode_rejected(self):
  for bad in (-1,0x100000000,None,1.4):
   with self.assertRaises(ValueError):a.helper(bad)
 def test_b2_packet_flag20_never_set(self):
  for i in range(4):
   for j in range(4):
    for flag in [False,True]:
     v=a.packet_bit20_from_b2(i,j,flag)
     self.assertEqual(v&0x20,0)
     self.assertEqual(v&0x06,0x06)
 def test_b2_fixed_mode_never_split_into_deferred_then_immediate(self):
  for m in range(16):
   results=set()
   for u in range(2):
    for v in range(2):
     for optional in (False,True):
      packet=a.packet_bit20_from_b2(u,v,optional)
      results.add(a.receiver_packet_path(m,packet)['path'])
   self.assertEqual(len(results),1,('mode',m,'paths',results))
 def test_regular_member_e8_clears_only_in_modes_6_9_with_extra_flag(self):
  for m in range(16):
   x=a.receiver_packet_path(m,0x20,member104=3)
   self.assertEqual(x['transitively_cleans_delayed'],6<=m<=9)
 def test_member104_routes(self):
  for state in (1,2):
   x=a.receiver_packet_path(6,0x20,member104=state)
   self.assertEqual(x['member_method'],'+0x100')
   self.assertFalse(x['transitively_cleans_delayed'])
  for state in (0,3,4,16):
   x=a.receiver_packet_path(6,0x20,member104=state)
   self.assertEqual(x['member_method'],'+0xE8')
   self.assertTrue(x['transitively_cleans_delayed'])
 def test_no_clear_inferred_from_missing_explicit_E8(self):
  d=a.receiver_packet_path(1,0x20,member104=3)
  self.assertEqual(d['note'],'CLEANUP_NOT_PROVEN_BY_THIS_DIRECT_CHAIN')
  self.assertFalse(d['transitively_cleans_delayed'])
 def test_member_kind_validation(self):
  with self.assertRaises(ValueError):a.receiver_packet_path(0,0,member_kind='fake')
 def test_deferred_branch_has_independent_cleanup(self):
  d=a.receiver_packet_path(6,a.packet_bit20_from_b2(0,0))
  self.assertEqual(d['path'],'deferred')
  self.assertEqual(d['note'],'DEFERRED_REPLACES_PRIOR_DEFERRED_VIA_RECEIVER')
 def test_branch_dest_helpers(self):
  self.assertEqual(a.branch_target(0x03070A85,bytes.fromhex('7536')),0x03070ABD)
 def test_static_pins_expected_count(self):self.assertEqual(len(a.read_pins()),71)
 def test_static_call_map_contains_transitive_cleanup(self):
  self.assertEqual(a.E8[0x030782B0],0x0307AE84)
  self.assertEqual(a.E8[0x0307AE9B],0x02DB5AC4)
 def test_known_relevant_member_vtables(self):
  self.assertEqual(a.MEMBER_TABLES['regular'][1][0xe8],0x03078268)
  self.assertEqual(a.MEMBER_TABLES['regular'][1][0x478],0x03078944)
 def test_output_cannot_overwrite_binary(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'game.exe';f.write_bytes(b'MZ')
   p=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertEqual(f.read_bytes(),b'MZ')
 def test_bad_binary_sha_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'bad.exe';f.write_bytes(b'MZ'+bytes(128))
   with self.assertRaisesRegex(ValueError,'EXE_SHA_MISMATCH'):
    a.static_audit(f)
 @unittest.skipUnless(os.getenv('WH3_NEW_EXE'),'private user WH3 EXE not available; do not report CI as true-binary PASS')
 def test_actual_exe_static_contract(self):
  d=a.static_audit(Path(os.getenv('WH3_NEW_EXE')))
  self.assertEqual((d['fixed_machine_code_pins'],d['verified_e8'],d['verified_branches'],d['typed_member_vtable_slots']), (71,17,8,6))
  self.assertEqual(d['delayed_cleanup_direct_callers_in_udata'],81)
  self.assertFalse(d['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main(verbosity=2)
