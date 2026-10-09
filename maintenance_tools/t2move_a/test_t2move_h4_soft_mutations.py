"""H4 speed-first rounded MOVE mutation coverage; real-controller fixtures only."""
from pathlib import Path
import shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
src=(ROOT/"source/better_shift_command.lua").read_text(encoding="utf-8")
lua=shutil.which("lua5.1") or shutil.which("lua")
assert lua,"Lua required"
fixture=ROOT/"tests/fixture.lua"
tests=[ROOT/"maintenance_tools/t2move_a/test_t2move_h4_soft_controller.lua",
       ROOT/"maintenance_tools/t2move_a/test_t2move_h4_soft_native.lua"]
def run(p):
 return [subprocess.run([lua,str(t),str(p),str(fixture)],cwd=ROOT,text=True,
    capture_output=True,timeout=30) for t in tests]
base=run(ROOT/"source/better_shift_command.lua")
if any(x.returncode for x in base):raise SystemExit("BASELINE FAIL\n"+"\n".join(x.stdout+x.stderr for x in base))
mutants=[
 ("disable_soft_steering","    return \"CORNER_SOFT_ACCEPTED\"",
  '    return nil -- MUTANT NO SOFT CORNER',"H4S-01"),
 ("fake_physical_waypoint_reach",
  'mark_action_complete(st,current,"H4_SOFT_WAYPOINT_ACCEPTED",now,g.remaining)',
  'mark_action_complete(st,current,"ROUTE_NODE_REACHED",now,g.remaining)',"H4S-01"),
 ("deny_valid_native_soft_corner",
  'cached.h4_soft_credit~="CORNER_SOFT_ACCEPTED"',
  'cached.h4_soft_credit~="NEVER_SOFT"', "H4SN-01"),
 ("turn_around_without_prior_proof",
  '            g.h2_route_credit=proof and (proof.h4_soft_credit or',
  '            g.h2_route_credit=proof and ("CORNER_SOFT_ACCEPTED" or',"H4SN-03"),
]
for name,a,b,witness in mutants:
 n=src.count(a)
 if n!=1:raise SystemExit("MUTANT ANCHOR "+name+" count="+str(n))
 with tempfile.TemporaryDirectory() as td:
  mutant=Path(td)/"mutant.lua";mutant.write_text(src.replace(a,b,1),encoding="utf-8")
  results=run(mutant)
  failed=[line for x in results for line in x.stdout.splitlines() if line.startswith("FAIL ")]
  if not any(witness in line for line in failed):
   raise SystemExit("MUTANT SURVIVED "+name+"\n"+"\n".join(x.stdout+x.stderr for x in results))
  print("CAUGHT "+name+" "+witness)
print("TOTAL "+str(len(mutants))+" H4 SOFT CORNER MUTANTS CAUGHT / SYNTHETIC ONLY")
