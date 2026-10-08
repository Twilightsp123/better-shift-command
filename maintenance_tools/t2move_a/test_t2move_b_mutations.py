"""T2-MOVE-B mutations: syntax/infrastructure failures are not counted as caught."""
from pathlib import Path
import shutil,subprocess,tempfile
root=Path(__file__).resolve().parent
lua=shutil.which('lua5.1') or shutil.which('texlua') or shutil.which('lua')
if not lua: raise SystemExit('FAIL Lua interpreter missing')
source=(root/'t2move_b_shadow.lua').read_text()
a=str(root/'t2move_a_shadow.lua')
test=str(root/'test_t2move_b_shadow.lua')
mutations=[
 ('route_gate','c.route_ok~=true','false'),
 ('debt_hard_gate','c.prior_debt_mode~="CLEAR" and c.prior_debt_mode~="SOFT_PRESERVED"','false'),
 ('sc3_deviation_gate','g.route_debt_error>g.route_debt_limit','false'),
 ('progress_gate','g.progress<g.route_min_progress','false'),
 ('path_cut_error_gate','g.cut_error>g.cut_safe_limit','false'),
 ('path_cut_cap_gate','g.cut_safe_limit>g.cut_tolerance','false'),
 ('corner_window_max_gate','g.corner_window~=math.max(g.corner_window_base,g.corner_window_early)','false'),
 ('corner_window_reach_gate','g.remaining>g.corner_window','false'),
 ('corner_adjacent_leg_cap','g.corner_window>math.min(g.leg,g.next_leg)','false'),
 ('sc4_proof','g.corner_stall_escape~=true','false'),
 ('temporal_issue_consistency','g.remaining<=temporal_frontier','false'),
 ('clock_alignment','evidence.current_sample_ms-evidence.previous_sample_ms~=c.poll_ms','false'),
 ('ground_motion_bound','evidence.ground_distance<radial_travel','false'),
 ('G1_ready_required','g.arrival_brake_ready~=true','false'),
 ('G1_measurement_required','math.abs(g.arrival_sync_margin-radial_travel)>','false and math.abs(g.arrival_sync_margin-radial_travel)>'),
 ('one_poll_bound','g.remaining>temporal_frontier+one_poll_travel','false'),
 ('stall_temporal_gate','if g.stall==true then','if false and g.stall==true then'),
 ('preserve_sc3_debt','preserve_prior_debt=c.prior_debt_mode=="SOFT_PRESERVED"','preserve_prior_debt=false'),
 ('correct_steering_credit','credit=c.route_mode=="STEERING_CORNER" and','credit=false and c.route_mode=="STEERING_CORNER" and'),
 ('frozen_geometry','geometry=copy_scalars(g)','geometry=g'),
]
def run(path):
    return subprocess.run([lua,test,a,str(path)],capture_output=True,text=True,timeout=15)
base=run(root/'t2move_b_shadow.lua')
if base.returncode: raise SystemExit('BASELINE FAILED\n'+base.stdout+base.stderr)
for name,old,new in mutations:
    if source.count(old)!=1: raise SystemExit('MUTANT SOURCE ANCHOR NOT UNIQUE: '+name)
    with tempfile.TemporaryDirectory() as td:
        mutant=Path(td)/'mutant.lua'
        mutant.write_text(source.replace(old,new,1),encoding='utf-8')
        load=Path(td)/'load.lua'
        load.write_text('local m=assert(loadfile(arg[1]))(); assert(type(m.preview)=="function");print("MODULE_LOADED")\n')
        sanity=subprocess.run([lua,str(load),str(mutant)],capture_output=True,text=True,timeout=15)
        if sanity.returncode or 'MODULE_LOADED' not in sanity.stdout:
            raise SystemExit('SYNTAX/INFRA FAILURE: '+name+'\n'+sanity.stdout+sanity.stderr)
        result=run(mutant)
        if result.returncode==0: raise SystemExit('MUTANT SURVIVED: '+name)
        fails=[s for s in result.stdout.splitlines() if s.startswith('FAIL B')]
        if not fails: raise SystemExit('NON-BEHAVIOR FAILURE: '+name+'\n'+result.stdout+result.stderr)
        print('CAUGHT '+name+' :: '+fails[0])
print('TOTAL',len(mutations),'MUTANTS CAUGHT')
