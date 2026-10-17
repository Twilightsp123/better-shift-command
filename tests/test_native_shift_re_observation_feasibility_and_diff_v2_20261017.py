"""CI-safe BSC Round29 original-EXE site contracts and conservative replay."""
import json,os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_readonly_observation_sites_20261017 as a
import causal_first_difference_v2_20261017 as d

def ev(i=0,**changes):
 x=dict(schema=d.SCHEMA,trace_id='trial_a',unit_epoch='unit_a',
 move_epoch='move_a',snapshot_id='window_a',group_epoch='group_a',
 packet_route_epoch='route_a',frame_epoch='frame_a',phase='world_goal_resolved',
 tick=18,sample_seq=i+1,sample_time_ns=1000000+10000*i,
 member_index=i,flags108=2,state324=0,b20_null=True,
 position_xyz=[i,0,0],world_goal_xyz=[10,0,0],velocity_xyz=[1,0,0])
 x.update(changes);return json.dumps(x)
def replay(*rows):return d.analyze(rows)['pairs']

class FirstRecordedDiffV2(unittest.TestCase):
 def test_static_site_inventory(self):
  self.assertEqual((len(a.PINS),len(a.CALLS)),(21,3))
 def test_generic_resolver_has_no_member_arg(self):
  self.assertEqual(a.SITES['world_goal_after_call']['member'],'RDI')
  self.assertNotIn('member',a.SITES.get('generic_resolver',{}))
 def test_near_time_not_atomic(self):
  x=replay(ev(),ev(1))[0];self.assertFalse(x['actual_atomic_snapshot_proven'])
  self.assertEqual(x['status'],'NEAR_IN_TIME_CANDIDATES_ONLY_NOT_ATOMIC')
 def test_different_phase_not_comparable(self):
  self.assertEqual(replay(ev(),ev(1,phase='post_member_tick'))[0]['status'],'NOT_COMPARABLE_PHASE_MISMATCH')
 def test_large_skew_not_comparable(self):
  self.assertEqual(replay(ev(),ev(1,sample_time_ns=1400000))[0]['status'],'NOT_COMPARABLE_SEQUENTIAL_SKEW')
 def test_duplicate_sequence_not_comparable(self):
  self.assertEqual(replay(ev(),ev(1,sample_seq=1))[0]['status'],'NOT_COMPARABLE_DUPLICATE_SAMPLE_SEQUENCE')
 def test_missing_earlier_epoch_blocks_first(self):
  x=replay(ev(group_epoch=None),ev(1,group_epoch=None,frame_epoch='frame_b'))[0]
  self.assertFalse(x['earliest_stage_is_unambiguous'])
  self.assertIn('group_epoch',x['earlier_unobserved_stages'])
 def test_known_packet_epoch_first_candidate(self):
  x=replay(ev(),ev(1,packet_route_epoch='route_b'))[0]
  self.assertEqual(x['earliest_ordered_recorded_stage'],'packet_route_epoch')
  self.assertTrue(x['earliest_stage_is_unambiguous'])
  self.assertFalse(x['stage_order_is_causal_or_temporal_proof'])
 def test_opposite_movement_not_proven_cause(self):
  x=replay(ev(),ev(1,velocity_xyz=[-1,0,0]))[0]
  self.assertFalse(x['root_cause_proven'])
 def test_index_adjacency_not_spatial_proof(self):
  self.assertFalse(replay(ev(),ev(1))[0]['index_adjacency_is_spatial_adjacency_proof'])
 def test_different_move_not_paired(self):
  self.assertEqual(replay(ev(),ev(1,move_epoch='move_b')),[])
 def test_missing_velocity_recorded(self):
  x=replay(ev(velocity_xyz=None),ev(1,velocity_xyz=None))[0]
  self.assertIn('motion_direction',x['unobserved_stages'])
 def test_raw_pointer_rejected(self):
  with self.assertRaises(ValueError):replay(ev(unit_epoch='0x7ffdf0011220'))
 def test_nonfinite_rejected(self):
  with self.assertRaises(ValueError):replay(ev(velocity_xyz=[float('inf'),0,0]))
 def test_duplicate_member_rejected(self):
  with self.assertRaises(ValueError):replay(ev(),ev())
 def test_flag_gate_priority(self):
  self.assertEqual(d.tick_branch(12,4,True),'virtual_498')
  self.assertEqual(d.tick_branch(6,0,True),'other_state')
 def test_wrong_build_fails_even_optimized(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'wrong.exe';path.write_bytes(b'MZ'+bytes(99))
   for opts in ([],['-O']):
    p=subprocess.run([sys.executable,*opts,str(Path(a.__file__)),'--exe',str(path)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0);self.assertIn('SHA_MISMATCH',p.stderr)
 def test_game_exe_protected(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'game.exe';path.write_bytes(b'original')
   p=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(path),'--out',str(path)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0);self.assertIn('EXE_OVERWRITE_FORBIDDEN',p.stderr)
   self.assertEqual(path.read_bytes(),b'original')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original game EXE is never uploaded to CI')
 def test_actual_original_exe(self):
  r=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['guarded_opcodes'],r['verified_direct_calls']),(21,3))
  self.assertFalse(r['collection_ready'])
if __name__=='__main__':unittest.main()
