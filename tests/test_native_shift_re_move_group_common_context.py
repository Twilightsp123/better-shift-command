"""Regression: exact game group/route/task lineage without false pointer alias."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_move_group_common_context as a

class MoveGroupCommonContext(unittest.TestCase):
    def test_real_group_constructor_param_root_passed_with_stack_abi(self):
        self.assertEqual(a.PINS[0x0301B90F].hex(),'4c8bc6') # r8 = root
        self.assertEqual(a.DIRECT_CALLS[0x0301B91F],0x0301B834)
        # 0x0301B834: params = rsp-after-push/sub+0x20;
        # [entry-rsp-0x20] = [params+0x08] receives r8.
        entry_sp=0x100000
        current_sp=entry_sp-8-0x40
        param_base=current_sp+0x20
        self.assertEqual(entry_sp-0x20,param_base+0x8)
        self.assertEqual(a.PINS[0x0301B84A].hex(),'4c8940e0')
        self.assertEqual(a.PINS[0x0301B8AB].hex(),'488d542420')

    def test_group_is_really_typed_same_unitroot(self):
        self.assertEqual(a.DIRECT_CALLS[0x0301B8B7],0x030C2C3C)
        self.assertEqual(a.DIRECT_CALLS[0x030C2C61],0x030C2D40)
        self.assertEqual(a.PINS[0x030C2C5A].hex(),'4883c230') # rdx=root+0x30
        self.assertEqual(a.PINS[0x030C2D40].hex(),'488b4208') # [root+0x38]
        self.assertEqual(a.PINS[0x030C2D4E].hex(),'48894110') # group+0x10
        self.assertEqual(a.PINS[0x030C2C7D].hex(),'488983100a0000') # group+0xA10
        self.assertEqual(a.PINS[0x0301B96D].hex(),'48899ef8320000') # root+0x32F8

    def test_two_route_descriptor_branches_both_store_root_plus270(self):
        self.assertEqual(a.PINS[0x03012987].hex(),'48898770020000')
        self.assertEqual(a.PINS[0x030129E5].hex(),'48898f70020000')
        self.assertEqual(a.DIRECT_CALLS[0x03012982],0x03008894)
        self.assertEqual(a.PINS[0x0302DBC9].hex(),'488b8570020000')
        self.assertEqual(a.PINS[0x0302DBD3].hex(),'488b5018')
        self.assertEqual(a.PINS[0x0302DBD7].hex(),'488b5270')

    def test_short_task_belongs_to_separate_constructor(self):
        self.assertEqual(a.DIRECT_CALLS[0x030260AF],0x02F2C734)
        self.assertEqual(a.PINS[0x030260A8].hex(),'488b5108') # rdx=root
        self.assertEqual(a.PINS[0x02F2C74D].hex(),'48895108') # task+0x08=root
        self.assertEqual(a.INSTALLED_VTABLES[0x02F2C777],0x03ABBE18)
        self.assertEqual(a.VTABLE_METHODS[0x03ABBE18+0x10],0x02F561E8)
        self.assertEqual(a.DIRECT_CALLS[0x02F56404],0x03279E40)
        self.assertEqual(a.PINS[0x02F563FD].hex(),'488b89f8320000')

    def test_deferred_dispatch_uses_root_route_metadata_under_mode_gate(self):
        self.assertEqual(a.DIRECT_CALLS[0x03279E62],0x02DC2E04)
        self.assertEqual(a.PINS[0x03279E69].hex(),'744f')
        self.assertEqual(a.PINS[0x03279E78].hex(),'498b81100a0000') # group+a10
        self.assertEqual(a.PINS[0x03279E7F].hex(),'488b8870020000') # root+270
        self.assertEqual(a.PINS[0x03279EA7].hex(),'f30f105940') # route+40
        self.assertEqual(a.DIRECT_CALLS[0x03279EB3],0x030D554C)

    def test_route_config_and_deferred_group_share_field_provenance(self):
        p=a.symbolic_sources('unit_A')
        self.assertEqual(p['route_config']['source_geometry'],p['deferred_fanout']['source_geometry'])
        self.assertEqual(p['route_config']['source_context'],p['deferred_fanout']['source_context'])
        self.assertNotEqual(p['route_config']['route_payload_creator'],p['deferred_fanout']['converter'])
        self.assertFalse(p['queue_big_task_plus160_alias_proven'])
        q=a.symbolic_sources('unit_B')
        self.assertNotEqual(p['route_config']['source_geometry'],q['route_config']['source_geometry'])
        self.assertEqual(a.PINS[0x030088C9].hex(),'488b8860010000')
        self.assertEqual(a.PINS[0x030D55DD].hex(),'488b8960010000')
        self.assertEqual(a.PINS[0x030D55E4].hex(),'4883c118')

    def test_two_inputs_to_same_member_fanout_are_distinct(self):
        self.assertEqual(a.DIRECT_CALLS[0x0302DBDB],0x030D5490)
        self.assertEqual(a.DIRECT_CALLS[0x030D55F5],0x030FDA9C)
        self.assertEqual(a.DIRECT_CALLS[0x030D5603],0x030D5490)
        self.assertEqual(a.PINS[0x030D54D9].hex(),'4c8d0476')
        self.assertEqual(a.PINS[0x030D54F0].hex(),'488b1cf0')
        self.assertEqual(a.PINS[0x030D550F].hex(),'ff9068030000')

    def test_pinned_coverage_and_leaf_boundaries(self):
        self.assertEqual(len(a.PINS),98)
        self.assertEqual(len(a.DIRECT_CALLS),15)
        self.assertEqual(len(a.VTABLE_METHODS),2)
        self.assertEqual(len(a.INSTALLED_VTABLES),3)
        self.assertEqual(a.LEAF_SPAN,(0x030C2D40,0x030C2DC6))

    def test_wrong_executable_sha_rejected_without_writes(self):
        class Wrong:
            sha='not_903'
            closed=False
            def close(self):self.closed=True
        wrong=Wrong()
        with patch.object(a,'StrictPE',return_value=wrong):
            with self.assertRaisesRegex(ValueError,'WRONG_ORIGINAL_EXE_SHA'):
                a.audit(Path('/tmp/not_real.exe'))
        self.assertTrue(wrong.closed)

    @unittest.skipUnless(os.environ.get('WH3_903_EXE'),'Original WH3 executable is private and excluded from public CI')
    def test_true_exact_original_903_exe(self):
        result=a.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual((result['opcode_and_objdump_instruction_starts'],result['direct_E8_calls']),(98,15))
        self.assertFalse(result['task_callback_always_fanout'])
        self.assertFalse(result['group_context_plus160_equals_queued_big_task_plus160_proven'])
        self.assertFalse(result['native_gameplay_patch_authorized'])

if __name__=='__main__':unittest.main()
