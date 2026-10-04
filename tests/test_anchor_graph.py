import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools"))

import anchor_graph
from resolve_relations import classify_resolution


class FakeCalls:
    edges = {100: {10}, 200: {20}}

    def __init__(self, mm, pe):
        pass

    def targets(self, site_rva):
        return set(self.edges.get(site_rva, set()))

    def callsites(self, site_rva, target_rva):
        return [site_rva + 5] if target_rva in self.edges.get(site_rva, set()) else []


class FakePE:
    pass


class TestAnchorGraph(unittest.TestCase):
    def test_bidirectional_callgraph_propagation(self):
        native_map = {
            "core": {
                "caller": {"rva": "0x64"},
                "callee": {"rva": "0x0A"},
                "peer": {"rva": "0x96"},
            },
            "relationships": [
                {"id": "call", "type": "calls", "caller": "caller", "callee": "callee", "strength": "hard", "weight": 10},
                {"id": "delta", "type": "rva_delta", "left": "caller", "right": "peer", "expected_delta": 50, "tolerance": 0, "strength": "hard", "weight": 5},
            ],
        }
        domains = {"caller": [100, 200], "callee": [10, 20], "peer": [150]}
        with patch.object(anchor_graph, "CallIndex", FakeCalls):
            result = anchor_graph.propagate(None, FakePE(), native_map, domains)
        self.assertTrue(result["consistent"])
        self.assertEqual(result["nodes"]["caller"]["resolved_rva"], "0x000000C8")
        self.assertEqual(result["nodes"]["callee"]["resolved_rva"], "0x00000014")
        self.assertIn("delta", result["nodes"]["caller"]["proof_relations"])
        self.assertIn("call", result["nodes"]["callee"]["proof_relations"])

    def test_single_edge_resolution_is_not_enough_for_stage6_promotion(self):
        native_map = {
            "core": {
                "caller": {"rva": "0x64"},
                "callee": {"rva": "0x0A"},
            },
            "relationships": [
                {"id": "call", "type": "calls", "caller": "caller", "callee": "callee", "strength": "hard", "weight": 10},
            ],
        }
        domains = {"caller": [100, 200], "callee": [10, 20]}
        with patch.object(anchor_graph, "CallIndex", FakeCalls):
            result = anchor_graph.propagate(None, FakePE(), native_map, domains)
        self.assertEqual(result["nodes"]["caller"]["final_candidate_count"], 2)
        self.assertEqual(result["nodes"]["callee"]["final_candidate_count"], 2)

    def test_unique_after_one_hard_support_stays_unresolved(self):
        row = classify_resolution(
            "EXACT",
            0x1000,
            {
                "initial_candidate_count": 3,
                "final_candidate_count": 1,
                "candidates": ["0x00001100"],
                "resolved_rva": "0x00001100",
                "proof_relations": ["edge_a"],
                "support_relations": ["edge_a"],
            },
        )
        self.assertFalse(row["resolved"])
        self.assertFalse(row["minimum_structural_support_met"])
        self.assertEqual(row["method"], "EXACT")

    def test_unique_after_two_hard_supports_resolves(self):
        row = classify_resolution(
            "EXACT",
            0x1000,
            {
                "initial_candidate_count": 3,
                "final_candidate_count": 1,
                "candidates": ["0x00001100"],
                "resolved_rva": "0x00001100",
                "proof_relations": ["edge_a", "edge_b"],
                "support_relations": ["edge_a", "edge_b"],
            },
        )
        self.assertTrue(row["resolved"])
        self.assertTrue(row["minimum_structural_support_met"])
        self.assertEqual(row["method"], "EXACT_RELATION_RESOLVED")

    def test_hard_contradiction_fails_closed(self):
        native_map = {
            "core": {"a": {"rva": "0x64"}, "b": {"rva": "0x0A"}},
            "relationships": [
                {"id": "bad", "type": "calls", "caller": "a", "callee": "b", "strength": "hard"},
            ],
        }
        with patch.object(anchor_graph, "CallIndex", FakeCalls):
            result = anchor_graph.propagate(None, FakePE(), native_map, {"a": [300], "b": [10]})
        self.assertFalse(result["consistent"])
        self.assertEqual(result["contradictions"][0]["relationship"], "bad")

    def test_regional_shift_is_advisory_only(self):
        native_map = {
            "core": {
                "site": {"rva": "0x1000"},
                "anchor": {"rva": "0x2000"},
            },
            "relationships": [
                {"id": "region", "type": "regional_shift", "site": "site", "anchors": ["anchor"], "tolerance": 0x100, "strength": "advisory"},
            ],
        }
        with patch.object(anchor_graph, "CallIndex", FakeCalls):
            result = anchor_graph.propagate(None, FakePE(), native_map, {"site": [0x1100, 0x1300], "anchor": [0x2100]})
        self.assertEqual(result["nodes"]["site"]["final_candidate_count"], 2)
        self.assertEqual(result["advisory"][0]["ranked"][0]["rva"], "0x00001100")


if __name__ == "__main__":
    unittest.main(verbosity=2)
