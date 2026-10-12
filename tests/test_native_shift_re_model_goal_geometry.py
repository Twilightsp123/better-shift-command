"""Native goal lookahead chord crossing does not imply WH3 collision."""
import math,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'))
import audit_model_goal_segment_geometry as a

def e(member,x,z,gx,gz,tick=548,group='g'):
 return {'ev':'MOTOR_GOAL_REVERSAL','group':group,'groupTick':tick,
         'member':member,'x':x,'z':z,
         'newGoal24':struct.pack('<6f',gx,0,gz,0,0,0).hex()}

class MemberGoalGeometryContract(unittest.TestCase):
 def test_crossing_is_only_geometric_chord_not_collision(self):
  report=a.audit([e('a',0,0,10,10),e('b',0,10,10,0)])
  x=report['simultaneous_reversal_ticks'][0]
  self.assertEqual(x['lookahead_straight_segment_crossings'],1)
  self.assertEqual(x['crossing_fraction_samples'][0]['fraction_along_first_lookahead'],.5)
  self.assertFalse(x['real_movement_trajectory_crossing_proven'])
  self.assertFalse(report['physical_collision_cause_proven'])
 def test_non_crossover_same_destination_direction(self):
  report=a.audit([e('a',0,0,10,0),e('b',0,1,10,1)])
  self.assertEqual(report['simultaneous_reversal_ticks'][0]['lookahead_straight_segment_crossings'],0)
 def test_distinct_group_and_tick_cannot_be_joined(self):
  report=a.audit([e('a',0,0,10,10,group='a'),e('b',0,10,10,0,group='b')])
  self.assertEqual(sum(x['lookahead_straight_segment_crossings'] for x in report['simultaneous_reversal_ticks']),0)
 def test_sampled_center_min_does_not_prove_collision(self):
  positions=[{'ev':'GROUP_TICK_POSITION','group':'g','turnStartTick':658,
    'groupTick':t,'member':m,'x':x,'z':0.}
    for t,d in [(659,1.1241),(660,.608719),(661,.973)]
    for m,x in [('a',0.),('b',d)]]
  report=a.audit(positions)
  x=report['closest_sampled_member_center']
  self.assertEqual(x['tick'],660)
  self.assertAlmostEqual(x['min_horizontal_center_distance'],.608719)
  self.assertFalse(x['collision_proven'])
 def test_bad_goal_hex_is_not_crash(self):
  report=a.audit([{'ev':'MOTOR_GOAL_REVERSAL','group':'g','groupTick':4,
    'x':0,'z':0,'member':'a','newGoal24':'INVALID'}])
  self.assertEqual(report['simultaneous_reversal_ticks'],[])

if __name__=='__main__':unittest.main()
