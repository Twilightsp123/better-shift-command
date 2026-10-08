#!/usr/bin/env python3
"""Seal isolated H2-B/C/D + H3 complete source and two deterministic WH3 test packs.
This is not a real-game test and never launches WH3, commits, merges or publishes.
"""
from pathlib import Path
import hashlib, json, os, subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"output"
BASE="a74df147fa48a63df69faf795795c7ceb3cb8c92"
LOCKED_NATIVE="8fc223c9d1da5834b2034ced8e34ea9f0a8bc0a27964d6704ce931bc9a3b3b0a"
EXPECTED_HEAD_BRANCH="maintenance/t2move-h2bcd-h3-route-integrity"
def git(*args):
 return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def sha(v):return hashlib.sha256(v).hexdigest()
def sha_file(p):return sha(p.read_bytes())
def run(*cmd):subprocess.run(cmd,cwd=ROOT,check=True)
head=git("rev-parse","HEAD")
changed=git("diff","--name-only",BASE,head).splitlines()
unsafe=[p for p in changed if p.startswith((
 "src/native_bridge/","release_artifacts/native/","baseline/minhook",
 "native_maps/","docs/CURRENT_BUILD_MAP.md","tools/inspect_exe.py",
 "tools/prebuild_contract_check.py"))]
if unsafe:raise SystemExit("LOCKED NATIVE/ADDRESS CHANGED: "+repr(unsafe))
controller=ROOT/"source/better_shift_command.lua"
mirror=ROOT/"src/better_shift_command.lua"
template=ROOT/"src/better_shift_command_selfcontained.template.lua"
src=controller.read_bytes()
assert src==mirror.read_bytes(),"controller source/mirror mismatch"
template_src=template.read_text(encoding="utf-8")
text=src.decode("utf-8")
for begin,end in [
 ("-- T2MOVE_H1_SHADOW_MODULE_BEGIN","-- T2MOVE_H1_SHADOW_MODULE_END"),
 ("function R1.H1ShadowObserve(","local function route_handoff_ready("),
 ("function R1.T2MoveEPreview(","function R1.TransitionPolicy.evaluate("),
 ("function Core.reconcile_native_successor(","local function advance(st,now)")
]:
 def region(s):
  a=s.index(begin);b=s.index(end,a);return s[a:b]
 if region(text)!=region(template_src):raise SystemExit("TEMPLATE H2 REGION DIVERGES "+begin)
old=subprocess.check_output(["git","show",BASE+":source/better_shift_command.lua"],cwd=ROOT).decode("utf-8")
def cfg(s):
 a=s.index("local CFG={");b=s.index("\nlocal bmgr,bridge",a);return s[a:b]
if cfg(old)!=cfg(text):raise SystemExit("GAMEPLAY CFG CHANGED")
bridge=ROOT/"release_artifacts/native/wh3_native_bridge.dll"
minhook=ROOT/"baseline/minhook.x64.dll"
if sha_file(bridge)!=LOCKED_NATIVE:raise SystemExit("NATIVE BRIDGE BASELINE HASH MISMATCH")
OUT.mkdir(exist_ok=True)
regular=OUT/"zzz_better_shift_command_steam.pack"
debug=OUT/"zzz_better_shift_command_steam_H2H3_debug.pack"
run(sys.executable,"maintenance_tools/build_corepath_rc8.py",str(bridge),str(regular))
run(sys.executable,"maintenance_tools/verify_corepath_rc8.py",str(regular),str(bridge))
sys.path.insert(0,str(ROOT/"controller_tools"))
import pack_tools
flag=b"local DEBUG_TELEMETRY = false"
if src.count(flag)!=1:raise SystemExit("DEBUG FLAG IS NOT UNIQUE")
dbg=src.replace(flag,b"local DEBUG_TELEMETRY = true",1)
debug_raw=pack_tools.selfcontained(ROOT,dbg,bridge.read_bytes(),minhook.read_bytes())
debug.write_bytes(debug_raw)
p=pack_tools.parse_pack(debug_raw)
if pack_tools.decode_payload(p[pack_tools.BRIDGE_PATH])!=bridge.read_bytes():
 raise SystemExit("DEBUG PACK NATIVE BYTES DIVERGE")
if pack_tools.decode_payload(p[pack_tools.MINHOOK_PATH])!=minhook.read_bytes():
 raise SystemExit("DEBUG PACK MINHOOK BYTES DIVERGE")
if b"local DEBUG_TELEMETRY = true" not in p[pack_tools.CONTROLLER_PATH]:
 raise SystemExit("DEBUG CONTROLLER NOT INCLUDED")
if debug_raw!=pack_tools.selfcontained(ROOT,dbg,bridge.read_bytes(),minhook.read_bytes()):
 raise SystemExit("DEBUG PACK NOT DETERMINISTIC")
archive=OUT/"BSC_T2MOVE_H2BCD_H3_full_source_20261009.zip"
run("git","archive","--format=zip","--output="+str(archive),"HEAD")
required={
 "source/better_shift_command.lua",
 "src/better_shift_command.lua",
 "src/better_shift_command_selfcontained.template.lua",
 "source/t2move_h1_route_obligation.lua",
 "maintenance_tools/t2move_a/test_t2move_h2bcd_controller.lua",
 "maintenance_tools/t2move_a/test_t2move_h2bcd_mutations.py",
 "maintenance_tools/t2move_a/test_t2move_h3_stress.lua",
 "maintenance_tools/t2move_h3_native.lua",
 ".github/workflows/t2move-h2bcd-h3-integrity.yml",
 "docs/design/T2_MOVE_H2BCD_H3_20261009.md",
 "docs/MAINTENANCE_TODO.md",
 "docs/OPEN_ISSUES.md",
 "docs/TEST_MATRIX.md",
}
with zipfile.ZipFile(archive) as z:
 names=set(z.namelist())
 if not required<=names:raise SystemExit("INCOMPLETE ARCHIVE "+repr(sorted(required-names)))
 if z.read("source/better_shift_command.lua")!=src:raise SystemExit("ARCHIVE SOURCE MISMATCH")
 items=[sha(z.read(n))+"  "+n for n in sorted(names) if not n.endswith("/")]
manifest={
 "stage":"T2-MOVE-H2-B-C-D-H3",
 "head":head,"base_H2A":BASE,"expected_branch":EXPECTED_HEAD_BRANCH,
 "candidate":"EXPERIMENTAL_WINDOWS_WINX64_TEST_ONLY_NOT_RELEASE",
 "wh3_runtime":"NOT TESTED - REQUIRES ACTUAL GAME PROCESS",
 "release_promotion":False,
 "simulation_H2_cases":"7/7 PASS",
 "simulation_H3_route_cases":"9/9 PASS",
 "simulation_H3_native_cases":"4/4 PASS",
 "H2_mutation_cases":"5/5 CAUGHT",
 "original_maintenance":"46/46 PASS",
 "historical_SC1_early_Uturn_contract":"EXPLICITLY_SUPERSEDED_ON_ISOLATED_H2_BRANCH",
 "controller_sha256":sha_file(controller),
 "native_sha256":sha_file(bridge),
 "minhook_sha256":sha_file(minhook),
 "source_zip_sha256":sha_file(archive),
 "test_pack_sha256":sha_file(regular),
 "test_debug_pack_sha256":sha_file(debug),
 "archive_file_count":len(items),
 "source_mirror_identical":True,
 "gameplay_cfg_identical_to_H2A":True,
 "native_address_files_unchanged":True,
 "github_ci_run_id":os.environ.get("GITHUB_RUN_ID","UNVERIFIED"),
}
(OUT/"H2H3_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"H2H3_SOURCE_FILE_SHA256.txt").write_text("\n".join(items)+"\n",encoding="utf-8")
(OUT/"READ_THIS_BEFORE_TESTING.txt").write_text(
 "H2-B/C/D+H3 OFFLINE CANDIDATE. NOT STEAM RELEASE. NOT WH3 VALIDATED.\n"
 "The plain and DEBUG test packs embed the SAME locked Native DLL.\n"
 "Only ONE candidate pack may be loaded at a time; do not mix with your subscribed BSC release.\n"
 "The DEBUG pack sets DEBUG_TELEMETRY=true; preserve WH3 script_log after test.\n"
 "Original SC1 90/180 early turn tests are superseded here by strict route-fidelity requirements.\n"
 "Observe possible extra braking/stepwise movement before any release promotion.\n"
 "Run RT-TP-02/03 and RT-TP-04/05 as detailed in docs/design/T2_MOVE_H2BCD_H3_20261009.md.\n"
 "DO NOT declare WH3 success using CI/fixture results.\n",encoding="utf-8")
outputs=[archive,regular,debug,OUT/"H2H3_MANIFEST.json",OUT/"H2H3_SOURCE_FILE_SHA256.txt",OUT/"READ_THIS_BEFORE_TESTING.txt"]
(OUT/"H2H3_HANDOFF_SHA256SUMS.txt").write_text("".join(sha_file(p)+"  "+p.name+"\n" for p in outputs),encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,indent=2))
