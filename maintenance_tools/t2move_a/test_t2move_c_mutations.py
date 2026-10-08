"""T2-MOVE-C: every mutation must compile and produce a behavioral fixture failure."""
from pathlib import Path
import subprocess, tempfile, sys, shutil
ROOT=Path(__file__).resolve().parent
base_path=ROOT/'t2move_c_txn_shadow.lua'
source=base_path.read_text(encoding='utf-8')
lua=shutil.which('lua5.1') or shutil.which('texlua') or shutil.which('lua')
if not lua: raise SystemExit('Lua interpreter missing')
test=ROOT/'test_t2move_c_txn_shadow.lua'
A=ROOT/'t2move_a_shadow.lua'
B=ROOT/'t2move_b_shadow.lua'
mutants=[
 ('ignore_generation','st.gen~=cache.a.gen','false'),
 ('ignore_revision','st.revision~=cache.revision','false'),
 ('ignore_prior_debt_change','st.prior_debt_signature~=cache.prior_debt_signature','false'),
 ('ignore_action_identity','st.plan[st.idx]~=cache.current','false'),
 ('ignore_successor_identity','st.plan[st.idx+1]~=cache.successor','false'),
 ('ignore_i2','q.future_index~=st.idx+1','false'),
 ('ignore_busy_txn','st.pending_by_uid or st.transition_txn or st.blocked or st.terminal','st.pending_by_uid or st.blocked or st.terminal'),
 ('allow_unknown_lineage','q.execution_lineage~="PLAYER_NATIVE" and q.execution_lineage~="BSC_ISSUED"','false'),
 ('permit_bad_preview','if not preview.preview_open or preview.authoritative~=false then','if false and (not preview.preview_open or preview.authoritative~=false) then'),
 ('wrong_credit','if mode=="STEERING_CORNER_HANDOFF" then','if false and mode=="STEERING_CORNER_HANDOFF" then'),
 ('forget_to_abort','Core.abort_transition_txn(st,tx,"TXN_COMMIT_REJECTED",q.now_ms)','-- MUTANT: no abort'),
 ('skip_observed_state','tx.state="OBSERVED";tx.execution_lineage=q.execution_lineage','tx.execution_lineage=q.execution_lineage'),
 ('ignore_geometry_mandatory','for _,name in ipairs(required_geom) do\n        if g[name]==nil then return false,"MOVE_SNAPSHOT_MISSING_"..name end','for _,name in ipairs(required_geom) do\n        if false and g[name]==nil then return false,"MOVE_SNAPSHOT_MISSING_"..name end'),
 ('ignore_hard_debt','if g.route_debt_mode=="HARD" then return nil,"CURRENT_ROUTE_DEBT_HARD" end','if false and g.route_debt_mode=="HARD" then return nil,"CURRENT_ROUTE_DEBT_HARD" end'),
]
def execute(path):
    return subprocess.run([lua,str(test),str(A),str(B),str(path)],capture_output=True,text=True,timeout=20)
base=execute(base_path)
if base.returncode or 'TOTAL 25 PASS 0 FAIL' not in base.stdout:
    raise SystemExit('BASELINE NOT GREEN\n'+base.stdout+'\n'+base.stderr)
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    loader=tmp/'loader.lua'
    loader.write_text('local x=assert(loadfile(arg[1]))();assert(type(x.simulate_observed)=="function");print("MODULE_LOADED")\n',encoding='utf-8')
    for name,old,new in mutants:
        if source.count(old)!=1: raise SystemExit(f'ANCHOR_NOT_UNIQUE {name}: {source.count(old)}')
        p=tmp/(name+'.lua');p.write_text(source.replace(old,new,1),encoding='utf-8')
        loaded=subprocess.run([lua,str(loader),str(p)],capture_output=True,text=True,timeout=10)
        if loaded.returncode or 'MODULE_LOADED' not in loaded.stdout:
            raise SystemExit('INFRASTRUCTURE/SYNTAX_FAILURE '+name+'\n'+loaded.stdout+loaded.stderr)
        result=execute(p)
        if result.returncode==0: raise SystemExit('MUTANT_SURVIVED '+name)
        failed=[s for s in result.stdout.splitlines() if s.startswith('FAIL C')]
        if not failed: raise SystemExit('UNRELATED_INFRA_FAILURE '+name+'\n'+result.stdout+result.stderr)
        print('CAUGHT',name,'::',failed[0])
print(f'TOTAL {len(mutants)} MUTANTS CAUGHT')
