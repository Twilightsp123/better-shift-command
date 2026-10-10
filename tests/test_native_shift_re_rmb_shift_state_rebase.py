"""Exact original EXE static link regression and separate structural transfer model."""
import copy, hashlib, os, struct, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"maintenance_tools"/"native_shift_re"))
import audit_903_rmb_shift_state_rebase as r

class RmbVsQueuedState(unittest.TestCase):
 def test_fresh_ctor_statezero(self):
  a=r.model_fresh(); self.assertEqual(struct.unpack_from('<I',a,0x20)[0],0)
  self.assertEqual(struct.unpack_from('<Q',a,0x160)[0],0)
 def test_queue_rebase_writes_payload_into_active_fields(self):
  a=r.model_fresh(); pending=bytes(range(0x30))
  ident=id(a)
  r.model_queued_rebase(a,pending)
  self.assertEqual(id(a),ident)
  self.assertEqual(struct.unpack_from('<I',a,0x20)[0],1)
  self.assertEqual(a[0x120:0x150],pending)
  self.assertEqual(a[0x60:0x80],pending[:0x20]);self.assertEqual(a[0x80:0xa0],pending[:0x20])
  self.assertEqual(a[0xa0:0xac],pending[0x20:0x2c])
 def test_transfer_does_not_touch_nested_pointer_before_native_reset(self):
  a=r.model_fresh();struct.pack_into('<Q',a,0x160,0x12345678)
  r.model_queued_rebase(a,bytes([0x77]*0x30))
  self.assertEqual(struct.unpack_from('<Q',a,0x160)[0],0x12345678)
  # Both actual native branches call 0x031086F8, which then assigns +0x160.
  self.assertEqual(r.GUARDS['native_reset_replaces_nested_route_context'][0],0x03108808)
 def test_independent_regular_move_does_not_inherit_previous_pointer(self):
  old=r.model_fresh();struct.pack_into('<Q',old,0x160,0x12345678)
  fresh=r.model_fresh();self.assertEqual(struct.unpack_from('<Q',fresh,0x160)[0],0)
  self.assertIsNot(fresh,old)
 def test_compatibility_gate_borderline(self):
  self.assertTrue(r.native_inherited_state_remains(5.0,5.0,0.0))
  self.assertTrue(r.native_inherited_state_remains(5.005,5.0,0.0))
  self.assertFalse(r.native_inherited_state_remains(5.2,5.0,0.0))
  self.assertFalse(r.native_inherited_state_remains(5.0,5.0,0.0,state25=1))
  self.assertFalse(r.native_inherited_state_remains(5.0,5.0,0.0,extra_gate=False))
 def test_same_native_solver_both_phases(self):
  self.assertEqual(r.EDGES['native_state1_uses_shared_route_solver'][1],
                   r.EDGES['native_state0_uses_shared_route_solver'][1])
 def test_nested_reset_in_both_phases(self):
  self.assertEqual(r.EDGES['native_planner_fresh_reset_context'][1],
                   r.EDGES['native_planner_reused_reset_context'][1])
 def test_wrong_struct_fail(self):
  with self.assertRaises(ValueError):r.model_queued_rebase(bytearray(1),b'\0'*0x30)
  with self.assertRaises(ValueError):r.model_queued_rebase(r.model_fresh(),b'\0'*0x2f)
 def test_opcode_and_call_census(self):
  self.assertEqual(len(r.GUARDS),60);self.assertEqual(len(r.EDGES),24);self.assertEqual(len(r.VTABLE),4)
 def test_byte_guard_captures_rebase(self):
  self.assertEqual(r.GUARDS['transfer_sets_state_one'],(0x030408CF,'c7422001000000'))
  self.assertEqual(r.GUARDS['state1_activate_140_to_a0_store'][0],0x0311E600)
 def test_call_decode(self):
  self.assertEqual(r.e8_target(0x1000,bytes.fromhex('e805000000')),0x100a)
  self.assertEqual(r.e8_target(0x1000,bytes.fromhex('e8fbffffff')),0x1000)
  with self.assertRaises(ValueError):r.e8_target(0x1000,b'\x90'*5)
 def test_not_all_native_objects_have_same_rva(self):
  self.assertNotEqual(r.VTABLE['MOVE_provider_virtual_40'][1],r.VTABLE['MOVE_successor_transfer_virtual_48'][1])
 def test_wrong_build_cannot_write(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fake.exe';orig=b'MZ'+b'\0'*512;p.write_bytes(orig)
   with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):r.original_contract(p)
   self.assertEqual(p.read_bytes(),orig)
 def test_report_cannot_overwrite_exe(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fake.exe';orig=b'not an exe';p.write_bytes(orig)
   res=subprocess.run([sys.executable,str(Path(r.__file__)),'--exe',str(p),'--report',str(p)],capture_output=True,text=True)
   self.assertNotEqual(res.returncode,0);self.assertEqual(p.read_bytes(),orig)
 def test_exe_read_only_orig_sha(self):
  exe=os.getenv('WH3_903_EXE')
  if not exe:self.skipTest('Original game EXE not available on this runner')
  report=r.original_contract(Path(exe))
  self.assertEqual(report['source_exe_sha256'],r.SHA)
  self.assertEqual(len(report['machine_instruction_guards']),60)
  self.assertEqual(len(report['direct_e8_calls']),24)
  self.assertEqual(len(report['vtables']),4)
  self.assertEqual(len(report['native_constants']),2)
  self.assertEqual(report['exception_functions'],209180)
  self.assertFalse(report['patch_authorized'])
 def test_no_patch_or_queue_mutation_source(self):
  src=Path(r.__file__).read_text()
  for forbidden in ['WriteProcessMemory(', 'VirtualProtect(', 'OrderHead =','runtime_patch_authorized=True']:
   self.assertNotIn(forbidden,src)
 def test_required_branch_coverage(self):
  for key in ['native_planner_state0_branch','native_planner_state1_branch','fresh_state_ctor_sets_zero',
              'transfer_pending_block_120','state1_solver_load_existing_nested','native_route_builder_from_planner',
              'fresh_state_planner_reset','reused_state_planner_reset','native_reset_replaces_nested_route_context',
              'move_worker_reuse_tolerance_001','move_worker_null_old_state',
              'state0_origin_load_current_geometry','group_current_geometry_source_flag']:
   self.assertIn(key,r.GUARDS)
if __name__=='__main__':unittest.main()