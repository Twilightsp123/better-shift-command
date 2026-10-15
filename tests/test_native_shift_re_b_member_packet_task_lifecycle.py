"""Bounded synthetic contracts + opt-in private exact-EXE SHA validation."""
import os, subprocess, sys, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/'audit_b_member_packet_task_lifecycle.py'
if not SRC.is_file():
    SRC=HERE.parent/'maintenance_tools'/'native_shift_re'/'audit_b_member_packet_task_lifecycle.py'
sys.path.insert(0,str(SRC.parent))
import audit_b_member_packet_task_lifecycle as m


class NativeBTaskLifecycle(unittest.TestCase):
    def test_unique_packet_modes_from_actual_b_caller_inputs(self):
        self.assertEqual(m.ordinary_b_flag(0,0),0x0E)
        self.assertEqual(m.ordinary_b_flag(0,1),0x07)
        self.assertEqual(m.ordinary_b_flag(1,0),0x07)
        self.assertEqual(m.ordinary_b_flag(1,1),0x07)

    def test_b_packet_kinds_both_omit_0x20(self):
        self.assertEqual({m.ordinary_b_flag(a,b) for a in (0,1) for b in (0,1)}, {0x07,0x0e})
        self.assertTrue(all((v & 0x20)==0 for v in (0x07,0x0E)))
        self.assertEqual(0x26&0x20,0x20)

    def test_receiver_needs_both_mode_zero_and_no_0x20(self):
        self.assertTrue(m.receiver_uses_inline_slot(0,0x07))
        self.assertTrue(m.receiver_uses_inline_slot(0,0x0e))
        self.assertFalse(m.receiver_uses_inline_slot(1,0x07))
        self.assertFalse(m.receiver_uses_inline_slot(0,0x26))
        self.assertFalse(m.receiver_uses_inline_slot(2,0x26))

    def test_unsigned_time_gate_counterexamples(self):
        self.assertTrue(m.time_gate_open(100,100))
        self.assertFalse(m.time_gate_open(99,100))
        self.assertTrue(m.time_gate_open(101,100))
        # This is a single unsigned compare, not a modulo-wrap-aware timer implementation.
        self.assertFalse(m.time_gate_open(1,0xffffffff))

    def test_holder_member_offset_identity(self):
        self.assertEqual(0x490+0x130,0x5c0)
        self.assertEqual(0x4a8+0x40,0x4e8)
        self.assertEqual(0x4a8+0x90,0x538)
        self.assertEqual(0x328+0x154,0x47c)

    def test_task_update_and_member_action_are_distinct_vtables(self):
        self.assertEqual(m.VTABLE[(0x03905E18,0x10)],0x02F83B24)
        self.assertEqual(m.VTABLE[(0x0390D4F8,0x568)],0x0306A8FC)
        self.assertEqual(m.VTABLE[(0x0390D4F8,0x580)],0x0306A990)
        self.assertEqual(m.VTABLE[(0x0390D4F8,0x5b0)],0x0306AD00)
        self.assertEqual(m.PINS[0x0308234D],'ff9080000000')

    def test_exact_static_edge_inventory(self):
        self.assertEqual(len(m.PINS),72)
        self.assertEqual(len(m.E8),23)
        self.assertEqual(len(m.VTABLE),7)
        self.assertEqual(m.E8[0x0326A423],0x02F5F8DC)
        self.assertEqual(m.E8[0x0326A466],0x02F5F8DC)
        self.assertEqual(m.E8[0x0306BA5B],0x02F5F7C8)
        self.assertEqual(m.E8[0x02ECA999],0x02F5F7C8)
        self.assertEqual(m.E8[0x02F448FC],0x02F5F7C8)

    def test_guard_not_python_assert_optimized_away(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'wrong.exe';fake.write_bytes(b'MZ'+bytes(128))
            path=Path(m.__file__)
            for opts in ([],['-O']):
                p=subprocess.run([sys.executable,*opts,str(path),'--exe',str(fake)],capture_output=True,text=True)
                self.assertNotEqual(p.returncode,0)
                self.assertIn('SHA_MISMATCH',p.stderr)

    def test_output_cannot_overwrite_exe(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'game.exe';path.write_bytes(b'unchanged')
            p=subprocess.run([sys.executable,str(Path(m.__file__)),'--exe',str(path),'--out',str(path)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('EXE_OVERWRITE_FORBIDDEN',p.stderr)
            self.assertEqual(path.read_bytes(),b'unchanged')

    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'original EXE not in public GitHub CI')
    def test_private_exact_exe_audit(self):
        result=m.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual(result['verified_instruction_starts'],72)
        self.assertEqual(result['verified_direct_calls'],23)
        self.assertEqual(result['verified_typed_vtable_slots'],7)
        self.assertFalse(result['runtime_shift_branch_observed'])
        self.assertFalse(result['native_patch_authorized'])

if __name__=='__main__':unittest.main()
