"""Exact-original BSC comprehensive graph contract tests, no executable mutation."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'maintenance_tools'/'native_shift_re'
sys.path.insert(0,str(SRC))
import audit_wh3_full_native_chain as full

class FullNativeChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=full.read_manifest(SRC/'full_chain_manifest.json')

    def test_strict_original_sha_and_build(self):
        m=self.manifest
        self.assertEqual(m['exe_sha256'],full.EXPECTED_SHA)
        self.assertEqual(m['unwind_function_count'],209180)
        self.assertEqual(full.from_hex(m['image_base']),full.EXPECTED_IMAGE_BASE)

    def test_comprehensive_object_aware_node_scope(self):
        m=self.manifest
        self.assertEqual(len(m['known_nodes']),175)
        self.assertEqual(len({n['rva'] for n in m['known_nodes']}),175)
        self.assertGreaterEqual(len(m['categories']),10)
        for k in ('RMB_SHIFT_COMMAND','MOVE_TASK_STATE','GROUP_FANOUT_A',
                  'GROUP_TASK_B','B_ROUTE_GEOMETRY','GROUP_TICK_SCHEDULERS',
                  'ACTOR_GOAL_TRANSFORM','ACTOR_PER_FRAME',
                  'ACTOR_CACHE_AND_CONTACT','MEMBER_FLAG_B7'):
            self.assertIn(k,m['categories'])
            self.assertTrue(m['categories'][k])

    def test_combined_original_opcode_sources(self):
        m=self.manifest
        self.assertEqual(len(m['guard_sites']),445)
        self.assertGreaterEqual(len({x['source'] for x in m['guard_sites']}),9)
        self.assertTrue(any(x['site']=='0x2f879d7'for x in m['guard_sites']))
        self.assertTrue(any(x['site']=='0x3263c0a'for x in m['guard_sites']))

    def test_curated_call_sites_and_disassembly_edges(self):
        m=self.manifest
        self.assertEqual(len(m['direct_edges']),141)
        self.assertEqual(len(m['all_decoded_outgoing_calls']),1083)
        self.assertEqual(m['counts']['extra_callee_stubs'],466)
        self.assertEqual(m['counts']['known_to_known'],276)
        self.assertTrue(all(x['kind'] in ('call','jmp') for x in m['direct_edges']))
        self.assertTrue(all(x['site'].startswith('0x') for x in m['direct_edges']))

    def test_batch_a_path_and_b_task_independent(self):
        m=self.manifest
        branches=m['categories']
        self.assertIn(hex(0x30d5490),branches['GROUP_FANOUT_A'])
        self.assertIn(hex(0x3263ab0),branches['GROUP_TASK_B'])
        self.assertIn(hex(0x3128e80),branches['GROUP_TICK_SCHEDULERS'])
        self.assertFalse(m['patch_authorized'])

    def test_same_offset_different_owner_objects(self):
        o=self.manifest['native_object_ownership']
        unit=next(z for z in o if z['holder']=='unit+0x1F0')
        route=next(z for z in o if z['holder']=='route_context+0x1F0')
        self.assertNotEqual(unit['object'],route['object'])
        self.assertIn('0x02F853A0',unit['consumer'])
        self.assertIn('0x03128E80',route['consumer'])

    def test_route_cache_is_not_actor_local_spline(self):
        o=self.manifest['native_object_ownership']
        route=next(z for z in o if z['holder']=='node+0x70')
        actor=next(z for z in o if z['holder']=='subtype_actor+0xB60/+0xBCC')
        self.assertNotEqual(route['object'],actor['object'])
        self.assertIn('NOT identified',route['meaning'])

    def test_b_member_bit7_dataflow_and_virtual_method_owner(self):
        m=self.manifest
        bridge=m['newly_connected_conditional_dataflow']
        self.assertIn('0x03263AB0',bridge['write'])
        self.assertIn('0x02F87684',bridge['read'])
        tables={(x['slot'],x['implementation']) for x in m['vtable_entries']}
        self.assertIn((hex(0x3905d98+0x78),hex(0x2f87684)),tables)
        self.assertIn((hex(0x3905d18+0x78),hex(0x11287fc)),tables)
        self.assertNotEqual(0x11287fc,0x2f87684)
        self.assertIn('no runtime call trace',bridge['necessary_unproven_condition'])

    def test_deferred_packet_actor_task_is_different_vtable(self):
        s={(x['slot'],x['implementation']) for x in self.manifest['vtable_entries']}
        self.assertIn((hex(0x3905e18+0x10),hex(0x2f83b24)),s)
        self.assertIn((hex(0x3905d98+0x78),hex(0x2f87684)),s)

    def test_group_tick_calls_are_verified_by_site(self):
        e={(x['site'],x['dest']) for x in self.manifest['all_decoded_outgoing_calls']}
        expected=[(0x2dd58ae,0x2f853a0),(0x2dd58c6,0x2dd81b0),
                  (0x2dd58de,0x3128e80),(0x302dbdb,0x30d5490)]
        for site,dest in expected:
            self.assertIn((hex(site),hex(dest)),e)

    def test_reject_fabricated_v3_branch_claim_or_patch(self):
        m=json.loads(json.dumps(self.manifest))
        self.assertEqual(m['original_v3_branch_execution'],
                         'not recorded; no code-level proof A vs B was taken')
        self.assertIs(m['patch_authorized'],False)
        self.assertTrue(any('not been connected' in z for z in m['explicit_unknown_data_edges']))

    def test_readonly_wrong_binary_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'faux.exe';content=b'MZ' + b'NOT_THE_WH3_BINARY'*10
            p.write_bytes(content)
            with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                full.StrictPE(p)
            self.assertEqual(p.read_bytes(),content)

    def test_never_overwrite_exe(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'wrong.exe';data=b'MZbad';p.write_bytes(data)
            import subprocess
            cp=subprocess.run([sys.executable,str(SRC/'audit_wh3_full_native_chain.py'),
                '--exe',str(p),'--out',str(p)],capture_output=True,text=True)
            self.assertNotEqual(cp.returncode,0)
            self.assertEqual(p.read_bytes(),data)

    def test_detailed_graphviz_keeps_proven_edges(self):
        dot=full.generate_dot(self.manifest)
        self.assertEqual(dot.count('[label="0x'),175)
        self.assertIn('F3279E40',dot)
        self.assertIn('F2F87684',dot)
        self.assertNotIn('patch.dll',dot)

    def test_original_wh3_if_attached(self):
        exe=os.getenv('WH3_903_EXE')
        if not exe:self.skipTest('CI does not contain game executable')
        p=full.StrictPE(Path(exe))
        try:
            checks=full.verify(p,self.manifest,True)
            self.assertEqual(checks['checks']['opcode_guards'],445)
            self.assertEqual(checks['checks']['decoded_function_bodies'],175)
            self.assertEqual(checks['checks']['vtable_entries'],21)
        finally:p.close()

if __name__=='__main__':unittest.main()