"""T2-MOVE-D positive real-controller mapping and zero-permission contract."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
controller=(ROOT/'source/better_shift_command.lua').read_text()
mirror=(ROOT/'src/better_shift_command.lua').read_text()
template=(ROOT/'src/better_shift_command_selfcontained.template.lua').read_text()
assert controller==mirror,'controller mirrors diverged'
fields={'remaining','leg','next_leg','progress','route_min_progress','threshold','stall','route_mode','route_debt_mode',
'arrival_brake_ready','arrival_sync_margin','cut_error','cut_safe_limit','cut_tolerance','corner_window','corner_window_base','corner_window_early','corner_stall_escape'}
for name,s in [('source',controller),('template',template)]:
 a='local function transition_geometry_snapshot(g)'
 b='function Core.begin_transition_txn('
 assert s.count(a)==1 and s.count(b)==1,(name,'snapshot anchors')
 block=s.split(a,1)[1].split(b,1)[0]
 pairs=set(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*g\.([A-Za-z_][A-Za-z0-9_]*)',block))
 mapped={x for x,y in pairs if x==y}
 missing=fields-mapped
 assert not missing,(name,'snapshot missing',sorted(missing))
 assert s.count('T2MOVE_D_EVIDENCE_MODULE_BEGIN')==1,(name,'D module')
 assert s.count('function R1.observe_t2move_d(st,cur,now)')==1,(name,'observer missing')
 assert s.count('R1.observe_t2move_d(st,cur,now)')==2,(name,'observation def+call required')
 assert 'd.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)' in s,(name,'MOVE permission widened')
 assert 'NATIVE_MOVE_PASSTHROUGH' not in s
 assert s.count('R1.TransitionPolicy.evaluate(st,')==10,(name,'E shared evaluator site count')
 assert 'st.t2move_d_evidence=nil' in s
 observer=s.split('function R1.observe_t2move_d(st,cur,now)',1)[1].split('function Core.reconcile_native_successor',1)[0]
 assert 'R1.TransitionPolicy.evaluate' in observer
 assert 'R1.T2MoveEvidence.route_debt_signature' in observer
 assert 'R1.T2MoveEvidence.capture' in observer
 for forbidden in ('Core.begin_transition_txn','Core.commit_transition_edge','dispatch(st','st.idx=','issue_verified_command'):
  assert forbidden not in observer,(name,'shadow mutates gameplay',forbidden)
reconcile=controller.split('function Core.reconcile_native_successor(st,now)',1)[1].split('local function advance(st,now)',1)[0]
assert reconcile.index('if current_match then')<reconcile.index('R1.observe_t2move_d(st,cur,now)')
assert 'if decision.hard_violation or adopt_window.hard_violation then' in reconcile
assert controller.count('T2B_G11_DUAL_ENVELOPE_CANDIDATE')>=1
print('PASS: T2-MOVE-D field mapping intact inside isolated E candidate')
