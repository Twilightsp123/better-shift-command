"""Packet constructor negative proof and independent v+0x368 census."""
import json,os,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(HERE))
import audit_actual_trace_packet_provenance as a

class NativePacketProvenanceTests(unittest.TestCase):
 def test_constructor_exact_opcode_sites(self):
  self.assertEqual(a.PINS[0x02f5f940],'80c906')
  self.assertEqual(a.PINS[0x02f5f956],'49c7424403000000')
  self.assertEqual(a.PINS[0x03265d3f],a.PINS[0x030d550f])
  self.assertEqual(len(a.PINS),9)
 def test_unattributed_receiver_with_flag2_and_qword0(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'capture.jsonl'
   packet=bytearray(88)
   packet[0x50]=2
   path.write_text(json.dumps({'type':'event','ev':'B_DEFERRED_RECEIVE',
     'member':'0x1','packet58':packet.hex()})+'\n',encoding='utf8')
   p=a.audit_log(path)
   self.assertEqual(p['incompatible_with_unmodified_B_constructor_flag50'],1)
   self.assertEqual(p['incompatible_with_unmodified_B_constructor_qword44'],1)
   self.assertFalse(p['B_fanout_proven'])
   self.assertFalse(p['patch_authorized'])
 def test_builder_compatible_bytes_do_not_prove_B_source(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'capture.jsonl';packet=bytearray(88)
   packet[0x50]=6;packet[0x44:0x4c]=(3).to_bytes(8,'little')
   path.write_text(json.dumps({'type':'event','ev':'B_DEFERRED_RECEIVE',
     'member':'0x1','packet58':packet.hex()})+'\n',encoding='utf8')
   p=a.audit_log(path)
   self.assertEqual(p['incompatible_with_unmodified_B_constructor_flag50'],0)
   self.assertEqual(p['incompatible_with_unmodified_B_constructor_qword44'],0)
   self.assertFalse(p['B_fanout_proven'])
 def test_wrong_binary_does_not_advance_to_census(self):
  from audit_wh3_full_native_chain import StrictPE
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'wrong.exe';data=b'MZ'+b'invalid'*200;path.write_bytes(data)
   with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):StrictPE(path)
   self.assertEqual(data,path.read_bytes())
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'CI excludes original WH3 executable')
 def test_original_binary_census(self):
  proof=a.audit_binary(Path(os.getenv('WH3_903_EXE')))
  self.assertEqual(proof['raw_v368_candidates'],59)
  self.assertEqual(proof['decoded_v368_callsites'],53)
  self.assertEqual(proof['checked_original_opcode_guards'],9)
 @unittest.skipUnless(os.getenv('BSC_REAL_TRACE_JSONL'),'user trace not present in CI')
 def test_real_trace(self):
  p=a.audit_log(Path(os.getenv('BSC_REAL_TRACE_JSONL')))
  self.assertEqual(p['jsonl_records'],157)
  self.assertEqual(p['mode_gated_receivers_not_B_proven'],28)
  self.assertEqual(p['incompatible_with_unmodified_B_constructor_qword44'],28)
  self.assertFalse(p['queued_Shift_proven'])
if __name__=='__main__':unittest.main()
