#!/usr/bin/env python3
"""Seal WinX64 9.0.2 H4 speed-first test-only PACKs from the actual Windows v142 built Native DLL."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"output"
BASE_H2="0f80b083bdf55a98c257d195c531e5b78ea2956f"
OLD_NATIVE="8fc223c9d1da5834b2034ced8e34ea9f0a8bc0a27964d6704ce931bc9a3b3b0a"
KNOWN_902_NATIVE="6abf064f2655b4c94f7791476643b0752654732a530ea9d6ad1aa3ffd80327e9"
TARGET_SHA="fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785"
VERSION=b"1.0.18-corepath-wh3-fec656f4-map902"
bridge=ROOT/"input_902/wh3_native_bridge.dll"
minhook=ROOT/"baseline/minhook.x64.dll"
controller=ROOT/"source/better_shift_command.lua"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def h(path):return sha(path.read_bytes())
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def run(*a):subprocess.run(a,cwd=ROOT,check=True)
if not bridge.is_file():raise SystemExit("MISSING WINDOWS v142 NEW DLL - fail closed")
if h(bridge)==OLD_NATIVE:raise SystemExit("OLD 9.0.1 Native DLL supplied to 9.0.2 pack")
if h(bridge)!=KNOWN_902_NATIVE:raise SystemExit("H8 MUST REUSE EXACT VERIFIED 9.0.2 DLL FROM CI 37877413553")
data=bridge.read_bytes()
for token in (VERSION,TARGET_SHA.encode()):
 if token not in data:raise SystemExit("9.0.2 VERSION/EXE HASH MISSING IN NEW DLL: "+repr(token))
run(sys.executable,"maintenance_tools/t2move_a/check_h2h3_902_integration.py")
run(sys.executable,"maintenance_tools/check_native_map_contract.py")
run(sys.executable,"maintenance_tools/check_documentation_contract.py")
map_file=ROOT/"native_maps/candidates/wh3_9.0.2_fec656f4.json"
overlay=ROOT/"input_902/generated_native_map.hpp"
if not overlay.exists():raise SystemExit("Compiled 9.0.2 header artifact missing")
sys.path.insert(0,str(ROOT/"maintenance_tools"))
from generate_native_header import render
candidate=json.loads(map_file.read_text(encoding="utf-8"))
if overlay.read_text(encoding="utf-8")!=render(candidate):
 raise SystemExit("Windows-built Native header does not match candidate 9.0.2 map")
sys.path.insert(0,str(ROOT/"controller_tools"))
import pack_tools
pack_tools.native_info(data,minhook.read_bytes())
OUT.mkdir(exist_ok=True)
regular=OUT/"zzz_better_shift_command_steam_H8_terminal.pack"
debug=OUT/"zzz_better_shift_command_steam_H8_terminal_debug.pack"
run(sys.executable,"maintenance_tools/build_corepath_rc8.py",str(bridge),str(regular))
run(sys.executable,"maintenance_tools/verify_corepath_rc8.py",str(regular),str(bridge))
src=controller.read_bytes()
marker=b"local DEBUG_TELEMETRY = false"
if src.count(marker)!=1:raise SystemExit("Unexpected DEBUG marker")
debug_src=src.replace(marker,b"local DEBUG_TELEMETRY = true",1)
dbg=pack_tools.selfcontained(ROOT,debug_src,data,minhook.read_bytes())
debug.write_bytes(dbg)
parsed=pack_tools.parse_pack(dbg)
if pack_tools.decode_payload(parsed[pack_tools.BRIDGE_PATH])!=data:raise SystemExit("Debug embedded Native wrong")
if pack_tools.decode_payload(parsed[pack_tools.MINHOOK_PATH])!=minhook.read_bytes():raise SystemExit("Debug MinHook wrong")
if marker in parsed[pack_tools.CONTROLLER_PATH] or b"local DEBUG_TELEMETRY = true" not in parsed[pack_tools.CONTROLLER_PATH]:
 raise SystemExit("Debug telemetry not enabled")
if dbg!=pack_tools.selfcontained(ROOT,debug_src,data,minhook.read_bytes()):raise SystemExit("Debug pack non-deterministic")
# Keep prior production/WH3 baseline branch immutable. Native integration has not been promoted.
changed=git("diff","--name-only",BASE_H2,"HEAD").splitlines()
if any(x.startswith("src/native_bridge/src/platform_windows.cpp") for x in changed):
 raise SystemExit("Runtime hooking code diverged from H2 without a separate audit")
archive=OUT/"BSC_H8_terminal_902_full_source.zip"
run("git","archive","--format=zip","--output="+str(archive),"HEAD")
required={"source/better_shift_command.lua","native_maps/wh3_9.0.2_fec656f4.json",
 "native_maps/candidates/wh3_9.0.2_fec656f4.json","maintenance_tools/t2move_a/check_h2h3_902_integration.py",
 "maintenance_tools/t2move_a/seal_h2h3_902.py",".github/workflows/h2h3-wh3-902-integration.yml",
 "docs/past_doc/design/T2MOVE_H2H3_WH3_902_INTEGRATION_20261009.md",
 "docs/past_doc/design/T2_MOVE_H4_SPEED_SOFT_20261009.md",
 ".github/workflows/t2move-h4-soft-corner.yml",
 "maintenance_tools/t2move_a/test_t2move_h4_soft_controller.lua",
 "maintenance_tools/t2move_a/test_t2move_h6_near_pass.lua",
 "maintenance_tools/t2move_a/test_t2move_h7_native_attack.lua",
 "maintenance_tools/t2move_a/test_t2move_h8_terminal_policy.lua",
 "maintenance_tools/t2move_a/test_t2move_h8_terminal_controller.lua",
 "maintenance_tools/t2move_a/test_t2move_h8_architecture_contract.py",
 "docs/past_doc/design/T2_MOVE_H8_TERMINAL_LIVENESS_AND_OWNERSHIP_20261009.md",
 "docs/past_doc/design/T2_MOVE_H7_NATIVE_ATTACK_TERMINAL_20261009.md",
 "docs/past_doc/design/T2_MOVE_H6_ROUTE_NEAR_PASS_20261009.md",
 "maintenance_tools/t2move_a/test_t2move_h4_soft_native.lua",
 "maintenance_tools/t2move_a/test_t2move_h4_soft_mutations.py",
 "maintenance_tools/t2move_a/seal_h4_soft_902.py",
 "docs/README.md","docs/past_doc/README.md",
 "docs/current/README.md","docs/current/PRODUCT_CONTRACT.md",
 "docs/current/CURRENT_BASELINE.md","docs/current/NATIVE_RESEARCH_MAP.md",
 "docs/current/TARGET_ARCHITECTURE.md","docs/current/IMPLEMENTATION_PLAN.md",
 "docs/current/VERIFICATION.md","docs/current/RISKS_AND_DECISIONS.md",
 "docs/current/MAINTENANCE_RULES.md",
 "docs/past_doc/MAINTENANCE_TODO.md","docs/past_doc/OPEN_ISSUES.md"}
with zipfile.ZipFile(archive) as z:
 missing=required-set(z.namelist())
 if missing:raise SystemExit("SOURCE ARCHIVE INCOMPLETE "+str(missing))
 if z.read("source/better_shift_command.lua")!=src:raise SystemExit("SOURCE ARCHIVE CONTROLLER DIVERGED")
 files=[sha(z.read(p))+"  "+p for p in sorted(z.namelist()) if not p.endswith("/")]
manifest={
 "stage":"H8-EXACT-NATIVE-MOVE-TERMINAL-LIVENESS-WH3-9.0.2",
 "source_head":git("rev-parse","HEAD"),
 "base_H2H3":BASE_H2,"target_exe_sha256":TARGET_SHA,
 "native_version":VERSION.decode("ascii"),
 "native_sha256":h(bridge),
 "map_id":candidate["map_id"],
 "required_hooks":"16/16 STATIC_MAP",
 "native_smoke_in_WH3":"HISTORICAL_H4_ONLY_NOT_H8",
 "runtime_motion_in_WH3":"H8_NOT_TESTED_IN_WH3",
 "windows_v142_compile_and_ctest":"CI JOB SUCCESS PREREQUISITE",
 "native_dll_from":"REUSED_UNCHANGED_VALIDATED_WINDOWS_V142_CTEST_14_OF_14_RUN_37877413553",
 "route_policy":"SOFT_GUIDE_CONTINUITY_PRIORITY",
 "h4_controller_tests":"6/6 OFFLINE PASS",
 "h4_native_parity":"4 H4 PARITY + 2 H5 NEGATIVE RACE FIXTURES; GATED BY CI",
 "h4_gameplay_change":"ALLOW_BOUNDED_STEERING_CORNER_BEFORE_ACTUAL_WAYPOINT_REACH",
 "h5_scope":"TELEMETRY_AND_NEGATIVE_NATIVE_RACE_FIXTURES_ONLY",
 "h6_scope":"BOUNDED_POST_ACK_MOVE_GUIDE_NEAR_PASS_WITH_ACTUAL_FORWARD_PLANE_CROSSING",
 "h6_runtime_status":"EXPERIMENTAL_PENDING_WH3_REPLAY",
 "h6_fixture":"POSITIVE_AND_NEGATIVE_NEAR_PASS_GATED_IN_CI",
 "h7_scope":"ADOPT_ONLY_EXACT_NATIVE_I_PLUS_ONE_ATTACK_IN_PHYSICAL_TERMINAL_ENVELOPE",
 "h7_runtime_status":"EXPERIMENTAL_PENDING_WH3_SHIFT_ATTACK_RETEST",
 "h8_scope":"EXACT_CURRENT_NATIVE_MOVE_STABLE_PHYSICAL_TERMINAL_PROACTIVE_ATTACK",
 "h8_policy_tests":"9/9 OFFLINE_GATED",
 "h8_controller_tests":"4/4 SYNTHETIC_GATED",
 "h8_static_contract":"ARCHITECTURE_WIRING_AND_OPEN_RISK_LABELS_GATED",
 "h8_runtime_status":"EXPERIMENTAL_OFFLINE_ONLY_UNVERIFIED_IN_WH3",
 "p0_hook_allocation":"OPEN_FIRST_MOVE_MH_ERROR_MEMORY_ALLOC",
 "p2_native_queue_ownership":"OPEN_NATIVE_TAIL_NOT_PROVEN_AFTER_NONQUEUED_ROLLBACK",
 "controller_sha256":h(controller),
 "normal_pack_sha256":h(regular),
 "debug_pack_sha256":h(debug),
 "source_archive_sha256":h(archive),
 "tracked_file_count":len(files),
 "github_run_id":os.getenv("GITHUB_RUN_ID","UNKNOWN"),
 "release_promotion":False}
(OUT/"H8_TERMINAL_902_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"H8_TERMINAL_902_SOURCE_SHA256.txt").write_text("\n".join(files)+"\n",encoding="utf-8")
(OUT/"READ_H8_TERMINAL_FIRST.txt").write_text(
 "BSC H8 STATIC/OFFLINE terminal-liveness candidate for WH3 9.0.2; NOT RELEASED or H8 WH3-tested.\n"
 "The 9.0.2 Native DLL is byte-identical to successful v142 Windows CTest 14/14 build in CI 37877413553.\n"
 "Supported EXE SHA256: "+TARGET_SHA+"\n"
 "If a later WH3 validation is authorized, use ONE PACK ONLY; disable duplicate BSC PACKs.\n"
 "No new human gameplay test is required for this static/offline architecture stage.\n"
 "Speed and continuity are priority: soft 90/180 steering is intentionally allowed before exact P reach.\n"
 "H6: after ACK, actual motion near-pass of an old MOVE guide may retire its debt (NOT physical arrival).\n"
 "H7: adopt only exact already-running Native queued Shift ATTACK near end of MOVE; no proactive ISSUE permission.\n"
 "H8: independent proactive ATTACK after actual stable exact current Native MOVE within old terminal envelope.\n"
 "H8 is SYNTHETIC/OFFLINE ONLY; P0 MinHook allocation and P2 dual queue ownership REMAIN OPEN.\n"
 "Verify Native attack transition on route end without forced MOVE rollback or skipped intermediate moves.\n"
 "Check for any major skipped leg, unresolved route debt and Native i+2 rollback/reasserts, then straight Move, 90/180, zigzag and Attack.\n"
 "In-game smoothness and Native Hook allocation are NOT proven by this artifact.\n"
 "Never publish to Steam until real-game smoke and acceptance pass.\n",encoding="utf-8")
picks=[archive,regular,debug,OUT/"H8_TERMINAL_902_MANIFEST.json",OUT/"H8_TERMINAL_902_SOURCE_SHA256.txt",OUT/"READ_H8_TERMINAL_FIRST.txt"]
(OUT/"H8_TERMINAL_902_SHA256SUMS.txt").write_text("".join(h(x)+"  "+x.name+"\n" for x in picks),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,indent=2))
