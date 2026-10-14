"""BSC shortTask scheduler static contract; strict original EXE optional."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULES = Path(__file__).resolve().parents[1] / 'maintenance_tools' / 'native_shift_re'
if not (MODULES / 'audit_move_shorttask_resume_gate.py').exists():
    MODULES = Path(__file__).resolve().parent  # standalone private audit workspace
sys.path.insert(0,str(MODULES))
import audit_move_shorttask_resume_gate as a

class ShortTaskScheduler(unittest.TestCase):
    def test_root_manager_pointer_provenance_pins(self):
        self.assertEqual(a.PINS[0x03007AD1].hex(),'498d87a02f0000')
        self.assertEqual(a.PINS[0x03007B62].hex(),'49898780020000')
        self.assertEqual(a.PINS[0x02F50460].hex(),'488b4308')
        self.assertEqual(a.PINS[0x02F50493].hex(),'48894110')

    def test_move_wrapper_constructor_copies_manager(self):
        self.assertEqual(a.DIRECT_CALLS[0x030326E4],0x030090BC)
        self.assertEqual(a.DIRECT_CALLS[0x030090CC],0x03008814)
        self.assertEqual(a.PINS[0x0300884D].hex(),'488b4210')
        self.assertEqual(a.PINS[0x03008851].hex(),'48894118')

    def test_new_task_registered_in_root_manager(self):
        self.assertEqual(a.PINS[0x03026084].hex(),'488b5318')
        self.assertEqual(a.DIRECT_CALLS[0x03026091],0x02F2FFB0)
        self.assertEqual(a.PINS[0x02F2FFDF].hex(),'898240020000')
        self.assertEqual(a.PINS[0x02F2FFEB].hex(),'f30f7f84c2000200')
        self.assertEqual(a.DIRECT_CALLS[0x030260AF],0x02F2C734)

    def test_scheduled_top_and_non_top_use_distinct_virtuals(self):
        self.assertEqual(a.PINS[0x03043579].hex(),'3bf8')
        self.assertEqual(a.BRANCHES[0x0304357B],(0x75,0x0304359E))
        self.assertEqual(a.PINS[0x0304357D].hex(),'ff5210')
        self.assertEqual(a.PINS[0x0304359E].hex(),'ff5218')
        self.assertEqual(a.VTABLES[0x03ABBE18+0x10],0x02F561E8)
        self.assertEqual(a.VTABLES[0x03ABBE18+0x18],0x008D3280)

    def test_unit_tick_moves_queue_before_manager(self):
        self.assertLess(0x03043770,0x0304377C)
        self.assertEqual(a.DIRECT_CALLS[0x03043770],0x0304433C)
        self.assertEqual(a.DIRECT_CALLS[0x0304377C],0x03043520)
        self.assertEqual(a.PINS[0x03043775].hex(),'488d8ba02f0000')

    def test_completed_top_can_be_popped(self):
        self.assertEqual(a.PINS[0x03043583].hex(),'807e1801')
        self.assertEqual(a.DIRECT_CALLS[0x0304358E],0x02F4FD5C)
        self.assertEqual(a.PINS[0x02F4FDC4].hex(),'ff8b40020000')

    def test_short_task_A0_is_rearmable_not_permanent(self):
        self.assertEqual(a.PINS[0x02F56223].hex(),'40387025')
        self.assertEqual(a.PINS[0x02F5622D].hex(),'4088b1a0000000')
        self.assertEqual(a.PINS[0x02F562C0].hex(),'4038b3a0000000')
        self.assertEqual(a.BRANCHES[0x02F562C7],(0x0F85,0x02F564C4))
        self.assertEqual(a.PINS[0x02F562FF].hex(),'c683a000000001')

    def test_plus74_selects_constructor_not_send_eligibility(self):
        self.assertEqual(a.PINS[0x02F5630C].hex(),'40387374')
        self.assertEqual(a.BRANCHES[0x02F56310],(0x0F84,0x02F5640E))
        self.assertEqual(a.DIRECT_CALLS[0x02F56358],0x03263D68)
        self.assertEqual(a.DIRECT_CALLS[0x02F56431],0x03263E7C)
        self.assertEqual(a.DIRECT_CALLS[0x02F56460],0x03263C4C)
        self.assertEqual(a.BRANCHES[0x02F56465],(0xeb,0x02F563F4))
        self.assertEqual(a.DIRECT_CALLS[0x02F56404],0x03279E40)

    def test_late_root_group_pointer_not_capture_at_ctor(self):
        self.assertEqual(a.PINS[0x02F563F4].hex(),'488b4b08')
        self.assertEqual(a.PINS[0x02F563FD].hex(),'488b89f8320000')
        self.assertEqual(a.DIRECT_CALLS[0x02F56282],0x030CFAC4)

    def test_synthetic_new_on_top_blocks_old_dispatch(self):
        r=a.simulate_manager(old_ready=True,old_already_dispatched=False,
             new_done=False,shared_change_rearms=False)
        self.assertFalse(r['stale_packet_possible_under_given_assumptions'])

    def test_synthetic_old_reexposed_is_conditional(self):
        choices={(previous,rearm,ready):a.simulate_manager(
          old_ready=ready,old_already_dispatched=previous,
          new_done=True,shared_change_rearms=rearm)
          ['stale_packet_possible_under_given_assumptions']
          for previous in (False,True) for rearm in (False,True) for ready in (False,True)}
        self.assertFalse(choices[(True,False,True)])
        self.assertTrue(choices[(False,False,True)])
        self.assertTrue(choices[(True,True,True)])
        self.assertTrue(all(not v for (p,r,ready),v in choices.items() if not ready))

    def test_invalid_original_fails_closed_without_writes(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'bad.exe';payload=b'MZ_but_not_903';fake.write_bytes(payload)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                a.audit(fake)
            self.assertEqual(fake.read_bytes(),payload)

    @unittest.skipUnless(os.environ.get('WH3_903_EXE'),'Original EXE is private; public CI does not include it')
    def test_true_exact_original_exe(self):
        r=a.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual((r['opcode_and_disassembly_starts'],r['direct_E8_edges'],
                          r['verified_branches'],r['typed_vtable_slots']),(69,13,5,4))
        self.assertFalse(r['old_task_immediate_update_when_nonlast'])
        self.assertTrue(r['shortTask_A0_guard_can_be_rearmed_on_associated_plus25'])
        self.assertFalse(r['native_patch_authorized'])

if __name__=='__main__':unittest.main()
