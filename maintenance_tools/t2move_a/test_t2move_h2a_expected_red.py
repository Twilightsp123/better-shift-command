"""H2-A intentionally-red regression seal: exactly two legacy ACK route-credit failures.
Do not treat xfail as gameplay success. This gates the proof of the original bug.
"""
from pathlib import Path
import re, shutil, subprocess
ROOT=Path(__file__).resolve().parents[2]
lua=shutil.which("lua5.1") or shutil.which("lua")
if not lua:raise SystemExit("LUA_UNAVAILABLE")
test=ROOT/"maintenance_tools/t2move_a/test_t2move_h2a_ack_credit.lua"
controller=ROOT/"source/better_shift_command.lua"
fixture=ROOT/"tests/fixture.lua"
r=subprocess.run([lua,str(test),str(controller),str(fixture)],cwd=ROOT,capture_output=True,text=True,timeout=30)
lines=r.stdout.splitlines()
passed=[x for x in lines if x.startswith("PASS H2-A")]
failed=[x for x in lines if x.startswith("FAIL H2-A")]
must_fail=("H2-A01","H2-A02")
must_pass=("H2-A03","H2-A04","H2-A05","H2-A06")
assert r.returncode!=0,"Expected-red fixture unexpectedly green; did runtime credit change?"
assert len(passed)==4 and len(failed)==2,("Unexpected pass/fail count",r.stdout,r.stderr)
assert all(any("FAIL "+i+" " in x for x in failed) for i in must_fail),r.stdout
assert all(any("PASS "+i+" " in x for x in passed) for i in must_pass),r.stdout
assert all("STEERING_CORNER_HANDOFF" in x and "remaining=40.000000" in x for x in failed),r.stdout
assert any("TOTAL 4 PASS 2 FAIL" in x for x in lines),r.stdout
assert "CONTROLLER_FAIL" not in r.stdout,"Controller crash rather than route-credit bug"
print("CONFIRMED RED H2-A01 H2-A02: 40m-unpaid STEERING_CORNER_HANDOFF after ACK")
print("CONFIRMED GREEN H2-A03 A04 A05 A06: reach, forward debt, pending and rejection")
print("TOTAL EXPECTED-RED 2/2 REPRODUCED; 4/4 CONTROL CASES PASS. NO WH3 RUNTIME CLAIM.")
