"""Exact-build typed alternate actor timer and action subtype ancestry controls."""
import os,sys,tempfile,unittest
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_alternate_member_timer_families as m
from audit_wh3_full_native_chain import StrictPE

class AlternateMemberTaskFamilies(unittest.TestCase):
 def test_pins_and_typed_slots_exact_counts(self):
  self.assertEqual(len(m.PINS),30)
  self.assertEqual(len(m.CALLS),8)
  self.assertEqual(len(m.VTABLES),17)
  self.assertEqual(len(m.RIP_LEAS),4)
 def test_group_task_fork_is_not_keyboard_RMB_vs_Shift(self):
  self.assertEqual(m.VTABLES[0x03915930],0x0327BD38)
  self.assertEqual(m.PINS[0x0327BD5F],'ff5060')
  self.assertEqual(m.PINS[0x0327BD68],'0f84e4000000')
  self.assertEqual(m.PINS[0x0327BE59],'ff5070')
  self.assertEqual(m.PINS[0x0327BE5F],'742a')
  self.assertEqual(m.CALLS[0x0327BE4B],0x0306B970)
  self.assertEqual(m.CALLS[0x0327BE86],0x0306B54C)
 def test_two_distinct_non_clock_task_families(self):
  self.assertEqual(m.RIP_LEAS[0x0306B581],0x03AC7FF0)
  self.assertEqual(m.RIP_LEAS[0x0306B9A5],0x03AC8200)
  self.assertEqual(m.VTABLES[0x03AC7FF8],0x02F73074)
  self.assertEqual(m.VTABLES[0x03AC8208],0x02F73260)
  self.assertEqual(m.VTABLES[0x03AC8000],0x02F838E8)
  self.assertEqual(m.VTABLES[0x03AC8210],0x02F838E8)
  self.assertEqual(m.PINS[0x02F730A7],'ff90b8040000')
  self.assertEqual(m.PINS[0x02F73292],'ff90c0040000')
 def test_typed_member_dispatch_not_three_action_classes_only(self):
  self.assertEqual(m.VTABLES[0x038FDB10],0x03069948)
  self.assertEqual(m.VTABLES[0x039109B8],0x03069948)
  self.assertEqual(m.VTABLES[0x038FDB18],0x02DC39CC)
  self.assertEqual(m.VTABLES[0x039109C0],0x0306A7E8)
  self.assertEqual(m.RIP_LEAS[0x0304E788],0x03ACD5A0)
  self.assertEqual(m.RIP_LEAS[0x0304ED31],0x03ACD6D0)
  self.assertEqual(m.VTABLES[0x03ACD5A8],0x0307C464)
  self.assertEqual(m.VTABLES[0x03ACD6D8],0x0307CAD0)
 def test_invalid_game_build_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'not-wh3.exe';data=b'MZ'+b'a'*(256)
   p.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
    StrictPE(p)
   self.assertEqual(data,p.read_bytes())
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Public CI intentionally excludes original WH3 game file')
 def test_pinned_original_exe_full_boundaries_edges_and_branches(self):
  r=m.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(r['verified_opcode_boundaries'],30)
  self.assertEqual(r['direct_edges'],8)
  self.assertEqual(r['typed_vtable_slots'],17)
  self.assertFalse(r['rmb_or_shift_player_key_proven'])
  self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
