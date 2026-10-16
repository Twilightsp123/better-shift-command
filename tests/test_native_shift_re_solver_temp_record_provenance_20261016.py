"""Native solver temporary-record provenance. Original EXE optional in CI."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
NATIVE=Path(__file__).resolve().parents[1]/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(NATIVE))
import audit_solver_temp_record_provenance_20261016 as m

class NativeSolverWorkRecord(unittest.TestCase):
    def test_original_pin_inventory(self):
        self.assertEqual((len(m.pins()),len(m.E8),len(m.JCC)),(60,8,3))
    def test_solver_receives_converter_local_not_native_node_record(self):
        p=m.pins()
        self.assertEqual(p[0x030FDCDB].hex(),'4c8d4560')
        self.assertEqual(p[0x030FDD78].hex(),'4c8d4560')
        self.assertEqual(p[0x03125A5C].hex(),'498bf8')
    def test_scratched_two_dwords_cannot_be_called_typed_pointer_by_assumption(self):
        p=m.pins()
        self.assertEqual(p[0x030F5B2B].hex(),'488906')
        self.assertEqual(p[0x030F5B30].hex(),'894e08')
        self.assertEqual(p[0x030F5B36].hex(),'894e0c')
        self.assertEqual(p[0x03125B0B].hex(),'488b4f08')
        self.assertFalse(m.packed_two_dwords(0x42800000,0x44000000)['runtime_object_pointer_proven'])
    def test_result1_call_requires_prior_guard(self):
        self.assertFalse(m.solver_early_gate(False,True))
        self.assertFalse(m.solver_early_gate(True,False))
        self.assertTrue(m.solver_early_gate(True,True))
        self.assertEqual(m.pins()[0x03125AFD].hex(),'0f85bc0c0000')
    def test_result1_vtable_chain_not_a_proven_B_member_vtable(self):
        p=m.pins()
        self.assertEqual(p[0x03125B3D].hex(),'ff5008')
        self.assertEqual(p[0x03125B67].hex(),'4c8bf8')
        self.assertEqual(p[0x031267F9].hex(),'41ff5018')
    def test_wrong_build_fails_even_optimized(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'wrong.exe';exe.write_bytes(b'MZ'+bytes(128))
            src=Path(m.__file__)
            for flags in ([],['-O']):
                r=subprocess.run([sys.executable,*flags,str(src),'--exe',str(exe)],capture_output=True,text=True)
                self.assertNotEqual(r.returncode,0)
                self.assertIn('SHA_MISMATCH',r.stderr)
    def test_no_overwrite_game_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'game.exe';exe.write_bytes(b'untouched')
            r=subprocess.run([sys.executable,str(Path(m.__file__)),'--exe',str(exe),'--out',str(exe)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('EXE_OVERWRITE_FORBIDDEN',r.stderr)
            self.assertEqual(exe.read_bytes(),b'untouched')
    @unittest.skipUnless(os.getenv('WH3_903_EXE'),'Do not store original game EXE in GitHub')
    def test_actual_original_exe(self):
        r=m.audit(os.environ['WH3_903_EXE'])
        self.assertEqual((r['opcode_decoded_sites'],r['e8_targets'],r['jcc_targets']),(60,8,3))
        self.assertFalse(r['return1_reachable_for_this_work_record_proven'])
        self.assertFalse(r['native_patch_authorized'])
if __name__=='__main__':unittest.main()
