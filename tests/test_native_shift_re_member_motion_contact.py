"""Synthetic CI contracts for WH3 9.0.3 member-motion/contact distinction.

No EXE distributed. If WH3_903_EXE is supplied, also run exact original checks.
"""
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"maintenance_tools"/"native_shift_re"
sys.path.insert(0,str(SOURCE))
import audit_903_member_motion_contact as a

class NativeMemberMotionContactTests(unittest.TestCase):
 def test_constructor_type_census(self):
  self.assertEqual(sum(a.FAMILY.values()),38)
  self.assertEqual(a.FAMILY[0x03081EB4],10)
  self.assertEqual(a.FAMILY[0x02F854AC],9)
  self.assertEqual(a.FAMILY[0x02F83F44],8)
 def test_direct_call_contract(self):
  self.assertEqual(len(a.CALLS),17)
  self.assertEqual(a.CALLS["common_to_contact_screen"],(0x030824A6,0x0308489C))
  self.assertEqual(a.CALLS["group_update_contact_roll"],(0x030E0C9F,0x030D3D7C))
 def test_original_opcodes_were_frozen(self):
  self.assertEqual(len(a.GUARDS),18)
  self.assertIn("same_owner_skip",a.GUARDS)
  self.assertIn("other_type_matrix_write",a.GUARDS)
 def test_same_offset_has_two_type_producers(self):
  self.assertEqual(a.GUARDS["child_path_fraction"][0],0x02F8411F)
  self.assertEqual(a.GUARDS["other_type_matrix_write"][0],0x0308B798)
  self.assertNotEqual(a.GUARDS["child_path_fraction"][1],a.GUARDS["other_type_matrix_write"][1])
 def test_signed_call_verification(self):
  self.assertEqual(a.e8_target(0x1000,b"\xe8\x05\0\0\0"),0x100a)
  self.assertEqual(a.e8_target(0x1000,b"\xe8\xfb\xff\xff\xff"),0x1000)
  with self.assertRaises(ValueError):a.e8_target(0x1000,b"\x90"*5)
 def test_native_group_contact_exit_and_rollover(self):
  self.assertEqual(a.GUARDS["same_owner_skip"][0],0x030849A4)
  self.assertEqual(a.GUARDS["pair_again_skip"][0],0x030C67D0)
  self.assertEqual(a.GUARDS["clear_contact_count"][0],0x030D3E24)
 def test_wrong_sha_fails_without_writing(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/"wrong.exe";data=b"MZ"+"not original".encode()
   path.write_bytes(data)
   with self.assertRaisesRegex(ValueError,"EXE_SHA_MISMATCH"):a.diagnose(path)
   self.assertEqual(path.read_bytes(),data)
 def test_never_overwrites_original_binary(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/"wrong.exe";data=b"MZwrong";path.write_bytes(data)
   r=subprocess.run([sys.executable,str(SOURCE/"audit_903_member_motion_contact.py"),
                      "--exe",str(path),"--out",str(path)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertEqual(path.read_bytes(),data)
 def test_no_native_patch_or_queue_mutation(self):
  text=(SOURCE/"audit_903_member_motion_contact.py").read_text(encoding="utf8")
  for term in ["WriteProcessMemory(","VirtualProtect(","OrderHead=","patch_authorized=True"]:
   self.assertNotIn(term,text)
 def test_exact_game_if_available(self):
  exe=os.environ.get("WH3_903_EXE")
  if not exe:self.skipTest("original EXE not present in GitHub CI")
  result=a.diagnose(Path(exe))
  self.assertEqual(result["constructor_member_vtables"],38)
  self.assertEqual(result["opcode_guards"],18)
  self.assertEqual(len(result["direct_edges"]),17)
  self.assertFalse(result["patch_authorized"])

if __name__=="__main__":unittest.main()
