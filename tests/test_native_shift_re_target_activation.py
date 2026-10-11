"""Read-only contracts; synthetic examples are NOT gameplay simulation."""
import importlib.util
import json
from pathlib import Path
import struct
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=next((p for p in [ROOT/'src'/'audit_target_activation.py',
  ROOT/'maintenance_tools'/'native_shift_re'/'audit_903_target_activation.py'] if p.exists()), None)
if SOURCE is None: raise FileNotFoundError('target activation auditor not found')
spec=importlib.util.spec_from_file_location('bsc_activation',SOURCE)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
GAME=Path(os.environ.get('WH3_903_EXE','/mnt/data/Warhammer3.exe'))

class StaticNativeActivation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=a.verify(GAME) if GAME.exists() else None

 def test_sha_is_pinned(self):
  self.assertEqual(len(a.SHA),64)

 def test_original_group_issue_order(self):
  g=a.OPCODES
  self.assertLess(g['group_generate_once'][0],g['group_load_indexed_member'][0])
  self.assertLess(g['group_load_indexed_member'][0],g['group_call_actor_virtual'][0])
  self.assertLess(g['group_call_actor_virtual'][0],g['group_postprocess_after_loop'][0])

 def test_no_group_member_completion_barrier_in_this_loop(self):
  self.assertIn('group_increment_index',a.OPCODES)
  self.assertIn('group_loop_count',a.OPCODES)
  self.assertIn('group_postprocess_after_loop',a.OPCODES)

 def test_receiver_immediate_goal_transform_to_pose(self):
  self.assertEqual(a.EDGES['actor_target_transform'][1],0x0307f5c8)
  self.assertEqual(a.EDGES['mode0_pose_receiver'][1],0x0315ec98)
  self.assertEqual(a.OPCODES['pose_write_xy_branch_a'][0],0x0315f311)
  self.assertEqual(a.OPCODES['pose_write_heading'][0],0x0315f34d)

 def test_new_subaction_distinct_from_main_goal_record(self):
  self.assertEqual(a.VTABLES['new_status_subaction_tick'][1],0x0325c818)
  self.assertEqual(a.EDGES['actor_new_subaction_ctor'][1],0x03248b0c)
  self.assertEqual(a.OPCODES['other_motor_goal_write_A'][0],0x03071e35)

 def test_per_actor_subaction_activation_gate(self):
  self.assertEqual(a.EDGES['actor_tick_update_subaction'][1],0x03080f4c)
  self.assertEqual(a.OPCODES['subaction_virtual_start'][1],'ff5008')
  self.assertEqual(a.OPCODES['subaction_virtual_tick'][1],'ff5010')
  self.assertEqual(a.OPCODES['subaction_local_counter'][1],'ff4314')

 def test_distance_uses_same_actor_specific_transform(self):
  self.assertEqual(a.EDGES['group_metric_uses_same_target_transform'][1],
                   a.EDGES['actor_target_transform'][1])
  self.assertEqual(a.EDGES['group_metric_calculator'][1],0x030d572c)

 def test_group_mean_is_not_all_members_barrier(self):
  distances=[0.0,0.0,0.0,4.0]
  limit=1.5
  self.assertLess(sum(distances)/len(distances),limit)
  self.assertGreater(max(distances),limit)
  self.assertTrue(any(d>limit for d in distances))
  # Synthetic input only. Real engine has variable threshold and other gates.

 def test_group_has_additional_far_count_predicate_elsewhere(self):
  self.assertEqual(a.OPCODES['other_gate_checks_far_actor_count'][0],0x0327e644)
  self.assertEqual(a.EDGES['other_gate_group_freshness'][1],0x030d5628)

 def test_rejects_non_relative_opcode(self):
  with self.assertRaisesRegex(ValueError,'NOT_REL32'):
   a.signed_target(0x1000,b'\x90'*5)

 def test_backwards_signed_e8(self):
  self.assertEqual(a.signed_target(0x1000,b'\xe8\xfb\xff\xff\xff'),0x1000)

 def test_wrong_exe_fails_closed_without_write(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'wrong.exe';original=b'MZwrongbuild';p.write_bytes(original)
   with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):a.verify(p)
   self.assertEqual(p.read_bytes(),original)

 def test_cli_output_never_overwrites_exe(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'wrong.exe';b=b'MZwrong';p.write_bytes(b)
   cp=subprocess.run([sys.executable,str(SOURCE),'--exe',str(p),'--out',str(p)],
     capture_output=True,text=True)
   self.assertNotEqual(cp.returncode,0)
   self.assertEqual(p.read_bytes(),b)

 def test_original_exe_opcodes_call_edges_and_vtables(self):
  if self.data is None:self.skipTest('Original user EXE not mounted')
  self.assertEqual(self.data['machine_guard_count'],52)
  self.assertEqual(self.data['verified_native_edges'],12)
  self.assertEqual(self.data['verified_action_vtable_slots'],2)
  self.assertEqual(self.data['exception_function_count'],209180)

 def test_does_not_claim_motor_goal_automatically_replaced(self):
  if self.data is None:self.skipTest('Original user EXE not mounted')
  self.assertEqual(self.data['separate_motor_path']['direct_edges_from_audited_receivers'],[])
  self.assertFalse(self.data['native_patch_authorized'])

 def test_no_dynamic_v3_execution_claim(self):
  if self.data is None:self.skipTest('Original user EXE not mounted')
  self.assertTrue(any('zero hits' in x for x in self.data['limits']))

 def test_no_process_patching_in_source(self):
  src=SOURCE.read_text(encoding='utf8')
  self.assertNotIn('WriteProcessMemory(',src)
  self.assertNotIn('VirtualProtect(',src)
  self.assertNotIn('OpenProcess(',src)

if __name__=='__main__':unittest.main()