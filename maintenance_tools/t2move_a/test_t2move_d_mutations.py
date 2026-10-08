"""T2-MOVE-D evidence mutations. Only Lua behavioral failures count."""
from pathlib import Path
import subprocess,tempfile,shutil
ROOT=Path(__file__).resolve().parent
lua=shutil.which('lua5.1') or shutil.which('texlua') or shutil.which('lua')
if not lua:raise SystemExit('Lua interpreter missing')
src=(ROOT/'t2move_d_evidence.lua').read_text()
test=ROOT/'test_t2move_d_evidence.lua'
mutants=[
 ('exact_current','f.exact_current_execution~=true','false'),
 ('i_plus_one','f.successor_index~=f.current_index+1','false'),
 ('debt_owner','debt.action.block_id~=current.block_id','false'),
 ('debt_tolerance','debt.tolerance,debt.action.pos.x','0,debt.action.pos.x'),
 ('debt_complete','debt.action.pos.z,done','debt.action.pos.z,false'),
 ('sample_clock','cur.ms-prev.ms~=f.poll_ms','false'),
 ('geometry_sample_consistency','math.abs(after-g.remaining)>1e-7*math.max(1,after,g.remaining)','false'),
 ('revision_binding','c[key]~=f[key]','false and c[key]~=f[key]'),
 ('poll_freshness','f.now_ms-c.sample_ms>f.observed_step_ms','false'),
 ('geometry_snapshot_copy','geometry=g,evidence=evidence','geometry=f.geometry,evidence=evidence'),
]
def run(p):return subprocess.run([lua,str(test),str(p)],capture_output=True,text=True,timeout=15)
baseline=run(ROOT/'t2move_d_evidence.lua')
if baseline.returncode:raise SystemExit('BASE FAILED\n'+baseline.stdout+baseline.stderr)
for name,old,new in mutants:
 if old not in src:raise SystemExit('ANCHOR MISSING '+name)
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'mutant.lua';p.write_text(src.replace(old,new,1))
  loader=Path(td)/'load.lua';loader.write_text('local m=assert(loadfile(arg[1]))();assert(m.VERSION)\n')
  check=subprocess.run([lua,str(loader),str(p)],capture_output=True,text=True,timeout=15)
  if check.returncode:raise SystemExit('INFRASTRUCTURE/SYNTAX '+name+'\n'+check.stdout+check.stderr)
  out=run(p)
  if out.returncode==0:raise SystemExit('MUTANT SURVIVED '+name)
  if 'FAIL D' not in out.stdout:raise SystemExit('NOT BEHAVIOR FAILURE '+name+'\n'+out.stdout+out.stderr)
  print('CAUGHT '+name)
print('TOTAL',len(mutants),'MUTANTS CAUGHT')
