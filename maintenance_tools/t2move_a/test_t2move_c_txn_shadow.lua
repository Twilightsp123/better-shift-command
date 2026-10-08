local A=assert(loadfile(assert(arg[1])))()
local B=assert(loadfile(assert(arg[2])))()
local C=assert(loadfile(assert(arg[3])))()
local pass=0
local function T(n,fn)
    local ok,e=pcall(fn)
    if not ok then print("FAIL "..n.." :: "..tostring(e));os.exit(1) end
    pass=pass+1;print("PASS "..n)
end
local function fixture(mode, issue_open)
    mode=mode or "PATH_SAFE"
    local cur={type="MOVE",action_id="100"}
    local fut={type="MOVE",action_id="101"}
    local st={gen="9",revision="7",prior_debt_signature="B1",idx=1,plan={cur,fut},
        prior_debts={"B1"},registered={},completed={},transition_txn=nil}
    local g={remaining=46,threshold=42,stall=false,leg=100,next_leg=90,
        progress=0.54,route_min_progress=0.2,route_mode=mode,
        route_debt_mode="CLEAR",route_debt_count=0,arrival_sync_margin=5,arrival_brake_ready=true,
        cut_error=0.5,cut_safe_limit=1,cut_tolerance=5,
        corner_window=50,corner_window_base=50,corner_window_early=30,corner_stall_escape=false}
    local reason=mode=="STEERING_CORNER" and "TURN_CORRIDOR_ENTERED" or "PATH_DEVIATION_SAFE_WITH_MARGIN"
    local frame={exact_current_execution=true,gen="9",unit_lifetime="1",current_action_id="100",
        successor_action_id="101",current_index=1,successor_index=2,current_kind="MOVE",successor_kind="MOVE",
        sample_ms=500,poll_ms=100,semantic_done=false,
        decision={transition_kind="MOVE->MOVE",route_ok=true,hard_violation=false,
            route_reason=reason,issue_window={open=issue_open==true}},geometry=g}
    local evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5}
    local timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}
    local q={exact_native_successor=true,gen="9",unit_lifetime="1",current_action_id="100",
        successor_action_id="101",current_index=1,future_index=2,now_ms=600,observed_step_ms=100,
        execution_lineage="PLAYER_NATIVE"}
    local cache,why=C.capture(A,{state=st,action_current=cur,action_next=fut,
        event=frame,evidence=evidence,timing=timing})
    assert(cache,why)
    return st,cache,q,frame,evidence
end
local function fake_core(opts)
    opts=opts or {}
    local core={calls={},}
    function core.begin_transition_txn(st,cur,fut,reason,now,g,source)
        core.calls[#core.calls+1]="begin"
        if opts.refuse_begin then return nil end
        local tx={state="AUTHORIZED",gen=st.gen,current_idx=st.idx,successor_idx=st.idx+1,
            current=cur,successor=fut,geometry=g,source=source,reason=reason}
        if opts.bad_transaction then tx.successor_idx=st.idx+2 end
        st.transition_txn=tx;return tx
    end
    function core.abort_transition_txn(st,tx,reason,now)
        core.calls[#core.calls+1]="abort";tx.state="ABORTED";st.transition_txn=nil;return true
    end
    function core.commit_transition_edge(st,tx,now,options)
        core.calls[#core.calls+1]="commit"
        if opts.reject_commit then return false end
        assert(tx.state=="OBSERVED" and tx.source=="NATIVE_RECONCILE")
        assert(tx.current_idx==st.idx and tx.successor_idx==st.idx+1)
        assert(tx.geometry.route_debt_mode=="CLEAR" or tx.geometry.route_debt_mode=="SOFT_PRESERVED")
        if not opts.semantic_done then
            if tx.geometry.route_mode=="STEERING_CORNER" then
                st.completed[#st.completed+1]="STEERING_CORNER_HANDOFF"
            else
                st.registered[#st.registered+1]="CURRENT_WAYPOINT_OWED"
            end
        end
        st.idx=tx.successor_idx;st.execution_lane=options.execution_lane
        tx.state="COMMITTED";st.transition_txn=nil
        return true
    end
    return core
end
local function simulate(st,cache,q,opts)
    local core=fake_core(opts)
    local result=C.simulate_observed(A,B,core,st,cache,q)
    return result,core
end
T("C00 A/B ADOPT_ONLY -> T1.6 OBSERVED -> COMMITTED",function()
    local s,c,q=fixture();local r,k=simulate(s,c,q)
    assert(r.allow and r.zone=="ADOPT_ONLY" and r.transaction_state=="COMMITTED")
    assert(r.authoritative==false and r.simulated and s.idx==2 and #s.registered==1)
    assert(table.concat(k.calls,",")=="begin,commit")
end)
T("C01 steering corner has exactly one completion credit",function()
    local s,c,q=fixture("STEERING_CORNER");local r=simulate(s,c,q)
    assert(r.allow and r.credit=="STEERING_CORNER_HANDOFF")
    assert(#s.completed==1 and #s.registered==0 and s.idx==2)
end)
T("C02 Stage A ISSUE_READY also uses same T1.6 commit",function()
    local s,c,q=fixture("PATH_SAFE",true);local r=simulate(s,c,q)
    assert(r.allow and r.zone=="ISSUE_READY" and #s.registered==1)
end)
T("C03 reject before observed => no cursor / credit",function()
    local s,c,q=fixture();local r,k=simulate(s,c,q,{refuse_begin=true})
    assert(not r.allow and s.idx==1 and #s.completed==0 and #s.registered==0)
    assert(table.concat(k.calls,",")=="begin")
end)
T("C04 failed commit aborts, no credit",function()
    local s,c,q=fixture();local r,k=simulate(s,c,q,{reject_commit=true})
    assert(not r.allow and s.idx==1 and #s.registered==0 and s.transition_txn==nil)
    assert(table.concat(k.calls,",")=="begin,commit,abort")
end)
T("C05 malformed begin tx fails closed",function()
    local s,c,q=fixture();local r,k=simulate(s,c,q,{bad_transaction=true})
    assert(not r.allow and s.idx==1 and #s.registered==0 and s.transition_txn==nil)
    assert(table.concat(k.calls,",")=="begin,abort")
end)
T("C06 wrong generation blocks without invoking T1.6",function()
    local s,c,q=fixture();s.gen="10";local r,k=simulate(s,c,q)
    assert(not r.allow and r.reason=="PLAN_GENERATION_OR_REVISION_CHANGED" and #k.calls==0 and s.idx==1)
end)
T("C07 journal/canonical revision change blocks",function()
    local s,c,q=fixture();s.revision="8";local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0 and s.idx==1)
end)
T("C08 prior route-debt signature change blocks",function()
    local s,c,q=fixture();s.prior_debt_signature="B2";local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0 and #s.registered==0)
end)
T("C09 replacement current action blocks",function()
    local s,c,q=fixture();s.plan[1]={type="MOVE",action_id="100"};local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C10 replacement successor action blocks",function()
    local s,c,q=fixture();s.plan[2]={type="MOVE",action_id="101"};local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C11 Native i+2 overrun remains hard block",function()
    local s,c,q=fixture();q.future_index=3;local r,k=simulate(s,c,q)
    assert(not r.allow and r.reason=="NATIVE_FUTURE_NOT_IMMEDIATE" and r.zone=="HARD_BLOCK" and #k.calls==0)
end)
T("C12 stale one-poll cache cannot cause T1.6 begin",function()
    local s,c,q=fixture();q.now_ms=601;local r,k=simulate(s,c,q)
    assert(not r.allow and r.reason=="CACHE_OUTSIDE_ONE_ACTUAL_POLL" and #k.calls==0)
end)
T("C13 wrong lifetime/active execution blocks",function()
    local s,c,q=fixture();q.unit_lifetime="2";local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
    s,c,q=fixture();q.exact_native_successor=false;r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C14 already outstanding T1.6 transaction blocks",function()
    local s,c,q=fixture();s.transition_txn={state="SUBMITTED"};local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C15 pending dispatch blocks, avoiding double-issued successor",function()
    local s,c,q=fixture();s.pending_by_uid=true;local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C16 SC3 debt is preserved by T1.6 commit",function()
    local s,c,q,f=fixture();f.geometry.route_debt_mode="SOFT_PRESERVED";f.geometry.route_debt_count=1
    f.geometry.route_debt_error=1;f.geometry.route_debt_limit=2
    c=assert(C.capture(A,{state=s,action_current=s.plan[1],action_next=s.plan[2],event=f,
        evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5},
        timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}}))
    local old_debt=s.prior_debts[1];local r=simulate(s,c,q)
    assert(r.allow and r.preserve_prior_debt and s.prior_debts[1]==old_debt)
    assert(#s.registered==1)
end)
T("C17 wrong execution lineage blocks",function()
    local s,c,q=fixture();q.execution_lineage="UNKNOWN";local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0)
end)
T("C18 old frame geometry mutation cannot widen adopt",function()
    local s,c,q,f=fixture();f.geometry.remaining=80;f.geometry.corner_window=200
    local r,k=simulate(s,c,q);assert(r.allow and #k.calls==2)
end)
T("C19 missing mandatory real snapshot field blocks capture",function()
    local s,c,q,f=fixture();f.geometry.route_min_progress=nil
    local rec,why=C.capture(A,{state=s,action_current=s.plan[1],action_next=s.plan[2],event=f,
        evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5},
        timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}})
    assert(rec==nil and why=="MOVE_SNAPSHOT_MISSING_route_min_progress")
end)
T("C20 missing route-mode field blocks capture",function()
    local s,c,q,f=fixture("STEERING_CORNER");f.geometry.corner_window=nil
    local rec,why=C.capture(A,{state=s,action_current=s.plan[1],action_next=s.plan[2],event=f,
        evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5},
        timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}})
    assert(rec==nil and why=="MOVE_SNAPSHOT_MISSING_corner_window")
end)
T("C21 incomplete G1 sample blocks adopt",function()
    local s,c,q,f=fixture();f.geometry.arrival_brake_ready=false
    c=assert(C.capture(A,{state=s,action_current=s.plan[1],action_next=s.plan[2],event=f,
        evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5},
        timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}}))
    local r,k=simulate(s,c,q);assert(not r.allow and r.reason=="G1_ONE_POLL_MEASUREMENT_MISMATCH" and #k.calls==0)
end)
T("C22 hard route debt blocks capture",function()
    local s,c,q,f=fixture();f.geometry.route_debt_mode="HARD"
    local rec,why=C.capture(A,{state=s,action_current=s.plan[1],action_next=s.plan[2],event=f,
        evidence={previous_sample_ms=400,current_sample_ms=500,previous_remaining=51,current_remaining=46,ground_distance=5},
        timing={proximity=1,stall_distance=8,lead_cap=70,brake_extra=3}})
    assert(rec==nil and why=="CURRENT_ROUTE_DEBT_HARD")
end)
T("C23 preview cannot issue a Native order",function()
    local s,c,q=fixture();local r,k=simulate(s,c,q)
    assert(r.simulated and not r.authoritative and k.issue_verified_command==nil)
end)
T("C24 fallback denial never itself reasserts current MOVE",function()
    local s,c,q=fixture();q.now_ms=700;local r,k=simulate(s,c,q)
    assert(not r.allow and #k.calls==0 and s.idx==1)
end)
print("TOTAL "..pass.." PASS 0 FAIL; SIMULATED T1.6 TRANSACTION ONLY")
