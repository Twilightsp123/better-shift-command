"""T2-MOVE-E isolated active adoption integration structural contract."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
src=(R/"source/better_shift_command.lua").read_text()
mir=(R/"src/better_shift_command.lua").read_text()
tpl=(R/"src/better_shift_command_selfcontained.template.lua").read_text()
assert src==mir,"mirrors diverged"
for name,s in (("source",src),("template",tpl)):
    for needle in ("T2MOVE_D_EVIDENCE_MODULE_BEGIN","T2MOVE_E_POLICY_MODULE_BEGIN",
        "function R1.T2MoveEPreview(st,current,successor,ctx)",
        "R1.T2MoveEvidence.revalidate(cached,query)",
        "R1.T2MoveA.capture({","R1.T2MoveB.preview(R1.T2MoveA,a,",
        'd.adopt_window=transition_envelope(false,"CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)',
        'd.adopt_window=transition_envelope(true,proof.reason,false)',
        "move_native_reconcile=true,move_native_evidence=proof,model_ms=now",
        "R1.observe_t2move_d(st,cur,now)","function Core.commit_transition_edge(st,tx,now,opts)"):
        assert needle in s,(name,"missing",needle)
    assert "NATIVE_MOVE_PASSTHROUGH" not in s
    assert s.count("R1.TransitionPolicy.evaluate(st,")==10,(name,"evaluator count")
    evaluator=s.split("function R1.TransitionPolicy.evaluate(st,current,successor,g,context)",1)[1].split("local function attack_metrics",1)[0]
    assert evaluator.index("if current_index and successor_index and successor_index~=current_index+1 then")<evaluator.index("context.move_native_reconcile==true")
    # The active method must not reopen proactive Move issue or use the post-promotion geometry route_handoff_ready path.
    e=evaluator.split("if successor.type==\"MOVE\" and context.move_native_reconcile==true then",1)[1].split("if not g then",1)[0]
    assert 'd.issue_window=transition_envelope(false,"NATIVE_MOVE_ALREADY_ACTIVE",false)' in e
    assert 'route_handoff_ready' not in e
    reconcile=s.split("function Core.reconcile_native_successor(st,now)",1)[1].split("local function advance(st,now)",1)[0]
    assert reconcile.index("if future_index==st.idx+1 and future.type==\"ATTACK\"")<reconcile.index('elseif future_index==st.idx+1 and future.type=="MOVE"')
    assert 'g=proof and transition_geometry_snapshot(proof.geometry) or nil' in reconcile
    assert 'Core.begin_transition_txn(st,cur,future,commit_reason,now,g,"NATIVE_RECONCILE")' in reconcile
    assert 'tx.state="OBSERVED"' in reconcile
    assert 'Core.commit_transition_edge(st,tx,now' in reconcile
print("PASS: E isolated MOVE adopt uses frozen A/B/D policy and existing T1.6 commit, i+2 hard")
