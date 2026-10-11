"""BSC 9.0.3: exact-build cohort-gated member mode and immediate packet evidence.

Offline structural contracts are NOT WH3 runtime reproduction or crowding fix.
"""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
SOURCE=HERE/'maintenance_tools'/'native_shift_re'/'audit_actor_cohort_gate.py'
spec=importlib.util.spec_from_file_location('audit_actor_cohort_gate',SOURCE)
audit=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=audit
spec.loader.exec_module(audit)

class ActorCohortContracts(unittest.TestCase):
    def test_global_ten_buckets_is_initial_image_constant_only(self):
        self.assertEqual(audit.DATA['milliseconds_numerator_f32'],(0x0391CF08,'<f',1000.0))
        self.assertEqual(audit.DATA['global_rate_initial_u32'],(0x03D0727C,'<I',100))
        self.assertEqual(audit.DATA['float_rounding_half_f32'],(0x0391CBC8,'<f',0.5))
        self.assertEqual(round(1000.0/100),10)

    def test_guard_held_condition_is_modulo_comparison(self):
        self.assertEqual(audit.PIN['cohort_compare_remainders'],(0x03082061,'3bca'))
        self.assertEqual(audit.PIN['cohort_skip_if_other_bucket'],(0x03082063,'752b'))
        self.assertEqual(audit.PIN['cohort_current_actor_mode'][0],0x03082065)
        self.assertEqual(audit.CALLS['staggered_member_mode_compute'],(0x0308206E,0x030716CC))
        self.assertEqual(audit.CALLS['staggered_member_mode_commit'],(0x0308208B,0x03078B1C))

    def test_only_one_ordinal_bucket_per_group_counter(self):
        for t in range(100):
            matching=[v for v in range(10) if audit.scheduled_for_mode_recheck(t,v,10)]
            self.assertEqual(matching,[t%10])

    def test_synthetic_60_ordinals_partition_ten_groups(self):
        for t in range(10):
            matches=[v for v in range(60) if audit.scheduled_for_mode_recheck(t,v,10)]
            self.assertEqual(matches,list(range(t,60,10)))
        self.assertEqual(sum(audit.scheduled_for_mode_recheck(0,v,10) for v in range(60)),6)

    def test_bucket_gate_is_not_a_physical_movement_gate(self):
        self.assertGreater(audit.PIN['later_general_actor_update_is_not_gated_by_cohort'][0],
                           audit.PIN['cohort_continue_general_actor_tick'][0])
        self.assertEqual(audit.CALLS['common_member_continued_update'],(0x03082165,0x03065584))

    def test_direct_goal_receiver_has_independent_mode_setter(self):
        self.assertEqual(audit.CALLS['immediate_member_pose'],(0x0307328B,0x0315EC98))
        self.assertEqual(audit.PIN['direct_member_packet_set_mode_argument'],(0x0307329C,'c644242001'))
        self.assertEqual(audit.CALLS['immediate_member_mode_commit'],(0x030732A4,0x03078B1C))
        self.assertEqual(audit.JUMPS['member_packet_cache_tail'],(0x030732C0,0x03056ED4))

    def test_branch_b_preclassifies_another_field(self):
        self.assertEqual(audit.PIN['branch_b_preclassification_bit7_clear'][0],0x03263C00)
        self.assertEqual(audit.PIN['branch_b_preclassification_bit7_set'][0],0x03263C0A)
        self.assertEqual(audit.PIN['cohort_current_actor_mode'][0],0x03082065)
        self.assertNotEqual(0xB10,0x318)

    def test_every_constructor_actor_class_has_static_path_to_common(self):
        self.assertEqual(sum(audit.ACTOR_METHOD_COUNTS.values()),38)
        self.assertEqual(audit.ACTOR_METHOD_COUNTS[0x03081EB4],10)
        self.assertEqual(audit.ACTOR_METHOD_COUNTS[0x02F854AC],9)
        self.assertEqual(sum(audit.ACTOR_METHOD_COUNTS[v] for v in audit.SUBTYPE_COMMON_CALL_SITES),19)
        self.assertEqual(len(audit.SUBTYPE_COMMON_CALL_SITES),7)
        self.assertEqual(audit.JUMPS['second_subtype_forwards_to_common_actor_update'],(0x02F854AC,0x03081EB4))
        self.assertEqual(len(set(audit.SUBTYPE_COMMON_CALL_SITES.values())),7)

    def test_cannot_overwrite_exe(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.exe';p.write_bytes(b'MZwrong')
            self.assertRaises(ValueError,audit.OriginalPE,p)
            self.assertEqual(p.read_bytes(),b'MZwrong')

    def test_invalid_divisor_or_counter_fail_closed(self):
        for a,b,c in [(0,0,0),(0,0,-1),(-1,0,10),(0,-1,10),(2**32,0,10)]:
            with self.subTest(a=a,b=b,c=c):
                with self.assertRaises(ValueError):audit.scheduled_for_mode_recheck(a,b,c)

    def test_report_v3_uncertainty_and_no_patch(self):
        self.assertIn('NOT proof of V3',SOURCE.read_text())
        self.assertNotIn('VirtualProtect(',SOURCE.read_text())
        self.assertEqual(audit.ORIGINAL_SHA256,len(audit.ORIGINAL_SHA256)*'' or '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a')

    def test_original_exe_when_available(self):
        exe=os.environ.get('WH3_903_EXE')
        if not exe:self.skipTest('Original EXE not distributed in public CI')
        report=audit.audit(Path(exe))
        self.assertEqual(report['machine_guards'],36)
        self.assertEqual(report['checked_direct_calls'],13)
        self.assertEqual(report['checked_direct_jumps'],2)
        self.assertEqual(report['common_actor_tick_statically_reachable_vtables'],38)
        self.assertTrue(report['rate_may_change_during_game'])
        self.assertEqual(report['v3_mode_path_reached'],'UNKNOWN')
        self.assertEqual(report['patch_status'],'NO_PATCH_AUTHORIZED')

if __name__=='__main__':unittest.main()