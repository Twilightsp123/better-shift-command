"""BSC exact original WH3 geometry manager proof; static not gameplay patch."""
import os, sys, unittest
from pathlib import Path
from unittest import mock
MODULE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(MODULE))
import audit_shared_move_geometry_manager as a

class SharedMoveGeometryManager(unittest.TestCase):
    def test_group_constructor_stores_native_context_typed(self):
        self.assertEqual(a.PINS[0x030C2C56].hex(),'488b5208')
        self.assertEqual(a.PINS[0x030C2C5A].hex(),'4883c230')
        self.assertEqual(a.PINS[0x030C2D40].hex(),'488b4208')
        self.assertEqual(a.PINS[0x030C2D4E].hex(),'48894110')
        self.assertEqual(a.LEAF_OWNER,(0x030C2D40,0x030C2DC6))

    def test_unit_context_source_has_corroborating_back_reference(self):
        self.assertEqual(a.PINS[0x02DD5B5D].hex(),'488b8f40040000')
        self.assertEqual(a.PINS[0x02DD57CE].hex(),'488b4308')
        self.assertEqual(a.PINS[0x02DD57D2].hex(),'4c8b8840040000')
        self.assertEqual(a.DIRECT_CALLS[0x02DD5B6C],0x02DD579C)

    def test_tick_uses_route_context_manager_160_and_member_uses_same_source(self):
        self.assertEqual(a.PINS[0x02DD58D7].hex(),'488b8b60010000')
        self.assertEqual(a.DIRECT_CALLS[0x02DD58DE],0x03128E80)
        self.assertEqual(a.PINS[0x030D55AD].hex(),'488b4310')
        self.assertEqual(a.PINS[0x030D55C7].hex(),'488b8840040000')
        self.assertEqual(a.PINS[0x030D55DD].hex(),'488b8960010000')
        self.assertEqual(a.PINS[0x030D55E4].hex(),'4883c118')

    def test_big_task_is_manager_owned_but_separate_from_manager(self):
        self.assertEqual(a.PINS[0x0310EE26].hex(),'48899ff0010000')
        self.assertEqual(a.PINS[0x03128EA8].hex(),'488bbbf0010000')
        self.assertEqual(a.DIRECT_CALLS[0x0310EDA7],0x030EE850)
        self.assertEqual(a.DIRECT_CALLS[0x03128F1D],0x0311DE74)
        self.assertEqual(a.PINS[0x0311E580].hex(),'488b9f60010000')

    def test_state_one_projector_is_guarded_not_forced(self):
        self.assertEqual(a.PINS[0x0311DEC0].hex(),'0f84b2060000')
        self.assertEqual(a.PINS[0x0311E63B].hex(),'807f2401')
        self.assertEqual(a.PINS[0x0311E63F].hex(),'0f859b010000')
        self.assertEqual(a.PINS[0x0311E64C].hex(),'48894320')
        self.assertEqual(a.DIRECT_CALLS[0x0311E636],0x0311E80C)

    def test_three_converter_calls_have_same_typed_subobject_offset(self):
        for at in (0x03129092,0x030D55F5,0x03121A99):
            self.assertEqual(a.DIRECT_CALLS[at],0x030FDA9C)
        self.assertEqual(a.PINS[0x0312908E].hex(),'488d4b18')
        self.assertEqual(a.PINS[0x030D55E4].hex(),'4883c118')
        self.assertEqual(a.PINS[0x03121A91].hex(),'488d4f18')

    def test_distinct_conversion_outputs(self):
        self.assertEqual(a.PINS[0x03129097].hex(),'48894770')
        self.assertEqual(a.PINS[0x03121A9E].hex(),'48894370')
        self.assertEqual(a.DIRECT_CALLS[0x030D5603],0x030D5490)

    def test_conversion_may_update_shared_manager_bookkeeping(self):
        self.assertEqual(0x18+0x1d0,0x1e8)
        self.assertEqual(a.PINS[0x030FDAC0].hex(),'488bf1')
        self.assertEqual(a.PINS[0x030FDEB0].hex(),'8986d0010000')
        self.assertEqual(a.PINS[0x030FE095].hex(),'8986d0010000')

    def test_aliased_source_expression_only_same_unitroot_snapshot(self):
        graph=a.native_source_names('R')
        self.assertEqual(graph['group_fanout_first_converter_argument'],graph['manager_task_node_converter_first_argument'])
        self.assertEqual(graph['group_fanout_first_converter_argument'],graph['original_route_node_converter_first_argument'])
        self.assertNotEqual(graph['group_fanout_first_converter_argument'],graph['manager_tick_first_argument'])
        self.assertFalse(graph['queued_big_task_plus_160_alias_proven'])

    def test_aba_synthetic_address_is_not_generation_proof(self):
        old={'address':0x2000,'generation':12}
        new={'address':0x2000,'generation':13}
        self.assertEqual(old['address'],new['address'])
        self.assertNotEqual(old['generation'],new['generation'])

    def test_twelve_decoded_edges_pinned(self):
        self.assertEqual(len(a.DIRECT_CALLS),12)
        self.assertEqual(len(a.CHECKED_VTABLE),2)
        self.assertEqual(len(a.PINS),81)

    def test_wrong_exe_refused_without_reads(self):
        class Fake:
            sha='wrong'
            closed=False
            def close(self):self.closed=True
        fake=Fake()
        with mock.patch.object(a,'StrictPE',return_value=fake):
            with self.assertRaisesRegex(ValueError,'EXE_SHA256_MISMATCH'):
                a.audit(Path('wrong.exe'))
        self.assertTrue(fake.closed)

    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Private exact original WH3 EXE not in public CI')
    def test_private_exact_original_exe(self):
        evidence=a.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual((evidence['opcode_and_instruction_starts'],evidence['verified_E8_edges'],evidence['verified_typed_vtable_entries']),(81,12,2))
        self.assertFalse(evidence['native_patch_authorized'])
        self.assertFalse(evidence['same_manager_instance_in_a_particular_SHIFT_battle_confirmed'])

if __name__=='__main__':unittest.main()
