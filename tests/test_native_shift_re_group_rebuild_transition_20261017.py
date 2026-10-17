"""Round31 exact native Group rebuild ordering and synthetic non-atomic ledger."""
import os,sys,json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_group_rebuild_transition_20261017 as native
import group_rebuild_transaction_replay_20261017 as ledger

def event(seq,op,alias='groupa',root='unitx',pool='poolx'):
 return json.dumps({'schema':ledger.SCHEMA,'seq':seq,'event':op,
   'root_id':root,'pool_id':pool,'object_alias':alias})
def sequence(*args):return [event(*x) for x in args]

class NonatomicNativeGroupRebuild(unittest.TestCase):
 def test_native_instruction_inventory(self):self.assertEqual(len(native.pins()),72)
 def test_calls_verified(self):
  self.assertEqual(len(native.E8),15)
  self.assertEqual(native.E8[0x301b902],0x30197a8)
  self.assertEqual(native.E8[0x301b91f],0x301b834)
  self.assertEqual(native.E8[0x30197e0],0x302c2d4)
 def test_direct_caller_inventory(self):self.assertEqual(len(native.CALLERS),4)
 def test_order_and_exact_root_write(self):
  self.assertLess(0x301b902,0x301b91f)
  self.assertLess(0x301b91f,0x301b96d)
  self.assertEqual(native.pins()[0x301b96d].hex(),'48899ef8320000')
 def test_same_address_can_be_rechecked_out_without_clear(self):
  x=ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'rebuild_begin'),
      (4,'return'),(5,'checkout'),(6,'bind'),(7,'rebuild_end'),(8,'snapshot')))
  rows=x['events']
  self.assertTrue(rows[3]['root_pointer_stale_during_transaction'])
  self.assertEqual(rows[3]['object_checkout_incarnation'],1)
  self.assertEqual(rows[5]['object_checkout_incarnation'],2)
  self.assertEqual(rows[1]['root_binding_revision'],1)
  self.assertEqual(rows[5]['root_binding_revision'],2)
  self.assertTrue(rows[7]['stable_snapshot_candidate'])
  self.assertFalse(x['full_native_event_coverage_proven'])
 def test_mid_rebuild_snapshot_never_stable(self):
  x=ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'rebuild_begin'),
      (4,'return'),(5,'snapshot'),(6,'checkout'),(7,'bind'),(8,'rebuild_end')))
  self.assertFalse(x['events'][4]['stable_snapshot_candidate'])
  self.assertTrue(x['events'][4]['root_pointer_stale_during_transaction'])
 def test_rebinding_same_incarnation_not_checkout(self):
  x=ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'rebuild_begin'),
      (4,'clear'),(5,'bind'),(6,'rebuild_end')))
  self.assertEqual(x['events'][4]['object_checkout_incarnation'],1)
  self.assertEqual(x['events'][4]['root_binding_revision'],3)
 def test_bound_return_outside_typed_scope_is_ambiguous(self):
  with self.assertRaisesRegex(ValueError,'AMBIGUOUS_RETURN_BOUND_OUTSIDE_TYPED_REBUILD'):
   ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'return')))
 def test_rebuild_end_with_stale_binding_rejected(self):
  with self.assertRaisesRegex(ValueError,'REBUILD_EXIT_WITH_STALE_BINDING'):
   ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'rebuild_begin'),
      (4,'return'),(5,'rebuild_end')))
 def test_unclosed_scope_rejected(self):
  with self.assertRaisesRegex(ValueError,'UNCLOSED_REBUILD_SCOPE'):
   ledger.replay(sequence((1,'checkout'),(2,'bind'),(3,'rebuild_begin')))
 def test_unmodeled_reentrancy_rejected(self):
  with self.assertRaisesRegex(ValueError,'REENTRANT_SCOPE_NOT_MODELLED'):
   ledger.replay(sequence((1,'rebuild_begin'),(2,'rebuild_begin')))
 def test_double_checkout_rejected(self):
  with self.assertRaisesRegex(ValueError,'DOUBLE_CHECKOUT'):
   ledger.replay(sequence((1,'checkout'),(2,'checkout')))
 def test_unknown_return_rejected(self):
  with self.assertRaisesRegex(ValueError,'RETURN_NOT_OBSERVED_CHECKOUT'):
   ledger.replay(sequence((1,'return')))
 def test_missing_checkout_remains_unknown(self):
  x=ledger.replay(sequence((1,'bind'),(2,'snapshot')))
  self.assertTrue(x['events'][1]['lifecycle_unknown'])
  self.assertFalse(x['events'][1]['stable_snapshot_candidate'])
 def test_raw_pointer_rejected(self):
  with self.assertRaisesRegex(ValueError,'UNTRUSTED_OR_MISSING'):
   ledger.replay(sequence((1,'checkout','0x7ffe123a0000')))
 def test_unsorted_event_rejected(self):
  with self.assertRaisesRegex(ValueError,'NONMONOTONIC_EVENT_SEQUENCE'):
   ledger.replay(sequence((1,'checkout'),(1,'bind')))
 def test_protect_input_from_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'events.jsonl';p.write_text(event(1,'checkout'))
   proc=subprocess.run([sys.executable,str(ledger.__file__),'--jsonl',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0)
   self.assertIn('INPUT_OVERWRITE_FORBIDDEN',proc.stderr)
 def test_wrong_game_build_fails_under_python_o(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'wrong.exe';p.write_bytes(b'MZ'+bytes(100))
   for flags in ([],['-O']):
    proc=subprocess.run([sys.executable,*flags,str(native.__file__),'--exe',str(p)],capture_output=True,text=True)
    self.assertNotEqual(proc.returncode,0)
    self.assertIn('SHA_MISMATCH',proc.stderr)
 def test_game_exe_never_overwritten(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'wrong.exe';p.write_bytes(b'original')
   proc=subprocess.run([sys.executable,str(native.__file__),'--exe',str(p),'--out',str(p)],capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0)
   self.assertEqual(p.read_bytes(),b'original')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original game EXE excluded from public CI')
 def test_real_original_exe(self):
  r=native.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['guarded_decoded_sites'],r['verified_e8']),(72,15))
  self.assertFalse(r['queued_shift_reaches_this_branch_proven'])
  self.assertFalse(r['safe_hook_ready'])
if __name__=='__main__':unittest.main()
