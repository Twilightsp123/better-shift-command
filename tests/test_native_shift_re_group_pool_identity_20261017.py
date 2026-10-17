"""Round30 fixed EXE Group object pool and conservative binding ledger tests."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
NATIVE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(NATIVE))
import audit_group_pool_identity_20261017 as a
import group_pool_binding_replay_20261017 as l
def e(seq,op,alias='g1',root='u1'):
 return json.dumps(dict(schema='bsc.n1.pool_binding_event.v1',
    seq=seq,event=op,root_id=root,pool_id='pool1',object_alias=alias))
class GroupPoolIdentity(unittest.TestCase):
 def test_guard_inventory(self):
  self.assertEqual((len(a.pins()),len(a.CALLS),len(a.RECOMPUTE)),(120,21,11))
 def test_group_writer_all_in_one_typed_function(self):
  self.assertTrue(all(0x301dc0c<x<0x301e252 for x in a.RECOMPUTE))
 def test_identity_same_address_recycled(self):
  x=l.analyze([e(1,'checkout'),e(2,'bind'),e(3,'clear'),
    e(4,'return'),e(5,'checkout'),e(6,'bind')])
  self.assertEqual([v['pool_checkout_incarnation'] for v in x['events'] if v['event']=='bind'],[1,2])
 def test_binding_revision_differs_from_lifetime_generation(self):
  x=l.analyze([e(1,'checkout'),e(2,'bind'),e(3,'clear'),e(4,'bind')])
  self.assertEqual(x['events'][-1]['pool_checkout_incarnation'],1)
  self.assertEqual(x['events'][-1]['binding_revision'],3)
 def test_unseen_checkout_remains_unknown(self):
  self.assertTrue(l.analyze([e(1,'bind')])['events'][0]['lifetime_uncertain'])
 def test_return_while_bound_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'RETURN_WHILE_ROOT_BOUND'):
   l.analyze([e(1,'checkout'),e(2,'bind'),e(3,'return')])
 def test_double_checkout_fails(self):
  with self.assertRaisesRegex(ValueError,'DOUBLE_CHECKOUT'):
   l.analyze([e(1,'checkout'),e(2,'checkout')])
 def test_return_without_checkout_fails(self):
  with self.assertRaisesRegex(ValueError,'RETURN_WITHOUT'):
   l.analyze([e(1,'return')])
 def test_raw_address_rejected(self):
  with self.assertRaisesRegex(ValueError,'INVALID_OR_POINTER_ID'):
   l.analyze([e(1,'checkout',alias='0x123456781234')])
 def test_nonmonotonic_order_rejected(self):
  with self.assertRaisesRegex(ValueError,'NON_MONOTONIC_SEQUENCE'):
   l.analyze([e(3,'checkout'),e(1,'clear')])
 def test_no_unobserved_runtime_claim(self):
  self.assertFalse(l.analyze([e(1,'checkout')])['source_is_real_gameplay_verified'])
 def test_constructor_root_group_null_guard(self):
  self.assertEqual(a.pins()[0x3007ce8].hex(),'49899ff8320000')
 def test_pool_pop_and_return_stores_guarded(self):
  d=a.pins()
  self.assertEqual(d[0x301b874].hex(),'488b5f58')
  self.assertEqual(d[0x301b8b0].hex(),'48894f58')
  self.assertEqual(d[0x302c2f5].hex(),'48893b')
 def test_wrong_build_rejected_even_python_optimized(self):
  with tempfile.TemporaryDirectory() as t:
   exe=Path(t)/'fake.exe';exe.write_bytes(b'MZ'+bytes(100))
   for args in ([],['-O']):
    p=subprocess.run([sys.executable,*args,str(Path(a.__file__)),'--exe',str(exe)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0);self.assertIn('SHA_MISMATCH',p.stderr)
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original EXE private, not in GitHub CI')
 def test_private_original_exe(self):
  d=a.audit(os.getenv('WH3_903_EXE'))
  self.assertEqual((d['original_opcode_starts'],d['direct_calls']),(120,21))
  self.assertFalse(d['gameplay_patch_authorized'])
if __name__=='__main__':unittest.main()
