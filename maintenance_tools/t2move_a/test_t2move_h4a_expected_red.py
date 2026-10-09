"""H4-A baseline: require exact two missing pre-turn run-through capabilities, not accidental red."""
from pathlib import Path
import shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
lua=shutil.which("lua5.1") or shutil.which("lua")
if lua is None:raise SystemExit("LUA_5_1_MISSING")
test=ROOT/"maintenance_tools/t2move_a/test_t2move_h4a_continuity.lua"
r=subprocess.run([lua,str(test),str(ROOT/"source/better_shift_command.lua"),str(ROOT/"tests/fixture.lua")],
 cwd=ROOT,capture_output=True,text=True,timeout=30)
passed=[l for l in r.stdout.splitlines() if l.startswith("PASS H4-A")]
failed=[l for l in r.stdout.splitlines() if l.startswith("FAIL H4-A")]
assert r.returncode!=0,"missing capability unexpectedly passed; upgrade expected-red baseline"
assert len(passed)==3 and len(failed)==2,(r.returncode,r.stdout,r.stderr)
assert all(any("FAIL H4-A0"+str(i)+" " in line for line in failed) for i in (1,2)),r.stdout
assert all(any("PASS H4-A0"+str(i)+" " in line for line in passed) for i in (3,4,5)),r.stdout
assert all("no early continuity command" in line or "no inbound run-through preparation" in line for line in failed),r.stdout
assert "CONTROLLER_FAIL" not in r.stdout,"not a clean expected-red failure"
print("H4-A EXPECTED RED: 90° and 180° have no waypoint-preserving run-through before native braking")
print("H4-A CONTROLS GREEN: 3/3 PATH_SAFE debt, pre-ACK inert, rejected ACK inert")
print("THIS IS NOT A FIX; nor evidence of WH3 smooth motion")
