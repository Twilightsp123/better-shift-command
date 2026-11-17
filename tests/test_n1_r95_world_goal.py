"""R95 public offline world-goal tests. Synthetic data is not WH3 gameplay."""
import os
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools" / "native_shift_re"))
from r95_world_goal import (InvalidEvidence, record, affine_world,
                            resolve, inspect_snapshot)

def make_frame(t=(0,0,0), rows=((1,0,0),(0,1,0),(0,0,1))):
    b=bytearray(0x5c)
    struct.pack_into("<3f", b, 0x18, *t)
    for i,row in enumerate(rows):
        struct.pack_into("<3f", b, 0x38+12*i, *row)
    return bytes(b)

def make_goal(kind, pos, pointer):
    off={"nav":0x10, "packet":0x18}[kind]
    b=bytearray(off+8)
    struct.pack_into("<3f", b, 0, *pos)
    struct.pack_into("<Q", b, off, pointer)
    return bytes(b)

def fixture():
    common={"root_generation":"R1","group_generation":"G1",
            "route_generation":"L1","tick_id":1,"reference_epoch":1}
    ref=0x10005000
    a={"member_id":"a","record_kind":"nav",
       "record_hex":make_goal("nav",(2,0,4),ref).hex(),**common}
    b={"member_id":"b","record_kind":"packet",
       "record_hex":make_goal("packet",(2,0,4),ref).hex(),**common}
    return {"origin":"synthetic",**common,
            "reference_bytes_by_pointer":{hex(ref):make_frame((10,0,-30)).hex()},
            "members":[a,b]}

class TestR95WorldGoal(unittest.TestCase):
    def test_nav_reference_offset(self):
        self.assertEqual(record("nav",make_goal("nav",(1,2,3),0xA))[1],0xA)
    def test_packet_reference_offset(self):
        b=bytearray(make_goal("packet",(1,2,3),0xB))
        struct.pack_into("<Q",b,0x10,0xBADE) # deliberately unrelated field
        self.assertEqual(record("packet",b)[1],0xB)
    def test_null_reference(self):
        self.assertEqual(resolve("nav",make_goal("nav",(1,2,3),0),{}),(1,2,3))
    def test_translation(self):
        self.assertEqual(affine_world((1,2,3),make_frame((10,20,30))),
                         (11,22,33))
    def test_rotation_xz(self):
        frame=make_frame(rows=((0,0,-1),(0,1,0),(1,0,0)))
        self.assertEqual(affine_world((3,2,4),frame),(-4,2,3))
    def test_nonunit_basis(self):
        frame=make_frame(rows=((2,1,0),(0,3,0),(0,0,-2)))
        self.assertEqual(affine_world((2,3,4),frame),(7,9,-8))
    def test_same_local_moving_frame_changes_world(self):
        self.assertNotEqual(affine_world((2,0,4),make_frame((10,0,0))),
                            affine_world((2,0,4),make_frame((50,0,0))))
    def test_different_local_same_world(self):
        self.assertEqual(affine_world((1,0,0),make_frame((10,0,0))),
                         affine_world((6,0,0),make_frame((5,0,0))))
    def test_same_tick_reconciles(self):
        a=inspect_snapshot(fixture())
        self.assertEqual([m["world_xyz"] for m in a["members"]],
                         [[12.0,0.0,-26.0]]*2)
        self.assertEqual(a["evidence_level"],"STRUCTURAL_ONLY")
        self.assertFalse(a["shift_causality_proven"])
    def test_mismatched_member_epoch_rejected(self):
        s=fixture();s["members"][1]["group_generation"]="G2"
        with self.assertRaises(InvalidEvidence):inspect_snapshot(s)
    def test_missing_reference_rejected(self):
        s=fixture();s["reference_bytes_by_pointer"]={}
        with self.assertRaises(InvalidEvidence):inspect_snapshot(s)
    def test_duplicate_member_rejected(self):
        s=fixture();s["members"][1]["member_id"]="a"
        with self.assertRaises(InvalidEvidence):inspect_snapshot(s)
    def test_truncated_reference_rejected(self):
        with self.assertRaises(InvalidEvidence):affine_world((1,2,3),b"short")
    def test_untrusted_fake_verified_origin_rejected(self):
        s=fixture();s["origin"]="engine_owned_verified"
        with self.assertRaises(InvalidEvidence):inspect_snapshot(s)

if __name__=="__main__":unittest.main()
