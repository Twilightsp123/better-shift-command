"""CI-safe native packet-state negative edge and offline first-difference replay."""
import json,os,sys,tempfile,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(ROOT))
import audit_packet_state_entry_gap_20261016 as a
import causal_first_difference_20261016 as d

def event(i=0,**overrides):
 r=dict(schema=d.SCHEMA,trace_id='example_1',unit_epoch='unitA',
  move_epoch='move2',group_epoch='group1',packet_route_epoch='route1',
  frame_epoch='frame1',tick=5,member_index=i,
  flags108=2,state324=0,b20_null=True,
  member_position=[float(i),0,0],world_target=[10,0,0],
  output_velocity=[1,0,0])
 r.update(overrides);return json.dumps(r)

class TypedGapAndReplay(unittest.TestCase):
 def test_fixed_static_pin_inventory(self):
  self.assertEqual((len(a.PINS),len(a.MEMBER_SLOT_METHODS)),(17,6))
 def test_packet_is_member_virtual_368(self):
  self.assertEqual(a.MEMBER_SLOT_METHODS[0x368],0x0306B9F0)
 def test_state_entry_slots_are_different(self):
  self.assertEqual(a.MEMBER_SLOT_METHODS[0x128],0x0307FB0C)
  self.assertEqual(a.MEMBER_SLOT_METHODS[0x538],0x0306A100)
 def test_indirect_calls_cannot_be_claimed_to_be_resolved(self):
  self.assertEqual(a.PINS[0x0306BB0E],'41ff9300010000')
  self.assertEqual(a.PINS[0x0306BB44],'41ff93e8000000')
 def test_clean_cohort(self):
  r=d.analyze([event(),event(1)])
  self.assertEqual(r['paired_adjacent_members'],1)
  self.assertIsNone(r['pairs'][0]['earliest_recorded_difference'])
  self.assertFalse(r['root_cause_proven'])
 def test_packet_generation_is_earlier_than_tick_state(self):
  r=d.analyze([event(),event(1,packet_route_epoch='route2',flags108=4,state324=4)])
  self.assertEqual(r['pairs'][0]['earliest_recorded_difference'],'packet_route_epoch')
 def test_frame_difference_precedes_state_difference(self):
  r=d.analyze([event(),event(1,frame_epoch='frame2',flags108=4,state324=4)])
  self.assertEqual(r['pairs'][0]['earliest_recorded_difference'],'frame_epoch')
 def test_state_branch_uses_verified_bit_gates(self):
  self.assertEqual(d.tick_branch(12,4,True),'other_virtual_0x498')
  self.assertEqual(d.tick_branch(6,0,True),'other_state')
  self.assertEqual(d.tick_branch(2,0,True),'neighbor')
 def test_motion_opposition_not_called_cause(self):
  r=d.analyze([event(),event(1,output_velocity=[-1,0,0])])
  self.assertEqual(r['pairs'][0]['earliest_recorded_difference'],'motion_direction')
  self.assertFalse(r['pairs'][0]['root_cause_proven'])
 def test_insufficient_other_tick(self):
  self.assertEqual(d.analyze([event(),event(1,tick=6)])['paired_adjacent_members'],0)
 def test_missing_output_is_unknown(self):
  r=d.analyze([event(output_velocity=None),event(1,output_velocity=None)])
  self.assertIn('motion_direction',r['pairs'][0]['not_observed_stages'])
 def test_reject_raw_addresses(self):
  with self.assertRaises(ValueError):
   d.analyze([event(unit_epoch='0x7ffe12345678')])
 def test_reject_duplicate_member(self):
  with self.assertRaises(ValueError):d.analyze([event(),event()])
 def test_reject_infinite_geometry(self):
  with self.assertRaises(ValueError):d.analyze([event(world_target=[float('inf'),0,0])])
 def test_reject_wrong_executable_even_python_optimized(self):
  with tempfile.TemporaryDirectory() as folder:
   bad=Path(folder)/'wrong.exe';bad.write_bytes(b'MZ'+bytes(99))
   for options in ([],['-O']):
    p=subprocess.run([sys.executable,*options,str(Path(a.__file__)),'--exe',str(bad)],capture_output=True,text=True)
    self.assertNotEqual(p.returncode,0)
    self.assertIn('SHA_MISMATCH',p.stderr)
 def test_protect_original_game_binary(self):
  with tempfile.TemporaryDirectory() as folder:
   bad=Path(folder)/'game.exe';bad.write_bytes(b'unmodified')
   p=subprocess.run([sys.executable,str(Path(a.__file__)),'--exe',str(bad),'--out',str(bad)],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertEqual(bad.read_bytes(),b'unmodified')
 @unittest.skipUnless(os.getenv('WH3_903_EXE'),'private original EXE excluded from GitHub CI')
 def test_exact_original_exe(self):
  r=a.audit(os.environ['WH3_903_EXE'])
  self.assertEqual((r['original_instruction_starts'],r['typed_member_slots'],r['packet_receiver_calls']),(17,6,13))
  self.assertFalse(r['indirect_state_change_excluded'])
if __name__=='__main__':unittest.main()
