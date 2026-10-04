#!/usr/bin/env python3
"""Prepare a build-local Native Bridge map overlay from a verified WH3 candidate.

This command never changes native_maps/CURRENT and never overwrites the checked-in
promoted generated header. It verifies the candidate against the supplied EXE,
then writes an isolated include overlay plus a manifest and Windows v142 commands.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from generate_native_header import render
from native_map_config import current_map_path
from verify_candidate_map import verify
ROOT = Path(__file__).resolve().parents[1]
def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def prepare(exe: Path, map_path: Path, out_dir: Path) -> dict:
    candidate=json.loads(map_path.read_text(encoding="utf-8"));meta=candidate.get("candidate")
    if not isinstance(meta,dict): raise ValueError("map is not a candidate")
    if meta.get("release_authorized") is not False: raise ValueError("candidate build lane requires release_authorized=false")
    if len(candidate.get("core",{}))!=16: raise ValueError("candidate must contain 16 mandatory core hooks")
    promoted_before=current_map_path(ROOT).resolve()
    if promoted_before==map_path.resolve(): raise ValueError("candidate build lane may not target native_maps/CURRENT")
    verification=verify(exe,candidate);rendered=render(candidate)
    include_root=out_dir/"include";header=include_root/"wh3"/"generated_native_map.hpp";native_build=out_dir/"native"
    header.parent.mkdir(parents=True,exist_ok=True);header.write_text(rendered,encoding="utf-8")
    promoted_after=current_map_path(ROOT).resolve()
    if promoted_after!=promoted_before: raise RuntimeError("native_maps/CURRENT changed during candidate preparation")
    manifest={"schema":1,"tool":"prepare_candidate_build","candidate_map":str(map_path.resolve()),"candidate_map_id":candidate["map_id"],
      "candidate_game_version":candidate["game"]["version"],"candidate_exe_sha256":candidate["game"]["sha256"],
      "candidate_release_authorized":False,"promoted_map_unchanged":str(promoted_after),"generated_header":str(header.resolve()),
      "generated_header_sha256":_sha256(rendered.encode("utf-8")),"cmake_native_map_include_dir":str(include_root.resolve()),
      "cmake_build_dir":str(native_build.resolve()),"static_verification":verification,
      "next_gates":["Windows v142/MASM configure+build","Windows Native CTest","WH3 native runtime smoke","L5 runtime verification","promotion only after all gates pass"]}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"candidate_build_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    ps=f'''$ErrorActionPreference = "Stop"
$Root = "{ROOT.resolve()}"
$Build = "{native_build.resolve()}"
$MapInclude = "{include_root.resolve()}"
$CandidateMap = "{map_path.resolve()}"
$Exe = "{exe.resolve()}"
python "$Root/maintenance_tools/verify_candidate_map.py" --exe "$Exe" --map "$CandidateMap"
python "$Root/maintenance_tools/check_native_map_contract.py" --map "$CandidateMap" --generated "$MapInclude/wh3/generated_native_map.hpp"
python "$Root/tools/prebuild_contract_check.py"
cmake -S "$Root/src/native_bridge" -B "$Build" -G "Visual Studio 16 2019" -A x64 -T v142 -DWH3_NATIVE_MAP_INCLUDE_DIR="$MapInclude"
cmake --build "$Build" --config Release
ctest --test-dir "$Build" -C Release --output-on-failure
'''
    (out_dir/"build_windows_v142.ps1").write_text(ps,encoding="utf-8");return manifest
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--exe",required=True,type=Path);ap.add_argument("--map",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    m=prepare(a.exe,a.map,a.out);print("PASS");print("map="+m["candidate_map_id"]);print("header="+m["generated_header"]);print("static_candidate_verification=PASS");print("CURRENT_unchanged=true");print("next_gate=WINDOWS_V142_BUILD")
if __name__=="__main__": main()
