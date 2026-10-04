import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"maintenance_tools"))
from generate_native_header import render
from native_map_config import current_map_path
CAND=ROOT/"native_maps"/"candidates"/"wh3_9.0.2_fec656f4.json"
class TestCandidateBuildLane(unittest.TestCase):
 def setUp(self): self.candidate=json.loads(CAND.read_text(encoding="utf-8"))
 def test_candidate_is_not_promoted(self):
  self.assertNotEqual(current_map_path(ROOT).resolve(),CAND.resolve());self.assertFalse(self.candidate["candidate"]["release_authorized"])
 def test_overlay_header_is_self_contained(self):
  h=render(self.candidate);self.assertIn(self.candidate["game"]["sha256"],h);self.assertIn("0x030351AC",h);self.assertIn("0x03913618",h);self.assertIn("0x03910438",h)
  self.assertIn("kCoreGuards{{\n",h);self.assertNotIn("kCoreGuards{{{{",h);self.assertIn("kHookNames{{\n",h);self.assertNotIn("kHookNames{{{{",h)
 def test_prepare_script_does_not_write_promoted_header(self):
  s=(ROOT/"maintenance_tools"/"prepare_candidate_build.py").read_text(encoding="utf-8");self.assertNotIn("src/native_bridge/include/wh3/generated_native_map.hpp",s);self.assertIn('out_dir/"include"',s);self.assertIn("CURRENT changed during candidate preparation",s)
 def test_cmake_overlay_contract(self):
  s=(ROOT/"src/native_bridge/CMakeLists.txt").read_text(encoding="utf-8");self.assertIn("WH3_NATIVE_MAP_INCLUDE_DIR",s);self.assertIn("target_include_directories(wh3_host_core BEFORE",s);self.assertIn("target_include_directories(wh3_native_bridge BEFORE",s);self.assertIn("wh3/generated_native_map.hpp",s);self.assertIn("COMPILE_LANGUAGE:CXX",s);self.assertNotIn("target_compile_options(${t} PRIVATE /W4 /WX /EHsc)",s)
 def test_native_fixtures_follow_generated_map(self):
  for rel in ("src/native_bridge/tests/test_host.cpp","src/native_bridge/tests/test_dual_root.cpp","src/native_bridge/tests/test_integrated_host.cpp"):
   with self.subTest(rel=rel):
    s=(ROOT/rel).read_text(encoding="utf-8");self.assertIn("wh3/generated_native_map.hpp",s);self.assertNotIn("0x03910AA8",s);self.assertNotIn("0x03910228",s)
 def test_no_api_literal_newline_corruption(self):
  checks={"maintenance_tools/check_native_map_contract.py":"render\\nfrom native_map_config","tools/prebuild_contract_check.py":"render\\nfrom native_map_config","maintenance_tools/wh3_update.py":"generate_candidate\\nfrom native_map_config","maintenance_tools/run_checks_corepath_rc8.py": "),\\n      ('address_pipeline","src/native_bridge/src/bridge_host.cpp":'bridge_host.hpp"\\n#include'}
  for rel,forbidden in checks.items():
   with self.subTest(rel=rel): self.assertNotIn(forbidden,(ROOT/rel).read_text(encoding="utf-8"))
if __name__=="__main__": unittest.main(verbosity=2)
