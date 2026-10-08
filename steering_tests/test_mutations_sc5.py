"""SC5 Exit-reassert mutation suite. Every deliberately broken invariant must be caught."""
from pathlib import Path
import shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def lua_cmd():
    for n in ('lua5.1','texlua','lua5.3','lua'):
        p=shutil.which(n)
        if p:return [p]
    p=shutil.which('luatex')
    return [p,'--luaonly'] if p else None
LUA=lua_cmd()
if not LUA:raise SystemExit('A Lua interpreter is required')
module=(ROOT/'source/fresh_engagement_gate.lua').read_text()
controller=(ROOT/'source/better_shift_command.lua').read_text()
# H2 route-integrity supersedes early SC1/SC2/SC4 steering permission as a
# gameplay requirement. Those 8 historical mutation expectations are preserved
# on the immutable H1/G baselines, not used to demand premature waypoint credit.
# Active H2 mutation coverage is in test_t2move_h2bcd_mutations.py.
mutants=[
 ('attack_accepts_predictive_route_debt',controller,'local clear=block_route_clear(st,current)','local clear=true -- mutant ignores prior route debt','t2b_contract'),
 ('disable_sc3_soft_debt',controller,'local soft_ok,soft_reason=move_route_debt_soft_continue(st,cur,nexta,g)','local soft_ok,soft_reason=false,\"MUTANT_HARD_DEBT\"','blocks'),
 ('disable_sc5_corepath_positive_contact_fallback',controller,'required_stall=CFG.exit_contact_fallback_stall_ms\n            confirmed_candidate=contact_fresh\n            evidence_mode="COREPATH_POSITIVE_CONTACT_FALLBACK"','required_stall=CFG.exit_contact_fallback_stall_ms\n            confirmed_candidate=false\n            evidence_mode="MUTANT_COREPATH_FALLBACK_DISABLED"','blocks'),
 ('sc5_stale_v3_fallback_waits_too_long',controller,'exit_contact_fallback_stall_ms=900','exit_contact_fallback_stall_ms=5000','blocks'),
 ('remove_idle_finish_confirmation',controller,'if now-c.since>=CFG.move_idle_finish_confirm_ms then','if now-c.since>=0 then','blocks'),
 ('restore_four_unit_batching',controller,'max_inflight=32','max_inflight=4','contracts'),
 ('single_move_boolean_urgency',controller,'if not nexta then\n        if rt.semantic_done then return -100,"MOVE_COMPLETE_NO_SUCCESSOR" end\n        return BSC_HUGE,"NO_SUCCESSOR"\n    end','if not nexta then return rt.semantic_done and -100,"MOVE_COMPLETE_NO_SUCCESSOR" or BSC_HUGE,"NO_SUCCESSOR" end','contracts'),
 ('routing_means_dead',controller,'local function target_viable(a)','local function target_viable(a)\n    if a.target and api_bool(a.target,"is_routing")==true then return false,"TARGET_DEAD" end','regressions'),
 ('remove_death_confirmation',controller,'if now-a.end_since>=CFG.target_end_confirm_ms then return false,why end','if true then return false,why end','regressions'),
 ('drop_no_tail_attack_latch',controller,'if not t.done then\n            t.done=true','if not t.done then\n            -- mutant: t.done latch removed','blocks'),
 ('remove_geometry_bbox',module,'and target_consistent and bbox_ok','and target_consistent and true','gate_compat'),
 ('remove_geometry_target_identity',module,'s.target_alive==true and target_consistent','s.target_alive==true and true','gate_compat'),
 ('remove_geometry_alive',module,'s.target_alive==true and target_consistent','true and target_consistent','gate_compat'),
 ('remove_geometry_dwell',module,'g.geometry_ms>=c.geometry_confirm_ms','g.geometry_ms>=0','gate_compat'),
 ('unbounded_strong_melee_envelope',module,'local strong_far=radius+c.far_margin_m+math.min(c.strong_extra_cap_m,width_sum*c.strong_width_factor)','local strong_far=1000000','gate_v104'),
 ('strong_melee_without_bbox',module,'local raw_extended=raw and bbox_ok and distance<=g.strong_far','local raw_extended=raw and distance<=g.strong_far','gate_v104'),
 ('disable_halt_queue_reset',controller,'local reset_good=reset and id(reset.revision) and r.unit_revision==inc(reset.revision)','local reset_good=false','v107'),
 ('source_target_death_completes_exit',controller,'if ok and men==0 then b.source_ended_logged=true;', 'if ok and men==0 then b.exit_permission=true;b.permission_ms=now;mark_exit_committed(st,b,"MUTANT_SOURCE_DEAD",now,0,nil,0);return end;if ok and men==0 then b.source_ended_logged=true;','v107'),
 # The former mutation expecting skipped final waypoints was itself a requirement
 # regression. Keep the original in history and test its INVERSE against R04.
 ('erase_final_exit_route',controller,'local clear=block_route_clear(st,a)\n    return rt.semantic_done==true and clear==true','local clear=block_route_clear(st,a)\n    rt.semantic_done=true -- mutant erases final Exit route\n    return true','v109'),
 ('stop_observing_after_first_clear',controller,'if not b or b.closed or not b.exit_started_ms or not st.pos then return end','if not b or b.closed or b.exit_committed or not b.exit_started_ms or not st.pos then return end','v109'),
 ('recovery_missing_with_move_successor',controller,'function Core.maintain_current_action(st,now)','function Core.maintain_current_action(st,now)\n if st.plan and st.plan[st.idx+1] and st.plan[st.idx+1].type=="MOVE" then return end','v109'),
 ('recovery_missing_with_invalid_successor',controller,'function Core.maintain_current_action(st,now)','function Core.maintain_current_action(st,now)\n if st.plan and st.plan[st.idx+1] and st.plan[st.idx+1].type=="ATTACK" and not target_viable(st.plan[st.idx+1]) then return end','v109'),
 ('unknown_enemy_assumed_absent',controller,'-- Hidden/entering/leaving/unmeasurable is not proof of absence.\n                unknown=true','-- mutant excludes a hidden enemy\n                unknown=false','v109'),
 ('center_entity_evidence_regains_veto',controller,'if CENTER_A2_MODE and code=="BLOCKED_EVIDENCE" then','if false and CENTER_A2_MODE and code=="BLOCKED_EVIDENCE" then','center_b2'),
 ('disable_attack_execution_reassert',controller,'if Core.reassert_current_attack(st,"ATTACK_REASSERT_NO_EXECUTION",now) then return end','if false and Core.reassert_current_attack(st,"ATTACK_REASSERT_NO_EXECUTION",now) then return end','center_b2'),
 ('unbound_attack_execution_reassert',controller,'attack_reassert_max=2','attack_reassert_max=99','center_b2'),
 ('route_debt_back_to_fixed_wallclock',controller,'local no_progress=now-(debt.last_progress_ms or debt.since or now)','local no_progress=now-(debt.last_progress_ms or debt.since or now)\n            if no_progress>=2000 then debt.stall_remaining=remaining;debt.stall_no_progress_ms=no_progress;return debt end','center_b2'),
 ('ordinary_attack_globally_depends_on_entity_v2',controller,'local eligible=r.allow -- ordinary Attack keeps mature FEG behavior.','local eligible=r.allow and R1.entity(st,now)~=nil -- mutant global dependency','v109'),
 ('disable_center_a2_mode',controller,'local CENTER_A2_MODE = true','local CENTER_A2_MODE = false','center_b2'),
 ('sc6_reconciliation_forced_back_to_v2',controller,'if v3.execution_identity==true then','if false and v3.execution_identity==true then','sc6'),
 ('sc6_ignore_execution_sequence',controller,'if e.active_engine_seq~=seq then return false,"EXECUTION_SEQUENCE_MISMATCH",lineage end','if false and e.active_engine_seq~=seq then return false,"EXECUTION_SEQUENCE_MISMATCH",lineage end','sc6'),
 ('t1_advance_bypass_shared_evaluator',controller,'local decision=R1.TransitionPolicy.evaluate(st,cur,nexta,g,{current_index=st.idx,successor_index=st.idx+1})\n        local route_ok,route_reason=decision.route_ok,decision.route_reason or decision.reason\n        g.current_credit=decision.current_credit','local decision={route_ok=true,route_reason="MUTANT",current_credit=nil,issue_window={open=true,reason="MUTANT"},adopt_window={open=true,reason="MUTANT"}}\n        local route_ok,route_reason=decision.route_ok,decision.route_reason or decision.reason\n        g.current_credit=decision.current_credit','t1_contract'),
 ('t1_sc6_cache_bypass_shared_evaluator',controller,'local cd=R1.TransitionPolicy.evaluate(st,cur,nexta,cg,{current_index=st.idx,successor_index=st.idx+1,target_terminal_abort=terminal_abort});cg.current_credit=cd.current_credit','local cd={route_ok=true,current_credit="MUTANT",issue_window={open=true},adopt_window={open=true}};cg.current_credit=cd.current_credit','t1_contract'),
 ('t1_sc6_bypass_shared_evaluator',controller,'decision=R1.TransitionPolicy.evaluate(st,cur,future,g,{current_index=st.idx,successor_index=future_index,execution_lineage=future_lineage,target_terminal_abort=terminal_abort})','decision={adopt_window={open=false,hard_violation=true,reason="MUTANT"}}','t1_contract'),
 ('t1_scheduler_bypass_shared_evaluator',controller,'local decision=R1.TransitionPolicy.evaluate(st,cur,nexta,g,{current_index=st.idx,successor_index=st.idx+1})\n        if not exit_gate_ready(st,nexta) then return 50000,"EXIT_BLOCK_PROTECT" end','local decision={route_ok=true,current_credit="MUTANT",issue_window={open=true,reason="MUTANT"},adopt_window={open=true,reason="MUTANT"}}\n        if not exit_gate_ready(st,nexta) then return 50000,"EXIT_BLOCK_PROTECT" end','t1_contract'),
 ('t1_h2_allows_future_skip',controller,'if current_index and successor_index and successor_index~=current_index+1 then','if false and current_index and successor_index and successor_index~=current_index+1 then','t1_contract'),
]
suite_map={'center_b2':'test_center_phase_b2.lua','blocks':'test_v104_blocks.lua','contracts':'test_contracts_v104.lua','regressions':'test_regressions_v104.lua','v107':'test_v107_regressions.lua','v109':'test_v109_regressions.lua','second_charge':'test_r1_v3_second_charge.lua','gate':'test_gate.lua','gate_compat':'test_gate_v103.lua','gate_v104':'test_gate_v104.lua','sc6':'test_exec_identity_v3.lua'}
for kind in sorted(set(x[4] for x in mutants)):
    if kind=='t1_contract':
        args=[shutil.which('python') or shutil.which('python3'),'tests/test_transition_policy_t1_contract.py']
    elif kind=='t2b_contract':
        args=[shutil.which('python') or shutil.which('python3'),'tests/test_t2b_attack_handoff_contract.py']
    else:
        args=LUA+[str(ROOT/'tests'/suite_map[kind]),str(ROOT/'source'/('fresh_engagement_gate.lua' if kind.startswith('gate') else 'better_shift_command.lua'))]
        if not kind.startswith('gate'):args.append(str(ROOT/'tests/fixture.lua'))
    base=subprocess.run(args,capture_output=True,text=True,cwd=ROOT)
    if base.returncode:raise SystemExit('BASELINE DID NOT PASS: '+kind+'\n'+base.stdout+base.stderr)
for name,src,before,after,kind in mutants:
    assert before in src,name
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'mutant.lua';p.write_text(src.replace(before,after,1))
        if kind=='t1_contract':
            args=[shutil.which('python') or shutil.which('python3'),str(ROOT/'tests/test_transition_policy_t1_contract.py'),str(p)]
        elif kind=='t2b_contract':
            args=[shutil.which('python') or shutil.which('python3'),str(ROOT/'tests/test_t2b_attack_handoff_contract.py'),str(p)]
        elif kind in ('gate','gate_compat','gate_v104'):
            script={'gate':'test_gate.lua','gate_compat':'test_gate_v103.lua','gate_v104':'test_gate_v104.lua','sc6':'test_exec_identity_v3.lua'}[kind];args=LUA+[str(ROOT/'tests'/script),str(p)]
        else:
            script={'center_b2':'test_center_phase_b2.lua','blocks':'test_v104_blocks.lua','contracts':'test_contracts_v104.lua','regressions':'test_regressions_v104.lua','v107':'test_v107_regressions.lua','v109':'test_v109_regressions.lua','second_charge':'test_r1_v3_second_charge.lua','sc6':'test_exec_identity_v3.lua'}[kind]
            args=LUA+[str(ROOT/'tests'/script),str(p),str(ROOT/'tests/fixture.lua')]
        r=subprocess.run(args,capture_output=True,text=True,cwd=ROOT)
        if r.returncode==0:raise SystemExit('MUTANT SURVIVED: '+name)
        failed=[line for line in r.stdout.splitlines() if line.startswith('FAIL ')]
        if not failed:raise SystemExit('Infrastructure failure, not a caught mutant: '+name+'\n'+r.stdout+r.stderr)
        print('CAUGHT '+name+' :: '+failed[0])
print(f'TOTAL {len(mutants)} MUTANTS CAUGHT; native Bridge has independent C++ tests')
