"""WH3 9.0.3 type-checked B-family route-node identity, NO GAME PATCH.

Only original private executable test decodes actual WH3 bytes; synthetic
fixtures check branch logic and intentional negative conclusions.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(TOOLS))
import audit_typed_task_route_node_bridge as a

class TypedTaskRouteNode(unittest.TestCase):
    def test_adjacent_vtables_are_not_the_same_type(self):
        self.assertEqual(a.INSTALLED_TABLES[0x03263ED5],0x03AE00E8)
        self.assertEqual(a.INSTALLED_TABLES[0x03263FE4],0x03AE0108)
        self.assertEqual(a.INSTALLED_TABLES[0x03263ACF],0x03AE0128)
        self.assertEqual(a.TYPED_METHODS[0x03AE0128+0x10],0x03281408)
        self.assertEqual(0x03AE0128+0x10,0x03AE00E8+0x50)
        # Numerical equality of pointer-cell RVA does NOT unify vtable identity.
        self.assertNotEqual(0x03AE00E8,0x03AE0128)

    def test_mode_selector_to_B_task_constructor_is_typed(self):
        self.assertEqual(a.E8[0x02F56404],0x03279E40)
        self.assertEqual(a.E8[0x03279E62],0x02DC2E04)
        self.assertEqual(a.JCC[0x03279E69],(b'\x74',0x03279EBA))
        self.assertEqual(a.E8[0x03279ED8],0x03263AB0)
        self.assertEqual(a.PINS[0x03263AEE],bytes.fromhex('48894750'))
        self.assertEqual(a.PINS[0x03263AF6],bytes.fromhex('48894758'))

    def test_same_dispatch_B_task_does_not_also_issue_A_fanout(self):
        self.assertEqual(a.JCC[0x03279E69],(b'\x74',0x03279EBA))
        self.assertEqual(a.E8[0x03279EB3],0x030D554C)
        self.assertEqual(a.EXCLUSIVE_JUMP[0x03279EB8],0x03279EDD)
        self.assertEqual(a.E8[0x03279ED8],0x03263AB0)
        self.assertEqual(a.PINS[0x03279EB8],bytes.fromhex('eb23'))

    def test_short_task_flag74_two_distinct_abi_constructors(self):
        self.assertEqual(a.PINS[0x02F5630C],bytes.fromhex('40387374'))
        self.assertEqual(a.JCC[0x02F56310][1],0x02F5640E)
        self.assertEqual(a.E8[0x02F56358],0x03263D68)
        self.assertEqual(a.E8[0x02F56431],0x03263E7C)
        self.assertEqual(a.E8[0x03263EB4],0x03263D68)
        self.assertEqual(a.PINS[0x02F56353],bytes.fromhex('4889742420'))
        self.assertEqual(a.PINS[0x03263EAC],bytes.fromhex('4c894c2420'))
        self.assertEqual(a.PINS[0x03263D6C],bytes.fromhex('4c8b542428'))
        self.assertEqual(a.PINS[0x03263D87],bytes.fromhex('4c895120'))
        # Windows x64 fifth argument: wrapper [rsp+20] -> leaf [rsp+28].

    def test_B_task_aux_pointer_is_descriptor_plus_8(self):
        self.assertEqual(a.PINS[0x02F563EB],bytes.fromhex('4c895c2458'))
        self.assertEqual(a.PINS[0x03279ED2],bytes.fromhex('4c8bc3'))
        self.assertEqual(a.PINS[0x03263AF2],bytes.fromhex('498b4308'))
        self.assertEqual(a.PINS[0x03263AF6],bytes.fromhex('48894758'))
        self.assertEqual(a.PINS[0x03281411],bytes.fromhex('488b4958'))

    def test_current_route_preserved_before_new_creation(self):
        self.assertEqual(a.PINS[0x03281497],bytes.fromhex('48837b5800'))
        self.assertEqual(a.PINS[0x0328149E],bytes.fromhex('488b4320'))
        self.assertEqual(a.PINS[0x032814A7],bytes.fromhex('4883b85801000000'))
        self.assertEqual(a.JCC[0x032814AF][1],0x03281517)

    def test_two_different_node_builders(self):
        self.assertEqual(a.E8[0x032814FB],0x03121ABC)
        self.assertEqual(a.E8[0x0328150A],0x031219B0)
        self.assertEqual(a.JCC[0x032814F9][1],0x0328150A)
        self.assertEqual(a.PINS[0x032814E4],bytes.fromhex('4c8b4320'))
        self.assertEqual(a.PINS[0x032814EF],bytes.fromhex('488b8860010000'))

    def test_task_aware_node_constructor_has_distinct_descriptor_and_task_arguments(self):
        self.assertEqual(a.PINS[0x03121B36],bytes.fromhex('4889742428'))
        self.assertEqual(a.PINS[0x03121B3B],bytes.fromhex('48896c2420'))
        self.assertEqual(a.E8[0x03121B40],0x030ECB10)
        self.assertEqual(a.PINS[0x030ECB1B],bytes.fromhex('488b542470'))
        self.assertEqual(a.PINS[0x030ECB41],bytes.fromhex('488b4c2478'))
        self.assertEqual(a.PINS[0x030ECB66],bytes.fromhex('488b9158010000'))
        self.assertEqual(a.E8[0x030ECB98],0x030FE1E4)
        self.assertEqual(a.PINS[0x030ECBA2],bytes.fromhex('48894370'))

    def test_generic_copy_does_not_imply_task_alias(self):
        self.assertEqual(a.E8[0x03121A40],0x030EC9EC)
        self.assertEqual(a.E8[0x030ECB3C],0x030EC9EC)
        self.assertEqual(a.PINS[0x030ECB38],bytes.fromhex('4883c120'))
        self.assertEqual(a.E8[0x03121A99],0x030FDA9C)
        self.assertEqual(a.PINS[0x03121A95],bytes.fromhex('488d5320'))

    def test_task_aware_input_old_subtask_is_walked_not_deleted(self):
        self.assertEqual(a.E8[0x030FE272],0x030C1FDC)
        self.assertEqual(a.E8[0x030FE287],0x030C7858)
        self.assertEqual(a.PINS[0x030FE280],bytes.fromhex('488d5318'))
        self.assertEqual(a.PINS[0x030FE28C],bytes.fromhex('488b5b08'))

    def test_created_task_aware_node_initially_skips_generic_refresh(self):
        self.assertEqual(a.PINS[0x030ECB2E],bytes.fromhex('66c741080100'))
        self.assertEqual(a.PINS[0x03129078],bytes.fromhex('44386708'))
        self.assertEqual(a.JCC[0x0312907C][1],0x031290A2)
        self.assertEqual(a.PINS[0x03121A25],bytes.fromhex('6683630800'))
        self.assertEqual(a.PINS[0x03121AA2],bytes.fromhex('c6430801'))
        self.assertEqual(a.E8[0x03129092],0x030FDA9C)

    def test_synthetic_generic_when_no_big_task_reference(self):
        self.assertEqual(a.symbolic_routes(short_task_flag74=1,big_task_available=True,
            aux_route_exists=False,old_subtask_exists=True),'CREATE_GENERIC_NODE')
        self.assertEqual(a.symbolic_routes(short_task_flag74=0,big_task_available=False,
            aux_route_exists=False,old_subtask_exists=True),'CREATE_GENERIC_NODE')

    def test_synthetic_task_aware_with_old_subtask(self):
        self.assertEqual(a.symbolic_routes(short_task_flag74=0,big_task_available=True,
            aux_route_exists=False,old_subtask_exists=True),'CREATE_BIG_TASK_ANCHORED_NODE')

    def test_synthetic_null_old_subtask_blocks_replacement(self):
        self.assertEqual(a.symbolic_routes(short_task_flag74=0,big_task_available=True,
            aux_route_exists=False,old_subtask_exists=False),'SKIP_NODE_WHILE_OLD_SUBTASK_NULL')

    def test_synthetic_existing_route_not_rebuilt(self):
        self.assertEqual(a.symbolic_routes(short_task_flag74=0,big_task_available=True,
            aux_route_exists=True,old_subtask_exists=True),'PRESERVE_EXISTING_ROUTE_NODE')

    def test_synthetic_B_mode_gate_and_fail_closed(self):
        self.assertEqual(a.symbolic_routes(short_task_flag74=0,big_task_available=True,
            aux_route_exists=False,old_subtask_exists=True,B_mode_allowed=False),'NO_B_TASK_CONSTRUCTION')
        with self.assertRaisesRegex(ValueError,'SYNTHETIC_FLAG_NOT_BOOLEAN'):
            a.symbolic_routes(short_task_flag74=2,big_task_available=True,
                aux_route_exists=False,old_subtask_exists=True)

    def test_pin_counts_and_types(self):
        self.assertEqual(len(a.PINS),170)
        self.assertEqual(len(a.E8),23)
        self.assertEqual(len(a.JCC),5)
        self.assertEqual(len(a.INSTALLED_TABLES),3)
        self.assertEqual(len(a.TYPED_METHODS),3)

    def test_wrong_executable_sha_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'wrong.exe';f.write_bytes(b'MZ'+b'wrong game'*99)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                a.audit(f)
            self.assertEqual(f.read_bytes()[:2],b'MZ')

    @unittest.skipUnless(os.getenv('WH3_903_EXE'), 'Original EXE excluded from public CI')
    def test_exact_original_exe(self):
        r=a.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual(r['opcode_instruction_starts'],170)
        self.assertEqual(r['direct_E8'],23)
        self.assertEqual(r['A_to_B_exclusion_jumps'],1)
        self.assertTrue(r['same_dispatch_call_A_record_fanout_and_B_task_are_mutually_exclusive'])
        self.assertEqual(r['branch_targets'],5)
        self.assertEqual(r['vtable_RIP_installs'],3)
        self.assertFalse(r['native_patch_authorized'])
        self.assertFalse(r['task_aware_node_selected_for_real_player_SHIFT'])

if __name__=='__main__': unittest.main()
