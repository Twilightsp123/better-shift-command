#!/usr/bin/env python3
"""Offline exact-SHA build guard + mathematically labelled synthetic policy tests."""
import os, sys, tempfile, subprocess, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO_TOOLS=HERE.parent/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(REPO_TOOLS if REPO_TOOLS.is_dir() else HERE))
import audit_r55_group_span_policy as a

class PolicyContracts(unittest.TestCase):
    def test_pin_manifest_inventory(self):
        self.assertEqual(len(a.parse_pins()),96)
    def test_policy_pairs_are_distinct(self):
        self.assertEqual(len(a.POLICY_TABLES),7)
        self.assertEqual(len(set(v[0] for v in a.POLICY_TABLES.values())),7)
    def test_numeric_dimension_floor(self):
        self.assertEqual([(n,a.floor_square_dimension(n)) for n in (1,8,15,16,60)],
                         [(1,1),(8,2),(15,3),(16,4),(60,7)])
    def test_numeric_dimension_ceil(self):
        self.assertEqual([(n,a.ceil_square_dimension(n)) for n in (1,8,15,16,60)],
                         [(1,1),(8,3),(15,4),(16,4),(60,8)])
    def test_linear_extent(self):
        self.assertAlmostEqual(a.linear_span(4,1.2,0.8),3.6)
    def test_cannot_call_span_a_curvature_radius(self):
        # Arbitrary synthetic figure shows lateral offset not curvature formula.
        self.assertEqual(0.5*a.linear_span(5,0,2),4.)
    def test_reject_bad_n(self):
        for n in (-1,1.5,None):
            with self.assertRaises(ValueError):a.floor_square_dimension(n)
    def test_reject_nonfinite_spacing(self):
        for x in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):a.linear_span(2,0,x)
    def test_leaf_rets_have_explicit_bounds(self):
        self.assertEqual(len(a.LEAVES),11)
    def test_distinct_external_group_policy(self):
        self.assertEqual(a.POLICY_TABLES['dynamic_bounded_linear'][1],0x03065020)
    def test_pin_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            old=a.PIN
            try:
                other=Path(td)/'pins.txt'
                other.write_text(old.read_text(encoding='utf8')+'\n030C7D17 90\n',encoding='utf8')
                a.PIN=other
                with self.assertRaises(ValueError):a.parse_pins()
            finally:a.PIN=old
    def test_self_no_gameplay_patch_api(self):
        source=Path(a.__file__).read_text('utf8')
        self.assertNotIn('WriteProcessMemory',source)
        self.assertNotIn('Frida.attach',source)
    @unittest.skipUnless(os.environ.get('WH3_NEW_EXE'),'private WH3 exe absent')
    def test_real_user_pe(self):
        result=a.audit(os.environ['WH3_NEW_EXE'])
        self.assertEqual(result['verified_pinned_instruction_sites'],96)
        self.assertEqual(result['verified_policy_vtable_pairs'],7)
        self.assertEqual(result['verified_direct_e8'],3)
        self.assertFalse(result['native_patch_authorized'])
        self.assertFalse(result['turn_radius_parameter_proven'])
    def test_wrong_sha_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'fake.exe';bad.write_bytes(b'MZ'+bytes(126))
            with self.assertRaises(ValueError):a.audit(bad)
    def test_cli_never_overwrites_exe(self):
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'fake.exe';bad.write_bytes(b'MZ'+bytes(126))
            proc=subprocess.run([sys.executable,str(Path(a.__file__)),
                     '--exe',str(bad),'--out',str(bad)],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(bad.read_bytes(),b'MZ'+bytes(126))

if __name__=='__main__':unittest.main(verbosity=2)
