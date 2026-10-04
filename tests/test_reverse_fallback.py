import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "maintenance_tools"))

from extract_bindiff_matches import extract
from consume_ghidra_evidence import resolve as resolve_ghidra
from run_ghidra_fallback import analyze_headless


class TestReverseFallback(unittest.TestCase):
    def test_bindiff_schema_discovery_and_anchor_extract(self):
        native_map = {
            "core": {
                "move": {"rva": "0x1000"},
                "attack": {"rva": "0x2000"},
            }
        }
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "x.BinDiff"
            db = sqlite3.connect(str(db_path))
            db.execute("CREATE TABLE function(id INTEGER, address1 INTEGER, address2 INTEGER, similarity REAL, confidence REAL)")
            db.execute("INSERT INTO function VALUES(1, 4096, 4352, 0.98, 0.91)")
            db.execute("INSERT INTO function VALUES(2, 9999, 8888, 0.2, 0.1)")
            db.commit(); db.close()
            result = extract(db_path, native_map)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["anchor"], "move")
        self.assertEqual(result["matches"][0]["candidate_rva"], "0x00001100")
        self.assertAlmostEqual(result["matches"][0]["similarity"], 0.98)

    def test_ghidra_callgraph_can_reduce_unresolved_callee(self):
        bundle = {
            "resolved_core": {"caller": "0x00001000"},
            "sites": {
                "callee": {
                    "relationships": [
                        {"id": "edge", "type": "calls", "caller": "caller", "callee": "callee", "strength": "hard"}
                    ]
                }
            },
        }
        evidence = {
            "exe_sha256": "x",
            "records": {
                "anchor:caller": {
                    "site_rva": "0x00001000",
                    "direct_calls": [{"target_rva": "0x00002000"}],
                },
                "candidate:callee:1": {"site_rva": "0x00002000", "direct_calls": []},
                "candidate:callee:2": {"site_rva": "0x00003000", "direct_calls": []},
            },
        }
        result = resolve_ghidra(bundle, evidence)
        row = result["sites"]["callee"]
        self.assertEqual(row["resolution"], "GHIDRA_GRAPH_UNIQUE")
        self.assertEqual(row["resolved_rva"], "0x00002000")
        self.assertFalse(row["release_authorized"])

    def test_analyze_headless_discovery(self):
        with tempfile.TemporaryDirectory() as td:
            support = Path(td) / "support"
            support.mkdir()
            tool = support / "analyzeHeadless"
            tool.write_text("#!/bin/sh\n")
            self.assertEqual(analyze_headless(Path(td)), tool)

    def test_ghidra_evidence_script_exports_graph_features(self):
        text = (ROOT / "maintenance_tools" / "ghidra" / "BscRelocationEvidence.py").read_text(encoding="utf-8")
        for token in (
            "getCallingFunctions",
            "getCalledFunctions",
            "getCodeBlocksContaining",
            "getFlowType().isCall()",
            "search_window",
        ):
            self.assertIn(token, text)

    def test_ghidra_runner_requires_bundle_exe_sha_match(self):
        text = (ROOT / "maintenance_tools" / "run_ghidra_fallback.py").read_text(encoding="utf-8")
        self.assertIn("Ghidra evidence EXE SHA mismatch", text)
        self.assertIn('bundle_payload.get("manifest", {}).get("exe_sha256")', text)
        self.assertIn('payload.get("exe_sha256")', text)

    def test_binexport_headless_options_are_single_semicolon_argument(self):
        text = (ROOT / "maintenance_tools" / "run_ghidra_fallback.py").read_text(encoding="utf-8")
        self.assertIn('"Subtract Imagebase;Prepend Namespace to Function Names"', text)
        self.assertNotIn('"Subtract Imagebase",\n            "Prepend Namespace to Function Names"', text)

    def test_stage7_bundle_declares_no_exe_and_bindiff_requirement(self):
        text = (ROOT / "maintenance_tools" / "export_re_bundle.py").read_text(encoding="utf-8")
        self.assertIn('"exe_included": False', text)
        self.assertIn('"matching old EXE or old .BinExport required"', text)
        self.assertIn('"GHIDRA_ENUMERATION_ONLY"', text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
