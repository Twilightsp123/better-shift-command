"""Exact-original B cache->member packet audit: executable/static test boundaries."""
import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_b_route_to_member_packets as a

class BRoutePacketBridgeTests(unittest.TestCase):
 def test_B_subtype_and_main_are_different_classes(self):
  self.assertEqual(a.VTABLES['cached_subtype_v10'],(0x3ae00f8,0x3281520))
  self.assertEqual(a.VTABLES['main_B_v10'],(0x3ae0138,0x3281408))
 def test_cache_reader_is_guarded_by_ready_and_pointer(self):
  self.assertEqual(a.PINS['subtype_cache_pointer'][1],'488b4178')
  self.assertEqual(a.PINS['subtype_cache_ready'][1],'80780800')
  self.assertEqual(a.PINS['subtype_node_route_read'][1],'488b4070')
  self.assertEqual(a.PINS['subtype_packet_geometry_pointer'][1],'4889442420')
 def test_bridge_reaches_member_delivery_but_not_proven_main_motor(self):
  self.assertEqual(a.CALLS['cache_to_fanout'],(0x32815c5,0x3265b24))
  self.assertEqual(a.PINS['packet_member_v368'][1],'ff9068030000')
  self.assertNotIn('main_motor',a.CALLS)
 def test_bit7_task_is_separate_native_factory(self):
  self.assertEqual(a.VTABLES['member_task_factory_v90'],(0x3ac7008,0x2f6ef4c))
  self.assertEqual(a.VTABLES['bit7_active_v78'],(0x3905e10,0x2f87684))
  self.assertNotEqual(a.VTABLES['bit7_negative_v78'][1],0x2f87684)
 def test_true_e8_target_math(self):
  s=0x32815c5;t=0x3265b24
  self.assertEqual(a.e8_destination(s,bytes([0xe8])+struct.pack('<i',t-s-5)),t)
  with self.assertRaisesRegex(ValueError,'NOT_E8'):
   a.e8_destination(s,bytes([0xe9])+struct.pack('<i',t-s-5))
 def test_original_version_refused_without_writes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fake.exe';data=b'MZ'+b'wrong version'*20;p.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):a.audit(p)
   self.assertEqual(p.read_bytes(),data)
 def test_no_overwrite_cli(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.exe';data=b'MZ'+b'wrong'*20;p.write_bytes(data)
   cp=subprocess.run([sys.executable,str(SRC/'audit_b_route_to_member_packets.py'),
      '--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(cp.returncode,0);self.assertEqual(p.read_bytes(),data)
 def test_no_unsafe_patch_claim(self):
  self.assertIn('bit7_active_v78',a.VTABLES)
  self.assertEqual(a.PINS['active_task_bit7_read'][1],'8a97100b0000')
  self.assertEqual(a.PINS['B_member_bit7_write'][1],'0883100b0000')
 @unittest.skipUnless(os.environ.get('WH3_903_EXE'),'CI excludes game EXE')
 def test_original_executable_static(self):
  proof=a.audit(Path(os.environ['WH3_903_EXE']))
  self.assertEqual(proof['level'],'ORIGINAL_EXE_STATIC')
  self.assertFalse(proof['patch_authorized'])
  self.assertEqual(proof['machine_guards'],len(a.PINS))
if __name__=='__main__':unittest.main()
