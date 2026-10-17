"""R36 deterministic tests. Binary-only proof requires locally supplied new EXE."""
import os
import sys
import struct
import tempfile
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'maintenance_tools'/'native_shift_re'))
import audit_r36_b_subtypes_20261017 as a


class R36BSubtypeTest(unittest.TestCase):
    def test_inventory_and_unwind_groups(self):
        gs=a.read_pins()
        self.assertEqual((len(gs),sum(len(pin) for (_,pin) in gs.values())),(15,128))
        self.assertEqual(len({at for _,pins in gs.values() for at in pins}),128)

    def test_3_distinct_constructor_vtable_pairs(self):
        self.assertEqual(len(a.VTABLES),3)
        self.assertEqual({t for t,_,_,_ in a.VTABLES.values()},
                         {0x03AE5820,0x03AE5800,0x03AE57E0})
        self.assertEqual({v for _,v,_,_ in a.VTABLES.values()},
                         {0x03286288,0x032863A0,0x03286480})

    def test_distinct_constructors_are_not_member_fanout(self):
        self.assertEqual(a.CALLS[0x0327ED3C],0x03268920)
        self.assertEqual(a.CALLS[0x0327EDD5],0x03268D34)
        self.assertEqual(a.CALLS[0x0327EE65],0x03268E3C)

    def test_all_B_paths_clear_shared_slot_before_constructing(self):
        p=a.read_pins()
        self.assertEqual(a.CALLS[0x0327ED28],0x02F3F0FC)
        self.assertEqual(a.CALLS[0x0327EDBA],0x02F3F0FC)
        self.assertEqual(a.CALLS[0x0327EE51],0x02F3F0FC)
        self.assertIn(0x0327ED1E,p['dispatch_B1'][1])
        self.assertIn(0x0327EDB3,p['dispatch_B2'][1])
        self.assertIn(0x0327EE47,p['dispatch_B3'][1])

    def test_shorttask_bigTask_state_gate(self):
        p=a.read_pins()['shorttask_callback'][1]
        self.assertEqual(p[0x02F5B2DF].hex(),'83782004')
        self.assertEqual(a.JUMPS[0x02F5B2F2],0x02F5B463)
        self.assertEqual(a.CALLS[0x02F5B475],0x02F54510)
        self.assertEqual(a.CALLS[0x02F54527],0x02F55FE0)
        self.assertEqual(a.CALLS[0x02F54628],0x0327ED4C)

    def test_B1_updates_route_B2_dispatches_members_B3_prepares(self):
        self.assertEqual(a.CALLS[0x032862A6],0x032862C4)
        self.assertEqual(a.CALLS[0x03286445],0x0326A994)
        self.assertEqual(a.CALLS[0x03286572],0x0326B0C8)
        self.assertNotIn(0x0326A994, [dst for src,dst in a.CALLS.items()
                                          if src in (0x032862A6,0x03286346,0x0328637B,0x0328638A)])

    def test_B2_current_member_sender(self):
        p=a.read_pins()
        self.assertEqual(p['fanout_B2'][1][0x0326ABAF].hex(),'ff9068030000')
        self.assertEqual(a.JUMPS[0x032863B7],0x0328645E)

    def test_guarded_object_reset_is_not_generation_barrier(self):
        p=a.read_pins()['slot_cleanup'][1]
        self.assertEqual(p[0x02F3F10A].hex(),'389118010000')
        self.assertEqual(p[0x02F3F11B].hex(),'ff10')
        self.assertEqual(p[0x02F3F11D].hex(),'c6831801000000')

    def test_branch_decoder_positive_and_negative(self):
        pins={at:v for _,group in a.read_pins().values() for at,v in group.items()}
        for site,expected in a.JUMPS.items():
            self.assertEqual(a.branch_dest(site,pins[site]),expected)
        with self.assertRaisesRegex(ValueError,'INVALID_BRANCH_SITE'):
            a.branch_dest(0x400,bytes.fromhex('9090'))

    def test_bad_exe_rejected_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            fake=Path(d)/'game.exe';fake.write_bytes(b'MZ'+bytes(90))
            tool=Path(a.__file__)
            cp=subprocess.run([sys.executable,str(tool),'--exe',str(fake),'--out',str(fake)],
                              capture_output=True,text=True)
            self.assertNotEqual(cp.returncode,0)
            self.assertEqual(fake.read_bytes(),b'MZ'+bytes(90))
            rejected=subprocess.run([sys.executable,str(tool),'--exe',str(fake)],
                                  capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0)

    def test_true_private_exe(self):
        exe=os.getenv('BSC_NEW_EXE')
        if not exe or not Path(exe).is_file():self.skipTest('WH3 EXE absent from CI')
        r=a.audit(Path(exe))
        self.assertEqual(r['sha256'],a.SHA)
        self.assertEqual(r['verified_opcode_starts'],128)
        self.assertEqual((r['verified_E8'],r['verified_jumps'],r['verified_B_vtable_method_slots']),(17,7,3))
        self.assertFalse(r['group_generation_mismatch_proven'])
        self.assertFalse(r['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
