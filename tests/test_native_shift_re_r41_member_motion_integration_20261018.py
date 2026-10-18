#!/usr/bin/env python3
"""CI-safe unit/static regression. No artificial trace is gameplay evidence."""
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'/'native_shift_re'))
import audit_r41_member_motion_integration_20261018 as a

class NativeMemberIntegration(unittest.TestCase):
    def test_14_groups_134_pins(self):
        gs=a.inventory()
        self.assertEqual(len(gs),14)
        self.assertEqual(sum(len(g['pins']) for g in gs.values()),134)

    def test_integrator_direct_calls_are_scoped(self):
        gs=a.inventory()
        self.assertEqual(a.DIRECT_E8[0x030592F8],0x03146FF0)
        self.assertEqual(a.DIRECT_E8[0x031000F6],0x03146FF0)
        self.assertEqual(a.DIRECT_E8[0x0310014C],0x03146FF0)
        self.assertEqual(gs['ordinary_virtual_20']['pins'][0x030592FF].hex(),'e8686d0a00')

    def test_derived_virtual_calls_base(self):
        self.assertEqual(a.MEMBER_VTABLE[0x03AD3360,0x20],0x03058D2C)
        self.assertEqual(a.DIRECT_E8[0x03058D5E],0x030592BC)

    def test_position_xyz_two_groups(self):
        groups=a.POSITION_STORES
        for key in ('direct_xyz','second_xyz'):
            self.assertEqual(set(groups[key].values()),{0x88,0x8c,0x90})

    def test_position_and_vector_sites_same_typed_integrator(self):
        gs=a.inventory()['common_integrator']['pins']
        for group in a.POSITION_STORES.values():
            self.assertTrue(set(group)<=set(gs))

    def test_displacement_delta_updated_in_integrator(self):
        pins=a.inventory()['common_integrator']['pins']
        self.assertEqual(pins[0x03147199].hex(),'f30f118b3c010000')
        self.assertEqual(pins[0x031471A1].hex(),'f30f11a344010000')
        self.assertEqual(pins[0x031472C3].hex(),'f20f11833c010000')
        self.assertEqual(pins[0x031472D1].hex(),'898344010000')
        self.assertTrue(0x03147199<0x031471B5<0x0314720B<0x031472C3)

    def test_packet_changes_bit2_before_integrator_gate(self):
        self.assertEqual(a.inventory()['common_integrator']['pins'][0x031471B5],bytes.fromhex('f6c202'))
        for name,pins in [
            ('packet_simple_position_writer',(0x03164676,0x0316467F)),
            ('packet_complex_position_writer',(0x03164477,0x03164480)),
        ]:
            p=a.inventory()[name]['pins']
            self.assertEqual(p[pins[0]],bytes.fromhex('24f7'))
            self.assertEqual(p[pins[1]],bytes.fromhex('0c02'))

    def test_movement_entry_not_member_primary_tick(self):
        self.assertEqual(a.MEMBER_VTABLE[0x03912950,0x18],0x03086F04)
        self.assertEqual(a.MEMBER_VTABLE[0x03912950,0x20],0x030592BC)

    def test_motion_route_gates(self):
        gs=a.inventory()['ordinary_virtual_20']['pins']
        self.assertEqual(gs[0x030592D6],bytes.fromhex('f6810801000010'))
        self.assertEqual(gs[0x030592E5],bytes.fromhex('4883b9200b000000'))
        self.assertEqual(gs[0x030592EF],bytes.fromhex('83b9280b000004'))

    def test_short_branch_destinations(self):
        p=a.inventory()
        allpins={k:v for g in p.values() for k,v in g['pins'].items()}
        self.assertEqual(len(a.DIRECT_BRANCH),7)
        for site,target in a.DIRECT_BRANCH.items():
            self.assertEqual(a.branch_dest(site,allpins[site]),target)

    def test_all_direct_edges_have_pins(self):
        p=a.inventory()
        allpins={k:v for g in p.values() for k,v in g['pins'].items()}
        for site,target in a.DIRECT_E8.items():
            opcode=allpins[site]
            self.assertEqual(opcode[0],0xE8)
            self.assertEqual(site+5+struct.unpack_from('<i',opcode,1)[0],target)

    def test_root_arrays_not_proved_typed(self):
        g=a.inventory()['unitroot_three_object_arrays']['pins']
        for site in (0x0304C75D,0x0304C788,0x0304C7B3):
            self.assertEqual(g[site],bytes.fromhex('ff5020'))
        # In reality, these are generic vtable calls, not type proof.
        self.assertNotIn((0x0304C72C,0x20),a.MEMBER_VTABLE)

    def test_typed_virtual_same_field_not_all_members(self):
        self.assertEqual(a.MEMBER_VTABLE[0x03912950,0xF0],0x03164710)
        self.assertEqual(a.MEMBER_VTABLE[0x03AD3360,0xF0],0x03164710)
        self.assertNotEqual(a.MEMBER_VTABLE[0x03912950,0x20],a.MEMBER_VTABLE[0x03AD3360,0x20])

    def test_fail_closed_wrong_executable(self):
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'wrong.exe'
            bad.write_bytes(b'MZ'+bytes(256))
            for flags in ([],['-O']):
                result=subprocess.run([sys.executable,*flags,str(a.__file__),'--exe',str(bad)],
                                       text=True,capture_output=True,timeout=10)
                self.assertNotEqual(result.returncode,0)

    def test_refuse_to_overwrite_executable(self):
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)/'game.exe';fake.write_bytes(b'not-a-game')
            result=subprocess.run([sys.executable,str(a.__file__),'--exe',str(fake),'--out',str(fake)],
                                  text=True,capture_output=True,timeout=10)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(fake.read_bytes(),b'not-a-game')

    @unittest.skipUnless(os.getenv('WH3_NEW_EXE'),'private WH3 EXE absent from GitHub CI')
    def test_original_new_exe_static_audit(self):
        got=a.audit(Path(os.environ['WH3_NEW_EXE']))
        self.assertEqual(got['exe_sha256'],a.SHA)
        self.assertEqual((got['verified_instruction_starts'],got['verified_e8_targets'],
                          got['verified_branch_targets'],got['verified_vtable_slots']),
                         (134,14,7,7))
        self.assertEqual(got['verified_all_executable_section_direct_integrator_callers'],3)
        self.assertFalse(got['vanilla_shift_crowding_root_cause_proven'])
        self.assertFalse(got['gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
