#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'maintenance_tools'/'native_shift_re'))
import r49_spatial_evidence_preflight as a

def mk(seq,t,coords,epoch=1,skew=100.0,duration=900.0,member_class='ordinary_exact_vtable'):
    rows=[]
    for i,(x,z) in enumerate(coords,1):
        row={'member_id':f'm{epoch}_{i}', 'member_index':i,'member_type':member_class,
             'position_xyz':[x,0,z],'stored_goal_xz':[x,10] if member_class=='ordinary_exact_vtable' else None,
             'goal_has_reference':False,'pending_delta_xyz':[0,0,0] if member_class=='ordinary_exact_vtable' else None,
             'action':'b2_general_action_vtable' if member_class=='ordinary_exact_vtable' else 'not_typed',
             'read_offset_us':200+(i-1)*skew}
        rows.append(row)
    return {'schema':'bsc.n1.passive_member_snapshot.v1','unit_token':'U','build':'6acec6f4',
            'sample_id':seq,'time_ms':t,'member_count':len(rows),'sample_type':'sequential-not-atomic',
            'inventory_stable':True,'intra_sample_full_roster_stable':True,
            'roster_bytes_checked':8*len(rows),'cross_snapshot_lifetime_proven':False,
            'native_patch_authorized':False,'roster_epoch':epoch,
            'read_duration_us':duration,'rows':rows}

class Preflight(unittest.TestCase):
    def test_compression_is_only_candidate(self):
        x=a.preflight([mk(0,0,[(0,0),(1.5,0),(0,2)]),
                       mk(1,80,[(0.6,0),(0.7,0),(0,2)])])
        self.assertEqual(x['compared_intervals'],1)
        self.assertEqual(x['evidence_grade'],'SEQUENTIAL_NEAR_TIME_PASSIVE_SPATIAL_ONLY')
        self.assertFalse(x['root_cause_proven'])
        self.assertTrue(x['candidate_proximity_events'])
    def test_epoch_prevents_cross_generation_pair(self):
        x=a.preflight([mk(0,0,[(0,0),(1.5,0)],epoch=1),
                       mk(1,80,[(0.6,0),(0.7,0)],epoch=2)])
        self.assertEqual(x['compared_intervals'],0)
        self.assertEqual(x['excluded_due_to_roster_epoch_change'],1)
    def test_large_gap_rejected(self):
        x=a.preflight([mk(0,0,[(0,0),(1.5,0)]),mk(1,300,[(0.6,0),(0.7,0)])])
        self.assertEqual(x['excluded_due_to_gap'],1)
    def test_large_row_skew_rejected(self):
        x=a.preflight([mk(0,0,[(0,0),(1.5,0)],skew=3000,duration=4000),
                       mk(1,100,[(0.6,0),(0.7,0)],skew=3000,duration=4000)])
        self.assertEqual(x['excluded_due_to_within_sample_skew'],1)
    def test_missing_mark_rejected(self):
        v=mk(0,0,[(0,0),(1.5,0)])
        del v['intra_sample_full_roster_stable']
        with self.assertRaisesRegex(ValueError,'R49_FULL_ROSTER_GUARD_REQUIRED'):a.preflight([v])
    def test_long_duration_rejected(self):
        v=mk(0,0,[(0,0),(1.5,0)],duration=5001)
        with self.assertRaisesRegex(ValueError,'BAD_SAMPLING_DURATION'):a.preflight([v])
    def test_invalid_row_time_rejected(self):
        v=mk(0,0,[(0,0),(1.5,0)])
        v['rows'][0]['read_offset_us']=-1
        with self.assertRaisesRegex(ValueError,'MISSING_OR_INVALID_ROW_TIME'):a.preflight([v])
    def test_unknown_member_is_position_only(self):
        v=mk(0,0,[(0,0),(1.5,0)],member_class='unknown_position_only')
        a.validate_r49_sample(v)
        v['rows'][0]['action']='walk_a'
        with self.assertRaisesRegex(ValueError,'UNTYPED_MEMBER_MUST_BE_POSITION_ONLY'):a.preflight([v])
    def test_pointer_id_rejected(self):
        v=mk(0,0,[(0,0),(1.5,0)])
        v['rows'][0]['member_id']='0x12345678'
        with self.assertRaisesRegex(ValueError,'RAW_POINTER_IDENTIFIER_FORBIDDEN'):a.preflight([v])
    def test_epoch_from_member_id_validated(self):
        v=mk(0,0,[(0,0),(1.5,0)])
        v['rows'][0]['member_id']='m3_1'
        with self.assertRaisesRegex(ValueError,'R49_ID_EPOCH_MISMATCH'):a.preflight([v])
    def test_no_spurious_interval_bridging(self):
        x=a.preflight([mk(0,0,[(0,0),(1.5,0)]),mk(1,50,[(0.2,0),(1.3,0)]),
                       mk(2,600,[(0.5,0),(1.1,0)]),mk(3,650,[(0.6,0),(.9,0)])])
        self.assertEqual(x['compared_intervals'],2)
        self.assertEqual(x['excluded_due_to_gap'],1)
    def test_not_overwrite_source_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.jsonl';p.write_text(json.dumps(mk(0,0,[(0,0),(1,0)]))+'\n')
            import subprocess
            r=subprocess.run([sys.executable,str(Path(a.__file__)),'--input',str(p),'--output',str(p)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('refusing to overwrite',r.stderr)

if __name__=='__main__':unittest.main()
