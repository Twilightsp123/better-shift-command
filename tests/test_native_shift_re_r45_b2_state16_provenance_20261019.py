#!/usr/bin/env python3
"""R45 read-only regression. Synthetic tests are NOT gameplay evidence."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[0]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(TOOLS))
import audit_r45_b2_state16_provenance_20261019 as r45

class TestR45(unittest.TestCase):
 def test_manifest_count_and_groups(self):
  gs=r45.groups()
  self.assertEqual((len(gs),sum(len(g['pins']) for g in gs.values())),(13,107))
 def test_b2_sender_indirect_member_slot(self):
  gs=r45.groups();self.assertEqual(gs['b2_sender']['pins'][0x0326ABAF],bytes.fromhex('ff9068030000'))
 def test_packet_bit20_always_clear_in_verified_B2_constructor(self):
  for bit0 in (0,1):
   for bit4 in (0,1):
    for optional8 in (0,0x08):
     packet_50=0x06|bit0|(bit4<<4)|optional8
     self.assertEqual(packet_50&0x20,0)
 def test_mode_zero_inline_task_not_action(self):
  for flags in (0x06,0x07,0x16,0x17,0x0e,0x1f):
   self.assertEqual(r45.classify_packet_mode(False,flags),'inline_4a8')
 def test_mode_nonzero_member_actions(self):
  for flags in (0x06,0x07,0x16,0x17,0x0e,0x1f):
   self.assertEqual(r45.classify_packet_mode(True,flags),'member_virtual_and_action_330')
 def test_bit20_overrides_helper(self):
  self.assertEqual(r45.classify_packet_mode(False,0x26),'member_virtual_and_action_330')
 def test_receiver_special_kinds(self):
  self.assertEqual([k for k in range(16) if r45.packet_action_type(k)=='packet_special'],[9,10,12,14,15])
 def test_generic_kinds_include_B2_67_to_69(self):
  for kind in (0x67,0x68,0x69):self.assertEqual(r45.packet_action_type(kind),'packet_generic')
 def test_constructor_addresses_distinct(self):
  self.assertNotIn(0x0324DBAC,(0x0324E2C8,0x0324D994))
 def test_own_vtables_distinct(self):
  self.assertEqual(r45.TABLES[0x03AE22D0,0x08],0x0325E4B4)
  self.assertEqual(r45.TABLES[0x03919B28,0x08],0x0325D9FC)
  self.assertEqual(r45.TABLES[0x039199F8,0x08],0x0325E824)
 def test_member_receiver_has_specific_ctor_edge(self):
  self.assertEqual(r45.E8[0x03070BF8],0x0324E2C8)
  self.assertEqual(r45.E8[0x03070C2D],0x0324D994)
  self.assertEqual(r45.E8[0x0306F733],0x0324DBAC)
 def test_state16_cached_vector_is_three_floats(self):
  gs=r45.groups();d=gs['state16_vector_task_ctor']['pins']
  for a,displacement in [(0x0324DBC8,0x38),(0x0324DBD0,0x3c),(0x0324DBD8,0x40)]:
   self.assertEqual(d[a],bytes.fromhex('418942')+bytes([displacement]))
 def test_action_task_tail_is_byte_zero_not_vector_third_component(self):
  gs=r45.groups()
  for name,site in [('packet_special_action_ctor',0x0324E2E8),('packet_generic_action_ctor',0x0324D9B4)]:
   self.assertEqual(gs[name]['pins'][site],bytes.fromhex('c6414000'))
 def test_action_to_member_state_restore_calls(self):
  for a in (0x03261A77,0x03261CAB,0x03263D9F):self.assertEqual(r45.E8[a],0x03081D40)
  self.assertEqual(r45.E8[0x03081ED6],0x03164710)
 def test_no_game_patch_authorized(self):
  self.assertTrue(r45.SHA.startswith('9bd58c63'))
  self.assertFalse(hasattr(r45,'inject'))
 def test_incorrect_exe_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'Warhammer3.exe';f.write_bytes(b'MZ'+bytes(90))
   with self.assertRaisesRegex(ValueError,'EXE_MISSING_OR_SIZE_DRIFT'):r45.audit(f)
 def test_cli_cannot_overwrite_input(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'Warhammer3.exe';f.write_bytes(b'Keep unchanged')
   r=subprocess.run([sys.executable,str(r45.__file__),'--exe',str(f),'--out',str(f)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(f.read_bytes(),b'Keep unchanged')
 @unittest.skipUnless(os.getenv('WH3_R45_EXE'),'private new EXE intentionally absent in public CI')
 def test_real_new_exe(self):
  got=r45.audit(os.environ['WH3_R45_EXE'])
  self.assertEqual(got['exe_sha256'],r45.SHA)
  self.assertEqual((got['verified_instruction_starts'],got['verified_direct_e8'],got['verified_jump_edges'],got['verified_typed_vtable_slots']),(107,22,6,8))
  self.assertEqual(got['state16_buffer_task_constructor_direct_callers'],['0x306f733'])
  self.assertEqual(got['state16_member_method_direct_e8_callers'],[])
  self.assertFalse(got['direct_B2_packet_installs_R44_vector_task'])
  self.assertFalse(got['motion_crowding_root_cause_proven'])
  self.assertFalse(got['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
