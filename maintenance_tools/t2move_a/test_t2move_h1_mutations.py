"""H1: prove route verdicts and shadow wiring fail tests when broken."""
from pathlib import Path
import shutil, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
lua=shutil.which("lua5.1") or shutil.which("lua")
if not lua: raise SystemExit("Lua missing")
pure_file=ROOT/"source/t2move_h1_route_obligation.lua"
ctrl_file=ROOT/"source/better_shift_command.lua"
pure=pure_file.read_text(encoding="utf-8")
ctrl=ctrl_file.read_text(encoding="utf-8")
t_pure=ROOT/"maintenance_tools/t2move_a/test_t2move_h1_pure.lua"
t_ctrl=ROOT/"maintenance_tools/t2move_a/test_t2move_h1_controller.lua"
fixture=ROOT/"tests/fixture.lua"
def execute(test,path):
    cmd=[lua,str(test),str(path)]
    if test==t_ctrl:cmd.append(str(fixture))
    return subprocess.run(cmd,cwd=ROOT,timeout=30,capture_output=True,text=True)
for test,path in [(t_pure,pure_file),(t_ctrl,ctrl_file)]:
    base=execute(test,path)
    if base.returncode:raise SystemExit("BASE FAILED "+test.name+"\n"+base.stdout+base.stderr)
cases=[
("skip_prior_debt_chord","pure",
 'if chord_error(d.waypoint,f.current_pos,f.successor)>d.tolerance then',
 'if false then',"H1-08"),
("open_unpaid_turnback_chord","pure",
 'if path_error<=f.reach then','if true then',"H1-01"),
("trust_legacy_semantic_done","pure",
 'if f.semantic_done and verified_done[f.done_reason]==true then',
 'if f.semantic_done then',"H1-14"),
("use_stale_motion_crossing","pure",
 'if f.motion_fresh==true and valid_point(f.previous_pos)',
 'if valid_point(f.previous_pos)',"H1-05"),
("remove_ISSUE_shadow_hook","controller",
 'R1.H1ShadowObserve(st,cur,nexta,"ISSUE",now,decision)',
 'do end -- H1 SHADOW HOOK MUTANT',"H1-RT00"),
("remove_frozen_current_proof","controller",
 'cert.h1_shadow=h1 -- diagnostic only; E/F/G proof and commit never read it.',
 'cert.h1_shadow=nil -- mutant',"H1-RT02"),
]
for name,kind,needle,replace,expected in cases:
    src=pure if kind=="pure" else ctrl
    if src.count(needle)!=1:raise SystemExit("NONUNIQUE MUTATION "+name+" "+str(src.count(needle)))
    with tempfile.TemporaryDirectory() as td:
        mutated=Path(td)/"mutant.lua"
        mutated.write_text(src.replace(needle,replace,1),encoding="utf-8")
        result=execute(t_pure if kind=="pure" else t_ctrl,mutated)
        failures=[line for line in result.stdout.splitlines() if line.startswith("FAIL ")]
        if result.returncode==0 or not any(expected in line for line in failures):
            raise SystemExit("MUTANT SURVIVED "+name+"\n"+result.stdout+result.stderr)
        print("CAUGHT "+name+" via "+expected)
print("TOTAL",len(cases),"H1 SHADOW MUTANTS CAUGHT")
