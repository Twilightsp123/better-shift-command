"""T2-MOVE-F: behavior mutations for V3-only and live-revision fail closed."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
src=(ROOT/"source/better_shift_command.lua").read_text(encoding="utf-8")
test=ROOT/"maintenance_tools/t2move_a/test_t2move_f_boundaries.lua"
fixture=ROOT/"tests/fixture.lua"
lua=shutil.which("lua5.1") or shutil.which("texlua") or shutil.which("lua")
if not lua: raise SystemExit("Lua 5.1 unavailable")
mutations=[
    ("accept_V2_fallback",'if ctx.execution_provider~="V3" then','if false then',"F-RISK-01"),
    ("skip_live_revision_match",'if live_revision~=st.revision or live_revision~=cached.revision then','if false then',"F-RISK-02"),
    ("fabricate_missing_live_revision",
        'if not ok_revision or not id(live_revision) then\n        return nil,"MOVE_LIVE_REVISION_UNAVAILABLE"\n    end',
        'if not ok_revision or not id(live_revision) then\n        live_revision=st.revision -- unsafe fabricated fallback\n    end',
        "F-RISK-05"),
]
def invoke(path):
    return subprocess.run([lua,str(test),str(path),str(fixture)],
        cwd=ROOT,capture_output=True,text=True,timeout=20)
base=invoke(ROOT/"source/better_shift_command.lua")
if base.returncode: raise SystemExit("BASE FAILED\n"+base.stdout+base.stderr)
for name,old,new,expected in mutations:
    if src.count(old)!=1: raise SystemExit("ANCHOR NOT UNIQUE "+name)
    with TemporaryDirectory() as d:
        tmp=Path(d)/"mutant.lua"
        tmp.write_text(src.replace(old,new,1),encoding="utf-8")
        result=invoke(tmp)
        if result.returncode==0 or not any(x.startswith("FAIL "+expected) for x in result.stdout.splitlines()):
            raise SystemExit("MUTANT SURVIVED "+name+"\n"+result.stdout+result.stderr)
        print("CAUGHT "+name+" via "+expected)
print("TOTAL",len(mutations),"F CONTROLLER MUTANTS CAUGHT")
