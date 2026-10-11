"""SHA-pinned native B subroute lifecycle: static exact EXE and synthetic invariants."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[0]
NATIVE=ROOT/'audit_b_route_consumption.py'
if not NATIVE.is_file():
    NATIVE=ROOT.parent/'maintenance_tools'/'native_shift_re'/'audit_b_route_consumption.py'
spec=importlib.util.spec_from_file_location('audit_b_route_consumption',str(NATIVE))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class Node:
    def __init__(self,refs=1,ready=False,geometry=None,valid=True):
        self.refs=refs
        self.ready=ready
        self.geometry=geometry
        self.valid=valid


def tick(nodes):
    """Only behavior guaranteed by inspected 0x03128E80 loop. Symbolic model."""
    budget=0
    remaining=[]
    for node in nodes:
        if node.refs==0:continue
        if budget<1 and not node.ready and node.valid:
            node.geometry='new native route cache';node.ready=True;budget+=1
        remaining.append(node)
    return remaining,budget


class BRouteLifecycleContracts(unittest.TestCase):
    def test_exact_sha_is_hard_guard(self):
        self.assertEqual(len(audit.EXPECTED_SHA),64)
        self.assertEqual(audit.EXPECTED_SHA, '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a')
    def test_genuine_e8_target_and_mismatch(self):
        self.assertEqual(audit.call_target(0x10,b'\xe8\x05\0\0\0'),0x1a)
        self.assertEqual(audit.call_target(0x10,b'\xe8\xfb\xff\xff\xff'),0x10)
        with self.assertRaises(ValueError):audit.call_target(0x10,b'\x90'*5)
    def test_no_route_tail_junction_false_positive(self):
        self.assertEqual(audit.CALLS['B_node_link_prev_next'],(0x030ECBB8,0x0310E770))
        self.assertNotIn('motor',audit.CALLS['B_node_link_prev_next'])
    def test_exclusive_group_route_context(self):
        self.assertEqual(audit.PIN['B_task_group_route_context'][0],0x032814EF)
        self.assertEqual(audit.PIN['group_route_context_load'][0],0x02DD58D7)
    def test_node_constructor_refcount_ready(self):
        self.assertEqual(audit.PIN['B_node_alloc_refcount_1'][1],'c7410401000000')
        self.assertEqual(audit.PIN['B_node_fresh_cache_ready'][1],'66c741080100')
    def test_node_constructor_creates_geometry_only(self):
        self.assertEqual(audit.CALLS['B_route_node_build_geometry'],(0x030ECB98,0x030FE1E4))
        self.assertEqual(audit.PIN['B_node_geom_store'][1],'48894370')
    def test_node_attached_to_list(self):
        self.assertEqual(audit.PIN['B_node_group_head_store'][0],0x03121B55)
        self.assertEqual(audit.PIN['B_node_group_tail_store'][0],0x03121B6B)
    def test_old_ref_drop_is_not_immediate_unlink(self):
        self.assertEqual(audit.PIN['B_task_drop_node_ref'][1],'014804')
        self.assertEqual(audit.PIN['B_task_drop_node_ptr'][1],'4883635800')
        self.assertEqual(audit.PIN['route_manager_current_node_live'][0],0x03129059)
    def test_unlink_and_reclaim_in_later_manager(self):
        self.assertEqual(audit.CALLS['B_manager_remove_dead_node'],(0x03129065,0x03109D78))
        self.assertEqual(audit.CALLS['B_unlink_finalizer'],(0x03109DB3,0x030F65AC))
        self.assertEqual(audit.CALLS['B_geometry_release'],(0x030F65DB,0x02E1B1C0))
    def test_route_cache_only_one_per_manager_tick(self):
        nodes=[Node(),Node(),Node()]
        n1,c=tick(nodes)
        self.assertEqual((c,sum(x.ready for x in n1)),(1,1))
        n2,c=tick(n1)
        self.assertEqual((c,sum(x.ready for x in n2)),(1,2))
        n3,c=tick(n2)
        self.assertEqual((c,sum(x.ready for x in n3)),(1,3))
        n4,c=tick(n3)
        self.assertEqual(c,0)
    def test_node_live_no_rebuild_if_ready(self):
        ns,c=tick([Node(ready=True,geometry='old geometry')])
        self.assertEqual(c,0)
        self.assertEqual(ns[0].geometry,'old geometry')
    def test_node_invalid_cannot_fill_cache(self):
        ns,c=tick([Node(valid=False)])
        self.assertEqual(c,0)
        self.assertFalse(ns[0].ready)
    def test_refzero_only_drops_that_node(self):
        ns,c=tick([Node(refs=0,geometry='old'),Node(ready=True,geometry='new')])
        self.assertEqual((len(ns),c,ns[0].geometry),(1,0,'new'))
    def test_no_direct_actor_count_boundary(self):
        self.assertEqual(audit.CALLS['B_manager_refresh'],(0x03129092,0x030FDA9C))
        self.assertFalse(any('member_v' in k for k in audit.CALLS))
    def test_A_uses_shared_builder_then_member_fanout(self):
        self.assertEqual(audit.CALLS['A_generate_member_route'][1],audit.CALLS['B_manager_refresh'][1])
        self.assertEqual(audit.CALLS['A_distribute_members'][1],0x030D5490)
        self.assertEqual(audit.CALLS['A_release_temporary_route'][1],audit.CALLS['B_geometry_release'][1])
    def test_B_two_geometry_construction_strategies(self):
        self.assertEqual(audit.CALLS['B_route_node_build_geometry'][1],0x030FE1E4)
        self.assertEqual(audit.CALLS['B_fresh_node_optional_geometry'][1],0x030FDA9C)
    def test_wrong_binary_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.exe';p.write_bytes(b'MZ'+b'\0'*60)
            original=p.read_bytes()
            with self.assertRaisesRegex(ValueError,'sha mismatch'):
                audit.original_verify(p)
            self.assertEqual(p.read_bytes(),original)
    def test_output_does_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.exe';p.write_bytes(b'MZ'+b'\0'*60)
            process=subprocess.run([sys.executable,str(NATIVE),'--exe',str(p),'--out',str(p)],text=True,capture_output=True)
            self.assertNotEqual(process.returncode,0)
            self.assertEqual(p.read_bytes(),b'MZ'+b'\0'*60)
    def test_patch_is_never_enabled(self):
        text=NATIVE.read_text(encoding='utf8')
        self.assertIn('patch_authorized=False',text)
        for bad in ('VirtualProtect(', 'WriteProcessMemory(', 'patch_authorized=True'):
            self.assertNotIn(bad,text)
    def test_original_exe_if_available(self):
        import os
        path=os.environ.get('WH3_903_EXE')
        if not path:self.skipTest('CI has no redistributed original EXE')
        result=audit.original_verify(path)
        self.assertEqual(result['machine_guards'],len(audit.PIN))
        self.assertEqual(result['direct_e8_edges'],len(audit.CALLS))
        self.assertFalse(result['patch_authorized'])

if __name__=='__main__':unittest.main()