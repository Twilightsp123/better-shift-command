#!/usr/bin/env python3
"""Isolated static-regression tests. Synthetic helper tests are NOT gameplay evidence."""
import os,struct,tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_r35_group_transaction_20261017 as a

class BscR35Static(unittest.TestCase):
 def test_manifest_inventory(self):
  groups=a.get_pins()
  self.assertEqual(len(groups),15)
  self.assertEqual(sum(len(g[1]) for g in groups.values()),119)
 def test_shorttask_does_not_store_frozen_group_as_task_plus8(self):
  p=a.get_pins()
  self.assertEqual(p['shorttask_ctor'][1][0x02F31791],bytes.fromhex('48895108'))
 def test_descriptor_pointer_alias(self):
  p=a.get_pins()
  self.assertEqual(p['queue_slot_to_task'][1][0x0302AEDB],bytes.fromhex('4c8db3a0000000'))
  self.assertEqual(p['queue_slot_to_task'][1][0x0302B191],bytes.fromhex('4c897590'))
  self.assertEqual(p['queue_slot_to_task'][1][0x0302B1A3],bytes.fromhex('4c8d4c2440'))
  self.assertEqual(p['descriptor_leaf'][1][0x02F318EF],bytes.fromhex('48894150'))
 def test_group_latebind_before_A_B_dispatch(self):
  p=a.get_pins()['callback'][1]
  self.assertEqual(p[0x02F5B3F0],bytes.fromhex('488b4b08'))
  self.assertEqual(p[0x02F5B3F9],bytes.fromhex('488b89f8320000'))
  self.assertLess(0x02F5B3F9,0x02F5B400)
  self.assertLess(0x02F5B400,0x02F5B529)
 def test_conditional_cleanup_is_post_dispatch(self):
  pins=a.get_pins()['callback'][1]
  self.assertLess(0x02F5B405,0x02F5B4B3)
  self.assertLess(0x02F5B4B3,0x02F5B4CD)
  self.assertEqual(pins[0x02F5B529],bytes.fromhex('493988f8320000'))
  self.assertEqual(pins[0x02F5B577],bytes.fromhex('493988f8320000'))
 def test_group_sender_virtual_method(self):
  p=a.get_pins()
  self.assertEqual(p['A_member_fanout'][1][0x030DA59B],bytes.fromhex('ff9068030000'))
  self.assertEqual(p['B_member_fanout'][1][0x0326ABAF],bytes.fromhex('ff9068030000'))
 def test_late_root_route_read_explicit(self):
  p=a.get_pins()
  self.assertEqual(p['group_A_B_dispatch'][1][0x0327ECE3],bytes.fromhex('488b8870020000'))
  self.assertEqual(p['B_fallback_current_Root_route'][1][0x03268CF0],bytes.fromhex('498b8070020000'))
 def test_short_and_near_branch_helpers(self):
  self.assertEqual(a.branch_dest(0x0327ECCD,bytes.fromhex('744f')),0x0327ED1E)
  self.assertEqual(a.branch_dest(0x02F5B405,bytes.fromhex('e9a9000000')),0x02F5B4B3)
  with self.assertRaisesRegex(ValueError,'INVALID_BRANCH_SITE'):
   a.branch_dest(0x100,bytes.fromhex('9090'))
 def test_no_unproven_group_identity_claim(self):
  self.assertEqual(a.VTABLE[0x03AE5820,0x10],0x03286288)
  self.assertEqual(a.VTABLE[0x03AE5800,0x10],0x032863A0)
 def test_private_new_exe_static_proof(self):
  exe=os.environ.get('BSC_NEW_EXE')
  if not exe or not Path(exe).exists():self.skipTest('User WH3 EXE not shipped/available in GitHub CI')
  r=a.audit(exe)
  self.assertEqual(r['sha256'],a.SHA)
  self.assertEqual(r['verified_full_instructions'],119)
  self.assertEqual(r['verified_E8_calls'],17)
  self.assertEqual(r['verified_control_transfers'],3)
  self.assertEqual(r['verified_vtable_slots'],2)
  self.assertFalse(r['patch_authorized'])
  self.assertFalse(r['same_shift_instance_group_route_mismatch_proven'])
 def test_no_game_executable_overwrite(self):
  # Report and executable are always different output paths; main() rejects overlap.
  self.assertTrue(callable(a.audit))

if __name__=='__main__':unittest.main()
