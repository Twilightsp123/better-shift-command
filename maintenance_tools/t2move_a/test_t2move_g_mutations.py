"""T2-MOVE-G real-controller route-semantic mutation gate."""
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/"source/better_shift_command.lua").read_text(encoding="utf-8")
test=ROOT/"maintenance_tools/t2move_a/test_t2move_g_adversarial.lua"
fixture=ROOT/"tests/fixture.lua"
lua=shutil.which("lua5.1") or shutil.which("lua")
if not lua: raise SystemExit("Lua interpreter missing")

cases=[
 ("disable_frozen_turnback_adoption_guard",
  'if backtrack>reach and cached.geometry.remaining>reach then',
  'if false then',
  "G-RT01"),
 ("bypass_PATH_SAFE_chord_error",
  'if g.progress>=min_progress and err<=safe_limit then',
  'if g.progress>=min_progress then',
  "G-RT01"),
 ("drop_registered_waypoint_obligation",
  'register_route_obligation(st,current,g,now)',
  'do end -- MUTANT: silently lose waypoint route debt',
  "G-RT05"),
]
def invoke(path):
    return subprocess.run([lua,str(test),str(path),str(fixture)],
        cwd=ROOT,text=True,capture_output=True,timeout=30)
base=invoke(ROOT/"source/better_shift_command.lua")
if base.returncode:
    raise SystemExit("BASE FAILED\n"+base.stdout+base.stderr)
for name,old,new,expected in cases:
    if source.count(old)!=1:
        raise SystemExit("MUTATION ANCHOR NOT UNIQUE "+name)
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"mutant.lua"
        f.write_text(source.replace(old,new,1),encoding="utf-8")
        result=invoke(f)
        failures=[line for line in result.stdout.splitlines() if line.startswith("FAIL G-RT")]
        if result.returncode==0 or not any(expected in line for line in failures):
            raise SystemExit("MUTANT SURVIVED "+name+"\n"+result.stdout+result.stderr)
        print("CAUGHT "+name+" via "+expected)
print("TOTAL",len(cases),"G CONTROLLER MUTANTS CAUGHT")
