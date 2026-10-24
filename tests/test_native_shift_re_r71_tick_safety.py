"""R71 public CI static/synthetic tests. Original game executable intentionally absent."""
import importlib.util,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
A=load('audit_r71_tick_safety')
G=load('r71_observation_gate')
M=json.loads((ROOT/'r71_tick_safety_manifest.json').read_text())
class R71(unittest.TestCase):
 def test_pin_count(self):self.assertEqual(len(M['pins']),32)
 def test_e8_count(self):self.assertEqual(len(M['e8_edges']),4)
 def test_two_complete_instructions(self):
    self.assertEqual(M['pins']['03086f04']+M['pins']['03086f07'],M['stolen_first_two_instructions_bytes'])
 def test_following_instruction(self):self.assertEqual(M['pins']['03086f0b'],'48896818')
 def test_inside_prologue(self):self.assertGreater(M['tick_prolog_length'],7)
 def test_unwind_slots(self):self.assertEqual(M['tick_unwind_slots'],19)
 def test_member_this_alias(self):self.assertEqual(M['pins']['03086f2c'],'488bf9')
 def test_steering_edge(self):self.assertEqual(M['e8_edges']['03087349'],'03059bc8')
 def test_lifetime_gate(self):self.assertIn('member_lifetime',G.Gate().evaluate()['missing'])
 def test_cave_collision_gate(self):self.assertIn('no_hook_collision',G.Gate().evaluate()['missing'])
 def test_even_full_gates_not_authorized(self):
    self.assertFalse(G.Gate(**{k:True for k in G.Gate().__dict__}).evaluate()['live_hook_authorized'])
 def test_wrong_sha_rejected(self):
    with self.assertRaisesRegex(A.AuditError,'FAIL_CLOSED_SHA'):A.check(b'MZ'+bytes(200),M)
 def test_optional_real_exe(self):
    x=os.environ.get('BSC_EXE')
    if not x:self.skipTest('Commercial game EXE not included in public CI')
    self.assertFalse(A.check(Path(x).read_bytes(),M)['hook_authorized'])
