#!/usr/bin/env python3
"""Native R38 static regression. Hypothetical combinations are never gameplay evidence."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path
AUDITS=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(AUDITS))
import audit_r38_packet_heading_motion_20261018 as a

class R38PacketHeadingAudit(unittest.TestCase):
 def test_manifest_pinned_counts(self):
  g=a.manifest()
  self.assertEqual(len(g),14)
  self.assertEqual(sum(len(items) for _,items in g.values()),259)
 def test_call_and_branch_inventory(self):
  self.assertEqual((len(a.E8),len(a.BRANCH),len(a.VIRTUAL)),(23,9,7))
 def test_known_member_vtable_type(self):
  self.assertEqual(a.VIRTUAL[(a.MEMBER_TABLE,0x368)],0x03070A48)
  self.assertEqual(a.VIRTUAL[(a.MEMBER_TABLE,0x100)],0x030785AC)
  self.assertEqual(a.VIRTUAL[(a.MEMBER_TABLE,0xE8)],0x03078268)
 def test_builder_never_sets_packet_bit20(self):
  for b0 in (False,True):
   for b4 in (False,True):
    for special in (False,True):
     for bit6 in (False,True):
      flags=a.packet_flag50(b0,b4,special,bit6)
      self.assertEqual(flags&0x20,0)
      self.assertEqual(flags&0x06,0x06)
 def test_r38_packet_bit2_reaches_member_heading_transform(self):
  self.assertEqual(a.E8[0x0326AB19],0x02F775AC)
  self.assertEqual(a.E8[0x02F775CE],0x030844C8)
  self.assertEqual(a.ASM[0x02F775B9],'test   BYTE PTR [rcx+0x50],0x2')
 def test_bit51_2_is_forced_by_per_member_call(self):
  self.assertEqual(a.ASM[0x02F775B2],'or     BYTE PTR [rcx+0x51],0x2')
  self.assertEqual(a.ASM[0x03070ABD],'test   BYTE PTR [rdx+0x51],0x2')
 def test_type_action_kind_mask_exact(self):
  ks={i for i in range(16) if 'kind_B' in a.receiver_kind(i)}
  self.assertEqual(ks,{9,10,12,14,15})
  self.assertEqual(a.receiver_kind(80),'kind_A_vtable_3919b28')
 def test_kind_action_classes_have_independent_virtual_ticks(self):
  self.assertEqual(a.VIRTUAL[(a.TASK_TABLE_A,0x10)],0x03261688)
  self.assertEqual(a.VIRTUAL[(a.TASK_TABLE_B,0x10)],0x03263AF8)
 def test_receiver_mode0_ignores_member_state_for_inline_path(self):
  for state in (0,1,2,3,4,16):
   self.assertEqual(a.receiver_phase(False,state),'inline_task_4a8')
 def test_receiver_mode1_member_state_1_2(self):
  for state in (1,2):self.assertEqual(a.receiver_phase(True,state),'member_virtual_100')
  for state in (0,3,4,16):self.assertEqual(a.receiver_phase(True,state),'member_virtual_e8')
 def test_member_tick_inline_versus_neighbor_mutually_exclusive_subgraph(self):
  self.assertEqual(a.tick_phase(0x04,4),'inline_action_328')
  self.assertEqual(a.tick_phase(0x04,16),'inline_action_328')
  self.assertEqual(a.tick_phase(0x00,4),'steering_3059bc8')
  self.assertEqual(a.tick_phase(0x00,4,False),'member_other_virtual_490')
  self.assertEqual(a.tick_phase(0x08,4),'member_other_virtual_498')
 def test_action_tick_register_identity(self):
  self.assertEqual(a.ASM[0x0308731B],'lea    rcx,[rdi+0x328]')
  self.assertEqual(a.ASM[0x03085FAB],'lea    rbx,[rcx+0x8]')
 def test_984_is_member_field_read_under_gated_heading_modifier(self):
  self.assertEqual(a.ASM[0x030844E4],'movss  xmm1,DWORD PTR [rcx+0x984]')
  self.assertEqual(a.ASM[0x030532BE],'movss  DWORD PTR [rbx+0x984],xmm0')
 def test_typed_tick_calls_real_native_steering(self):
  self.assertEqual(a.E8[0x03087349],0x03059BC8)
  self.assertEqual(a.E8[0x03087322],0x03085F9C)
 def test_wrong_binary_fails_even_python_optimized(self):
  with tempfile.TemporaryDirectory() as d:
   fake=Path(d)/'wrong.exe';fake.write_bytes(b'MZ'+bytes(256))
   for args in ([],['-O']):
    x=subprocess.run([sys.executable,*args,str(a.__file__),'--exe',str(fake)],capture_output=True,text=True,timeout=30)
    self.assertNotEqual(x.returncode,0)
   self.assertEqual(fake.read_bytes(),b'MZ'+bytes(256))
 def test_exe_input_output_collision_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'input.exe';f.write_bytes(b'important')
   r=subprocess.run([sys.executable,str(a.__file__),'--exe',str(f),'--out',str(f)],capture_output=True,text=True,timeout=20)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(f.read_bytes(),b'important')
 @unittest.skipUnless(os.getenv('WH3_CURRENT_EXE'),'user original new EXE not present in repository CI')
 def test_real_updated_exe_static(self):
  result=a.audit(Path(os.environ['WH3_CURRENT_EXE']))
  self.assertEqual(result['exe_sha256'],a.SHA)
  self.assertEqual((result['verified_opcode_starts'],result['verified_e8'],result['verified_control_transfers'],result['verified_vtable_slots']),(259,23,9,7))
  self.assertTrue(result['B2_packet_flag50_bit20_always_clear_in_verified_sender'])
  self.assertFalse(result['shift_crowding_root_cause_proven'])
  self.assertFalse(result['native_gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
