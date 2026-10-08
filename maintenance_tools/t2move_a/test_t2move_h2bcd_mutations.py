"""H2 B/C/D: behavior mutation gate for issue, Native adoption and route-credit."""
from pathlib import Path
import shutil, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
src_path=ROOT/"source/better_shift_command.lua"
src=src_path.read_text(encoding="utf-8")
lua=shutil.which("lua5.1") or shutil.which("lua")
if not lua:raise SystemExit("Lua 5.1 unavailable")
fixture=ROOT/"tests/fixture.lua"
tests=[ROOT/"maintenance_tools/t2move_a/test_t2move_h2bcd_controller.lua",
       ROOT/"maintenance_tools/t2move_h3_native.lua"]
def invoke(p):
 return [subprocess.run([lua,str(t),str(p),str(fixture)],cwd=ROOT,text=True,
    capture_output=True,timeout=30) for t in tests]
base=invoke(src_path)
for n,r in enumerate(base):
 if r.returncode:raise SystemExit("BASE FAILED "+tests[n].name+"\n"+r.stdout+r.stderr)
cases=[
 ("remove_issue_fidelity_gate",'        if not h2 or h2.state=="BLOCKED" then',
  '        if false then',"H2-RT01"),
 ("remove_preissue_identity_guard",'            if not h2 or h2.state=="BLOCKED" then',
  '            if false then',"H2-RT01"),
 ("remove_native_obligation_guard",
  'if type(obligation)~="table" or\n       (obligation.state~="SATISFIED" and obligation.state~="DEBT_PRESERVED") then',
  'if false then',"H3-N02"),
 ("credit_payable_debt_as_complete",
  'if g.h2_route_credit=="SATISFIED" then',
  'if g.h2_route_credit=="DEBT_PRESERVED" then',"H2-RT04"),
 ("discard_unpaid_route_debt",
  '                else\n                    register_route_obligation(st,current,g,now)\n                    if DEBUG_TELEMETRY then dlog("H2_EXECUTION_COMMITTED_ROUTE_OWED',
  '                else\n                    do end -- illegal lost route debt\n                    if DEBUG_TELEMETRY then dlog("H2_EXECUTION_COMMITTED_ROUTE_OWED',"H2-RT04"),
]
for name,old,new,expected in cases:
 if src.count(old)!=1:raise SystemExit("BAD MUTATION ANCHOR "+name+" "+str(src.count(old)))
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/"mutant.lua";p.write_text(src.replace(old,new,1),encoding="utf-8")
  results=invoke(p)
  failures=[x for r in results for x in r.stdout.splitlines() if x.startswith("FAIL ")]
  if all(r.returncode==0 for r in results) or not any(expected in f for f in failures):
   raise SystemExit("MUTANT SURVIVED "+name+"\n"+"\n".join(r.stdout+r.stderr for r in results))
  print("CAUGHT "+name+" via "+expected)
print("TOTAL",len(cases),"H2 ROUTE CREDIT MUTANTS CAUGHT; OFFLINE ONLY")
