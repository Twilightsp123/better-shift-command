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
mutants=[
 ('disable_t2b_terminal_corridor',controller,'if (g.remaining or BSC_HUGE)>(g.threshold or 0) then','if true or (g.remaining or BSC_HUGE)>(g.threshold or 0) then','t2b'),
 ('remove_t2b_short_leg_progress_guard',controller,'if (g.leg or 0)<60 and (g.leg or 0)>0.001 then','if false and (g.leg or 0)<60 and (g.leg or 0)>0.001 then','blocks'),
 ('passthrough_disable_native_queue_ownership',controller,'return st and st.move_owner=="NATIVE_QUEUE" and st.owned~=true','return false','passthrough'),
 ('passthrough_reenable_proactive_move_dispatch',controller,'if nexta and nexta.type=="MOVE" and native_move_passthrough_owned(st) then\n        st.phase="NATIVE_MOVE_PASSTHROUGH"\n        return\n    end','if false and nexta and nexta.type=="MOVE" and native_move_passthrough_owned(st) then\n        return\n    end','passthrough'),
 ('passthrough_disable_move_shadow_sync',controller,'if native_passthrough and future.type=="MOVE" then','if false and native_passthrough and future.type=="MOVE" then','passthrough'),
 ('passthrough_cross_semantic_boundary',controller,'local function native_move_passthrough_range(st,from_i,to_i)\n    if not st or not st.plan then return false,"NO_PLAN" end','local function native_move_passthrough_range(st,from_i,to_i)\n    if st and st.plan then return true,"MUTANT_CROSS_SEMANTIC" end\n    if not st or not st.plan then return false,"NO_PLAN" end','passthrough'),
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
 ('erase_final_exit_route',controller,'local function transition_handoff_ready(st,g,nexta)\n    -- R04/R07: exit evidence never erases ANY Move, including the final one.\n    local route_ok,why=route_handoff_ready(st,g,nexta)','local function transition_handoff_ready(st,g,nexta)\n    -- mutant: erase final Exit route\n    local route_ok,why=true,"MUTANT_SKIP_ROUTE";action_runtime(st.plan[st.idx]).semantic_done=true','v109'),
 ('stop_observing_after_first_clear',controller,'if not b or b.closed or not b.exit_started_ms or not st.pos then return end','if not b or b.closed or b.exit_committed or not b.exit_started_ms or not st.pos then return end','v109'),
 ('recovery_missing_with_move_successor',controller,'function Core.maintain_current_action(st,now)','function Core.maintain_current_action(st,now)\n if st.plan and st.plan[st.idx+1] and st.plan[st.idx+1].type=="MOVE" then return end','v109'),
 ('recovery_missing_with_invalid_successor',controller,'function Core.maintain_current_action(st,now)','function Core.maintain_current_action(st,now)\n if st.plan and st.plan[st.idx+1] and st.plan[st.idx+1].type=="ATTACK" and not target_viable(st.plan[st.idx+1]) then return end','v109'),
 ('unknown_enemy_assumed_absent',controller,'-- Hidden/entering/leaving/unmeasurable is not proof of absence.\n                unknown=true','-- mutant excludes a hidden enemy\n                unknown=false','v109'),
 ('center_entity_evidence_regains_veto',controller,'if CENTER_A2_MODE and code=="BLOCKED_EVIDENCE" then','if false and CENTER_A2_MODE and code=="BLOCKED_EVIDENCE" then','center_b2'),
 ('disable_attack_execution_reassert',controller,'if Core.reassert_current_attack(st,"ATTACK_REASSERT_NO_EXECUTION",now) then return end','if false and Core.reassert_current_attack(st,"ATTACK_REASSERT_NO_EXECUTION",now) then return end','center_b2'),
 ('unbound_attack_execution_reassert',controller,'attack_reassert_max=2','attack_reassert_max=99','center_b2'),
 ('ordinary_attack_globally_depends_on_entity_v2',controller,'local eligible=r.allow -- ordinary Attack keeps mature FEG behavior.','local eligible=r.allow and R1.entity(st,now)~=nil -- mutant global dependency','v109'),
 ('disable_center_a2_mode',controller,'local CENTER_A2_MODE = true','local CENTER_A2_MODE = false','center_b2'),
 ('sc6_reconciliation_forced_back_to_v2',controller,'if v3.execution_identity==true then','if false and v3.execution_identity==true then','sc6'),
 ('sc6_ignore_execution_sequence',controller,'if e.active_engine_seq~=seq then return false,"EXECUTION_SEQUENCE_MISMATCH" end','if false and e.active_engine_seq~=seq then return false,"EXECUTION_SEQUENCE_MISMATCH" end','sc6'),
]
suite_map={'passthrough':'test_native_move_passthrough.lua','t2b':'test_tpol_t2b_shift_attack.lua','center_b2':'test_center_phase_b2.lua','blocks':'test_v104_blocks.lua','contracts':'test_contracts_v104.lua','regressions':'test_regressions_v104.lua','v107':'test_v107_regressions.lua','v109':'test_v109_regressions.lua','second_charge':'test_r1_v3_second_charge.lua','gate':'test_gate.lua','gate_compat':'test_gate_v103.lua','gate_v104':'test_gate_v104.lua','sc6':'test_exec_identity_v3.lua'}
for kind in sorted(set(x[4] for x in mutants)):
    args=LUA+[str(ROOT/'tests'/suite_map[kind]),str(ROOT/'source'/('fresh_engagement_gate.lua' if kind.startswith('gate') else 'better_shift_command.lua'))]
    if not kind.startswith('gate'):args.append(str(ROOT/'tests/fixture.lua'))
    base=subprocess.run(args,capture_output=True,text=True,cwd=ROOT)
    if base.returncode:raise SystemExit('BASELINE DID NOT PASS: '+kind+'\n'+base.stdout+base.stderr)
for name,src,before,after,kind in mutants:
    assert before in src,name
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'mutant.lua';p.write_text(src.replace(before,after,1))
        if kind in ('gate','gate_compat','gate_v104'):
            script={'gate':'test_gate.lua','gate_compat':'test_gate_v103.lua','gate_v104':'test_gate_v104.lua','sc6':'test_exec_identity_v3.lua'}[kind];args=LUA+[str(ROOT/'tests'/script),str(p)]
        else:
            script={'passthrough':'test_native_move_passthrough.lua','t2b':'test_tpol_t2b_shift_attack.lua','center_b2':'test_center_phase_b2.lua','blocks':'test_v104_blocks.lua','contracts':'test_contracts_v104.lua','regressions':'test_regressions_v104.lua','v107':'test_v107_regressions.lua','v109':'test_v109_regressions.lua','second_charge':'test_r1_v3_second_charge.lua','sc6':'test_exec_identity_v3.lua'}[kind]
            args=LUA+[str(ROOT/'tests'/script),str(p),str(ROOT/'tests/fixture.lua')]
        r=subprocess.run(args,capture_output=True,text=True,cwd=ROOT)
        if r.returncode==0:raise SystemExit('MUTANT SURVIVED: '+name)
        failed=[line for line in r.stdout.splitlines() if line.startswith('FAIL ')]
        if not failed:raise SystemExit('Infrastructure failure, not a caught mutant: '+name+'\n'+r.stdout+r.stderr)
        print('CAUGHT '+name+' :: '+failed[0])
print(f'TOTAL {len(mutants)} MUTANTS CAUGHT; native Bridge has independent C++ tests')
