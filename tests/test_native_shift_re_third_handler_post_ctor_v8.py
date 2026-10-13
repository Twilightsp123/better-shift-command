"""Exact BSC N1 post-constructor virtual+8, bounded negative regression."""
import os, sys, unittest
from pathlib import Path
MODULES=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(MODULES))
import audit_third_handler_post_ctor_v8 as a

class ThirdPostCtorV8(unittest.TestCase):
    def test_exactly_the_existing_16_constructors(self):
        self.assertEqual(set(a.POSTCALL_V8), set(a.CONSTRUCTOR_CALL_SITES))
        self.assertEqual(len(a.POSTCALL_V8), 16)
    def test_virtual_plus8_target_not_keyboard_specialization(self):
        self.assertEqual(a.VTABLE, 0x03ADE428)
        self.assertEqual(a.VTABLE_PLUS_8, 0x03ADE430)
        self.assertEqual(a.EMPTY_METHOD, 0x008D3280)
    def test_all_postcall_dispatch_sites_are_pinned(self):
        self.assertEqual(len({v[0] for v in a.POSTCALL_V8.values()}), 16)
        self.assertEqual(sum(v[1]=='48ff6008' for v in a.POSTCALL_V8.values()),12)
        self.assertEqual(sum(v[1]=='ff5008' for v in a.POSTCALL_V8.values()),4)
    def test_destructor_typed_vtable_and_resource_fields(self):
        self.assertEqual(a.DTOR_PINS[0x03266FD1], '488d0550748700')
        self.assertEqual(a.DTOR_PINS[0x03266FDB], '488d053e758700')
        self.assertEqual(a.DTOR_PINS[0x03266FED], '488b8b98000000')
        self.assertEqual(a.DTOR_PINS[0x03267024], '488b8b80000000')
    def test_wrong_sha_rejected_before_read(self):
        fake=type('Fake',(),{'sha':'wrong'})()
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
            a.verify(fake)
    def test_wrong_vtable_is_fail_closed(self):
        fake=type('Fake',(),{
            'sha':a.ORIGINAL_SHA,
            'base':0x140000000,
            'read':lambda self, site, n, code=False: b'\x00'*n,
        })()
        with self.assertRaisesRegex(ValueError,'VTABLE_PLUS8_NO_LONGER_EMPTY'):
            a.verify(fake)
    def test_decoded_line_parser_filters_non_instruction_text(self):
        class Fake:
            def disasm(self,site,n):
                return 'metadata\n  30d3023: 48 ff 60 08 jmp QWORD PTR [rax+0x8]\n'
        self.assertEqual(a.decoded_lines(Fake(),0x030D3023,0x030D3027),
                         [(0x030D3023,'jmp QWORD PTR [rax+0x8]')])
    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Original EXE excluded from public CI')
    def test_original_903_exe(self):
        r=a.audit(Path(os.environ['WH3_903_EXE']))
        self.assertEqual(r['post_ctor_virtual_plus_8_dispatches'],16)
        self.assertEqual((r['tail_jumps'],r['direct_calls']),(12,4))
        self.assertFalse(r['MOVE_slot_plus_A0_pointer_alias_proven'])
        self.assertFalse(r['native_patch_authorized'])

if __name__=='__main__':unittest.main()
