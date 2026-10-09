#!/usr/bin/env python3
"""Prevent mixing old WH3 9.0.1 address bytes or Native binaries into the 9.0.2 H2/H3 test pack."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"maintenance_tools"))
from generate_native_header import render
from native_map_config import current_map_path, candidate_map_path
BASE_901="wh3_9.0.1_6c104a63.json"
TARGET="fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785"
VERSION="1.0.18-corepath-wh3-fec656f4-map902"
past="1.0.17-corepath-wh3-6c104-movevtfix"
old_map=current_map_path(ROOT)
assert old_map.name==BASE_901,"Released/default CURRENT pointer was unexpectedly promoted"
p=ROOT/"native_maps/wh3_9.0.2_fec656f4.json"
q=candidate_map_path(ROOT)
a=json.loads(p.read_text(encoding="utf-8"));b=json.loads(q.read_text(encoding="utf-8"))
assert a["game"]["sha256"]==b["game"]["sha256"]==TARGET
assert a["game"]["version"]==b["game"]["version"]=="9.0.2"
assert set(a["core"])==set(b["core"]) and len(a["core"])==16
for key in a["core"]:
  assert a["core"][key]["rva"]==b["core"][key]["rva"],key+" RVA"
  assert a["core"][key]["guard"]==b["core"][key]["guard"],key+" guard"
for key in ("full_move_vtable","simple_intercept_move_vtable","attack_vtable"):
  assert a["derived"][key]["rva"]==b["derived"][key]["rva"],key
assert b["derived"]["full_move_vtable"]["rva"]=="0x03913618"
assert b["derived"]["simple_intercept_move_vtable"]["rva"]=="0x03910438"
assert b["derived"]["attack_vtable"]["rva"]=="0x03912988"
assert b["candidate"]["release_authorized"] is False
assert not b["policy"]["optional_sites_are_release_gates"]
assert '9.0.2' in render(b) and TARGET in render(b)
paths=["source/better_shift_command.lua","src/better_shift_command.lua",
       "src/better_shift_command_selfcontained.template.lua","tests/fixture.lua",
       "controller_tools/pack_tools.py","maintenance_tools/check_corepath_rc8.py",
       "src/native_bridge/include/wh3/bridge_host.hpp"]
for path in paths:
  txt=(ROOT/path).read_text(encoding="utf-8")
  assert VERSION in txt,(path,"missing new Native identity")
  assert past not in txt,(path,"old Native identity survived")
source=(ROOT/paths[0]).read_bytes()
assert source==(ROOT/paths[1]).read_bytes(),"Lua Controller mirrors diverged"
template=(ROOT/paths[2]).read_text(encoding="utf-8")
a1=source.decode("utf-8")
for start,end in [("function Core.commit_transition_edge(","function Core.observe_move_completion("),
                  ("function R1.T2MoveEPreview(","function R1.TransitionPolicy.evaluate("),
                  ("function Core.reconcile_native_successor(","local function advance(st,now)")]:
 assert a1[a1.index(start):a1.index(end,a1.index(start))]==template[template.index(start):template.index(end,template.index(start))],start
cmake=(ROOT/"src/native_bridge/CMakeLists.txt").read_text(encoding="utf-8")
assert "project(wh3_bridge_host VERSION 1.0.18" in cmake
for option in ("$<$<COMPILE_LANGUAGE:CXX>:/W4>","$<$<COMPILE_LANGUAGE:CXX>:/WX>","$<$<COMPILE_LANGUAGE:CXX>:/EHsc>"):
 assert option in cmake,"ASM_MASM unsafe options"
assert "target_compile_options(${t} PRIVATE /W4 /WX /EHsc)" not in cmake
assert "WH3_NATIVE_MAP_INCLUDE_DIR" in cmake
print("PASS 9.0.2 static integration: 16/16 exact RVA+guards, full Move/Attack VTables, H2/H3 mirrors, CXX-only MASM flags")
print("PASS source of truth: 9.0.2 candidate overlay is separate from unchanged 9.0.1 CURRENT")
print("PASS Native bridge target version",VERSION)
