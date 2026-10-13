"""Synthetic-only regression for type-predicate RIP and registration xrefs."""
import sys
import unittest
import struct
from pathlib import Path
MODULES = Path(__file__).resolve().parents[1] / 'maintenance_tools' / 'native_shift_re'
sys.path.insert(0, str(MODULES))
import audit_factory_registry_xrefs as a
import audit_two_handler_factory_origins as origins

class SyntheticPE:
    base = 0x140000000
    sections = [('.text', 0x1000, 0x50, 0, 0x50, 0x20000000),
                ('.rdata', 0x4000, 0x20, 0, 0x20, 0)]
    def __init__(self):
        self.code = bytearray(b'\x90' * 0x50)
        ref = 0x03D19A88
        self.code[0x10:0x17] = b'\x48\x8d\x05' + struct.pack('<i', ref - (0x1010+7))
        # Decodes as a raw byte pattern but starts inside mov eax, imm32.
        self.code[0x20:0x28] = b'\xb8\x48\x8d\x05' + struct.pack('<i', ref - (0x1021+7))
        self.data = bytearray(b'\x00' * 0x20)
        struct.pack_into('<Q', self.data, 0x08, self.base+0x03940ED8)
    def read(self, rva, n, code=False):
        if 0x1000 <= rva and rva+n <= 0x1050:
            return bytes(self.code[rva-0x1000:rva-0x1000+n])
        if 0x4000 <= rva and rva+n <= 0x4020:
            return bytes(self.data[rva-0x4000:rva-0x4000+n])
        raise ValueError('fixture bounds')
    def function(self, site):
        return (0x1000, 0x1050) if 0x1000 <= site < 0x1050 else None
    def disasm(self, start, length):
        return ('  1010: 48 8d 05 71 8a d1 03 lea rax,[rip+0x3d18a71]\n'
                '  1020: b8 48 8d 05 00 mov eax,0x58d48\n')

class NativeRegistryXrefContracts(unittest.TestCase):
    def test_all_four_existing_lea_targets_are_recomputed(self):
        for addr, dest in a.TYPE_PREDICATE_LEAS.items():
            code = bytes.fromhex(origins.PINS[addr])
            self.assertEqual(a.decode_rip_site(code, addr)[0], dest)
    def test_reject_non_rip_and_handle_signed_displacement(self):
        self.assertEqual(a.decode_rip_site(b'\x48\x8d\x05\xf9\xff\xff\xff', 0x1000),
                         (0x1000, 7))
        self.assertIsNone(a.decode_rip_site(b'\xe8\xf9\xff\xff\xff', 0x1000))
        self.assertIsNone(a.decode_rip_site(b'\x48\x8d\x45\x00', 0x1000))
    def test_static_candidate_inside_instruction_does_not_pass(self):
        self.assertEqual([x['site'] for x in a.code_xrefs(SyntheticPE())],
                         ['0x00001010'])
    def test_pointer_not_mistaken_for_invoked_virtual_call(self):
        refs = a.pointer_xrefs(SyntheticPE())
        self.assertEqual([(x['site'], x['target']) for x in refs],
                         [('0x00004008', '0x03940ED8')])
        self.assertIn('consumer unproven', refs[0]['evidence'])
    def test_different_registry_candidates_are_not_collapsed(self):
        self.assertNotEqual(a.TARGETS[0x03D19C08], a.TARGETS[0x03D19C10])
        self.assertEqual(len(a.TYPE_PREDICATE_LEAS), 4)

if __name__ == '__main__':
    unittest.main()
