"""Native-exact guards and bounded original-branch RMB/queued member motion split."""
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC = ROOT/'src' if (ROOT/'src'/'audit_cache_to_motor.py').exists() else ROOT/'maintenance_tools'/'native_shift_re'
DOC = ROOT/'README_中文.md' if (ROOT/'README_中文.md').exists() else ROOT/'docs'/'current'/'N1_903_CACHE_TO_MOTOR_CAUSAL_BOUNDARY_20261011.md'
sys.path.insert(0,str(SRC))
import audit_cache_to_motor as a

class NativeCacheMotorTests(unittest.TestCase):
 def test_exact_original_instruction_count(self):
  self.assertEqual(len(a.GUARDS),56)
  self.assertEqual(a.GUARDS['group_motion_group_lookup'],(0x030886CA,'488bbff8320000'))
 def test_edges_and_pointer_tables(self):
  self.assertEqual(len(a.EDGES),18)
  self.assertEqual(len(a.VFUNC),3)
  self.assertEqual(a.VFUNC['action_type_a_neighbour_update'],(0x03ACD218,0x0308279C))
  self.assertEqual(a.VFUNC['action_type_b_spatial_target_update'],(0x03ACD598,0x0308393C))
  self.assertEqual(a.VFUNC['action_type_b_update'],(0x03ACD478,0x03083120))
 def test_original_e8_forward(self):
  self.assertEqual(a.e8_destination(0x1000,b'\xe8\x05\x00\x00\x00'),0x100a)
 def test_original_e8_back(self):
  self.assertEqual(a.e8_destination(0x1000,b'\xe8\xfb\xff\xff\xff'),0x1000)
 def test_indirect_not_direct(self):
  with self.assertRaisesRegex(ValueError,'NOT_DIRECT_E8'):
   a.e8_destination(0x1000,b'\xff\x50\x10\x90\x90')
 def test_group_stale_cache_rebuilds(self):
  self.assertEqual(a.group_movement_target_decision(flag_e8=0,group_action_mode=1,
        member_enabled=True,candidate_available=True,compatible=False),
      'install_new_target_and_flag_e8')
 def test_group_compatible_cache_keeps(self):
  self.assertEqual(a.group_movement_target_decision(flag_e8=0,group_action_mode=1,
      member_enabled=True,candidate_available=True,compatible=True),'retain_existing_target')
 def test_same_unit_different_actor_cache(self):
  conditions=dict(flag_e8=0,group_action_mode=1,member_enabled=True,candidate_available=True)
  self.assertNotEqual(a.group_movement_target_decision(**conditions,compatible=False),
                      a.group_movement_target_decision(**conditions,compatible=True))
 def test_action_individual_old_association_two_branches(self):
  c=dict(enabled=True,old_cache_present=True,new_spatial_target_found=True)
  self.assertEqual(a.action_movement_target_decision(**c,compatibility_result=False),'full_replace_via_03071e04')
  self.assertEqual(a.action_movement_target_decision(**c,compatibility_result=True),'reuse_via_0306ef1c')
 def test_no_cache_not_a_cache_proof(self):
  self.assertEqual(a.action_movement_target_decision(enabled=True,old_cache_present=False,
      new_spatial_target_found=True,compatibility_result=False),'fallback_action_path')
 def test_branch_prerequisite_disallows_inactive(self):
  for inactive in [{'group_action_mode':0},{'member_enabled':False},{'candidate_available':False}]:
   args=dict(flag_e8=0,group_action_mode=1,member_enabled=True,candidate_available=True,compatible=False)
   args.update(inactive)
   self.assertEqual(a.group_movement_target_decision(**args),'no_target_change')
 def test_prior_action_flag_is_a_different_gate(self):
  self.assertEqual(a.group_movement_target_decision(flag_e8=1,group_action_mode=1,
      member_enabled=True,candidate_available=True,compatible=False),'different_prior_target_check')
 def test_wrong_exe_hash_strict_fail_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'fake.exe'; original=b'MZ fake untrusted EXE';p.write_bytes(original)
   with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):a.audit(p)
   self.assertEqual(p.read_bytes(),original)
 def test_refuse_in_place_report(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'fake.exe'; data=b'MZ fake';p.write_bytes(data)
   cmd=[sys.executable,str(SRC/'audit_cache_to_motor.py'),'--exe',str(p),'--out',str(p)]
   out=subprocess.run(cmd,capture_output=True,text=True)
   self.assertNotEqual(out.returncode,0)
   self.assertEqual(data,p.read_bytes())
 def test_safe_no_live_memory_patch(self):
  text=(SRC/'audit_cache_to_motor.py').read_text(encoding='utf8')
  for forbidden in ('WriteProcessMemory(', 'VirtualProtect(', 'OrderHead=', "'native_patch_authorized':True"):
   self.assertNotIn(forbidden,text)
 def test_original_exe_when_available(self):
  exe=os.getenv('WH3_903_EXE')
  if not exe:self.skipTest('real original Warhammer3.exe not installed in public CI')
  r=a.audit(Path(exe))
  self.assertEqual(r['binary_sha256'],a.SHA256)
  self.assertEqual(len(r['verified_direct_calls']),18)
  self.assertEqual(len(r['exact_instruction_guards']),56)
  self.assertEqual(len(r['verified_virtual_slots']),3)
  self.assertFalse(r['native_patch_authorized'])
  self.assertEqual(r['v3_dynamic_evidence']['branch_taken'],'UNKNOWN')
 def test_machine_trace_does_not_prove_runtime_v3(self):
  t=(SRC/'audit_cache_to_motor.py').read_text(encoding='utf8')
  self.assertIn("'branch_taken':'UNKNOWN'",t)
  self.assertIn('recorded V3 member movement samples',t)
 def test_bundle_contains_verbatim_proof_inputs(self):
  self.assertTrue((SRC/'audit_903_queued_member_activation.py').exists())
  self.assertTrue(DOC.exists())
 def test_nested_target_rollover_path(self):
  self.assertEqual(a.EDGES['fresh_target_to_original_progression'],(0x03071E86,0x03071F20))
  self.assertEqual(a.EDGES['original_move_writer_commits'],(0x03119687,0x03102CA4))
 def test_effect_not_only_pose_rate(self):
  self.assertIn('progression_uses_actual_x',a.GUARDS)
  self.assertIn('motion_writer_copy_active_target',a.GUARDS)
  self.assertIn('original_move_writer_commits',a.EDGES)

if __name__=='__main__':unittest.main()