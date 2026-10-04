import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools"))

from generate_native_header import render
from native_map_config import current_map_path

BASE = ROOT / "native_maps" / "wh3_9.0.1_6c104a63.json"
CAND = ROOT / "native_maps" / "candidates" / "wh3_9.0.2_fec656f4.json"
GENERATED = ROOT / "src" / "native_bridge" / "include" / "wh3" / "generated_native_map.hpp"

EXPECTED_902 = {
    "move": 0x030351AC,
    "attack": 0x03033544,
    "allocator": 0x02F53128,
    "halt": 0x0301C5E0,
    "lua_move": 0x02ED6404,
    "lua_attack": 0x02ED5C9C,
    "publish_move": 0x01CAFDDC,
    "publish_attack": 0x02DF3410,
    "writer_begin": 0x01BCBE28,
    "writer_finalize": 0x01BCF144,
    "copy": 0x01BACFB4,
    "stage": 0x01BAE7B8,
    "move_handler": 0x02ECFCD0,
    "attack_handler": 0x02ECF79C,
    "selection": 0x02F04F70,
    "free": 0x00537420,
}


class TestAddressPipeline(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(BASE.read_text(encoding="utf-8"))
        self.cand = json.loads(CAND.read_text(encoding="utf-8"))

    def test_current_pointer_stays_promoted_901(self):
        self.assertEqual(current_map_path(ROOT).name, "wh3_9.0.1_6c104a63.json")

    def test_base_shape_and_generated_header(self):
        self.assertEqual(len(self.base["core"]), 16)
        self.assertEqual(set(self.base["optional"]), {"contact_pair", "smart_guard"})
        self.assertEqual(render(self.base), GENERATED.read_text(encoding="utf-8"))

    def test_902_candidate_identity(self):
        self.assertEqual(self.cand["game"]["version"], "9.0.2")
        self.assertEqual(
            self.cand["game"]["sha256"],
            "fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785",
        )
        self.assertFalse(self.cand["candidate"]["release_authorized"])

    def test_902_core_rvas_frozen(self):
        actual = {name: int(spec["rva"], 0) for name, spec in self.cand["core"].items()}
        self.assertEqual(actual, EXPECTED_902)

    def test_902_optional_non_gating(self):
        self.assertFalse(self.cand["policy"]["optional_sites_are_release_gates"])
        self.assertEqual(int(self.cand["optional"]["contact_pair"]["rva"], 0), 0x030A4505)
        self.assertEqual(int(self.cand["optional"]["smart_guard"]["rva"], 0), 0x030E319C)

    def test_move_identity_is_full_not_sibling(self):
        derived = self.cand["derived"]
        self.assertEqual(int(derived["order_constructors"]["full_move"], 0), 0x0300BDC0)
        self.assertEqual(int(derived["full_move_vtable"]["rva"], 0), 0x03913618)
        self.assertEqual(
            int(derived["order_constructors"]["simple_intercept_move"], 0), 0x0300BD64
        )
        self.assertEqual(
            int(derived["simple_intercept_move_vtable"]["rva"], 0), 0x03910438
        )
        self.assertNotEqual(
            derived["full_move_vtable"]["rva"],
            derived["simple_intercept_move_vtable"]["rva"],
        )
        self.assertFalse(derived["simple_intercept_move_vtable"]["release_use"])

    def test_attack_identity(self):
        derived = self.cand["derived"]
        self.assertEqual(int(derived["order_constructors"]["attack"], 0), 0x0300B8C4)
        self.assertEqual(int(derived["attack_vtable"]["rva"], 0), 0x03912988)
        self.assertEqual(int(derived["order_constructors"]["base"], 0), 0x0300B518)

    def test_candidate_proof_levels(self):
        self.assertEqual(self.cand["core"]["attack"]["proof_level"], "L1_BYTE_MATCH")
        self.assertEqual(self.cand["core"]["halt"]["proof_level"], "L2_NORMALIZED_MATCH")
        self.assertEqual(self.cand["core"]["move"]["proof_level"], "L3_STRUCTURAL_MATCH")
        self.assertEqual(
            self.cand["core"]["publish_move"]["proof_level"], "L3_STRUCTURAL_MATCH"
        )
        self.assertEqual(
            self.cand["derived"]["full_move_vtable"]["proof"],
            "L4_DATAFLOW_DERIVED_CANDIDATE",
        )

    def test_pair_relationships(self):
        core = {name: int(spec["rva"], 0) for name, spec in self.cand["core"].items()}
        self.assertEqual(core["lua_move"] - core["lua_attack"], 0x768)
        self.assertEqual(core["move_handler"] - core["attack_handler"], 0x534)

    def test_candidate_header_is_not_promoted(self):
        rendered = render(self.cand)
        self.assertIn("fec656f433dd7eb2", rendered)
        self.assertIn("0x03913618", rendered)
        self.assertIn("0x03910438", rendered)
        self.assertEqual(current_map_path(ROOT), BASE.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2)
