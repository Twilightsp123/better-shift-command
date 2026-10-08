-- BSC T2-MOVE-C transaction integration simulation.
-- Research-only: this module is NOT loaded by the live controller.
-- No Native API, no Command.issue, no commit without a trusted mock Core.
local C = {VERSION="T2MOVE_C_TXN_SHADOW_1", authoritative=false}
local huge=math.huge or 1e300
local function finite(n) return type(n)=="number" and n==n and n<huge and n>-huge end
local function scalar(v) return type(v)=="string" or (finite(v) and v>=0) end
local function copy_scalars(t)
    local out={}
    if type(t)=="table" then
        for k,v in pairs(t) do
            if type(k)=="string" and (type(v)=="string" or type(v)=="boolean" or finite(v)) then out[k]=v end
        end
    end
    return out
end
local required_geom={
    "remaining","leg","next_leg","progress","route_min_progress","threshold","stall",
    "route_mode","route_debt_mode","arrival_brake_ready","arrival_sync_margin"
}
local mode_fields={
    PATH_SAFE={"cut_error","cut_safe_limit","cut_tolerance"},
    STEERING_CORNER={"corner_window","corner_window_base","corner_window_early"}
}
C.REQUIRED_GEOMETRY=required_geom
C.MODE_FIELDS=mode_fields
local function deny(reason,hard)
    return {allow=false,zone=hard and "HARD_BLOCK" or "WAIT",reason=reason,authoritative=false}
end
local function has_fields(g,mode)
    if type(g)~="table" then return false,"GEOMETRY_MISSING" end
    for _,name in ipairs(required_geom) do
        if g[name]==nil then return false,"MOVE_SNAPSHOT_MISSING_"..name end
    end
    for _,name in ipairs(mode_fields[mode] or {}) do
        if g[name]==nil then return false,"MOVE_SNAPSHOT_MISSING_"..name end
    end
    if g.route_debt_mode=="SOFT_PRESERVED" then
        for _,name in ipairs({"route_debt_count","route_debt_error","route_debt_limit"}) do
            if g[name]==nil then return false,"MOVE_SNAPSHOT_MISSING_"..name end
        end
    end
    return true,"OK"
end
-- Must be called while native EXACT current MOVE execution remains observed.
-- Current canonical plan/revision and route-debt identity are bound alongside A/B.
function C.capture(A,input)
    if type(input)~="table" or type(input.action_current)~="table" or type(input.action_next)~="table"
        or type(input.state)~="table" or type(input.evidence)~="table"
        or type(input.timing)~="table" then return nil,"CAPTURE_INPUT_MISSING" end
    local st=input.state
    local rev=st.revision
    local debt_sig=st.prior_debt_signature
    if not scalar(rev) or not scalar(debt_sig) or not scalar(st.gen)
        or type(st.plan)~="table" or type(st.idx)~="number"
        or st.plan[st.idx]~=input.action_current or st.plan[st.idx+1]~=input.action_next then
        return nil,"CANONICAL_PLAN_OR_DEBT_NOT_STABLE"
    end
    local frame=input.event
    if type(frame)~="table" or frame.gen~=st.gen or frame.current_index~=st.idx
        or frame.successor_index~=st.idx+1
        or frame.current_action_id~=input.action_current.action_id
        or frame.successor_action_id~=input.action_next.action_id then
        return nil,"CAPTURE_IDENTITY_DIVERGED"
    end
    local g=frame.geometry
    local ok,why=has_fields(g,g and g.route_mode)
    if not ok then return nil,why end
    local a,err=A.capture(frame)
    if not a then return nil,err end
    if g.route_debt_mode=="HARD" then return nil,"CURRENT_ROUTE_DEBT_HARD" end
    local e=input.evidence
    if not finite(e.previous_sample_ms) or not finite(e.current_sample_ms)
        or not finite(e.previous_remaining) or not finite(e.current_remaining)
        or not finite(e.ground_distance) then return nil,"MOTION_EVIDENCE_INVALID" end
    -- Establish that all B evidence was captured while the CURRENT Move was active.
    if frame.exact_current_execution~=true or e.current_sample_ms~=frame.sample_ms
        or e.current_sample_ms-e.previous_sample_ms~=frame.poll_ms
        or e.current_remaining~=g.remaining then return nil,"CAPTURE_MOTION_NOT_EXACT_CURRENT" end
    local timing=input.timing
    for _,k in ipairs({"proximity","stall_distance","lead_cap","brake_extra"}) do
        if not finite(timing[k]) or timing[k]<0 then return nil,"CAPTURE_TIMING_INVALID" end
    end
    return {
        a=a,revision=rev,prior_debt_signature=debt_sig,
        current=input.action_current,successor=input.action_next,
        geometry=copy_scalars(g),evidence=copy_scalars(e),timing=copy_scalars(timing)
    },"OK"
end
local function revalidate(cache,st,q)
    if type(cache)~="table" or type(st)~="table" or type(q)~="table" then
        return false,"INTEGRATION_INPUT_INVALID" end
    if st.gen~=cache.a.gen or st.revision~=cache.revision then
        return false,"PLAN_GENERATION_OR_REVISION_CHANGED" end
    if st.prior_debt_signature~=cache.prior_debt_signature then
        return false,"ROUTE_DEBT_CHANGED_SINCE_PROOF" end
    if st.idx~=cache.a.current_index or not st.plan
        or st.plan[st.idx]~=cache.current or st.plan[st.idx+1]~=cache.successor then
        return false,"CANONICAL_ACTIONS_CHANGED" end
    if st.pending_by_uid or st.transition_txn or st.blocked or st.terminal then
        return false,"TRANSITION_EXECUTION_BUSY" end
    if q.gen~=st.gen or q.current_index~=st.idx or q.future_index~=st.idx+1 then
        return false,"NATIVE_FUTURE_NOT_IMMEDIATE" end
    if q.execution_lineage~="PLAYER_NATIVE" and q.execution_lineage~="BSC_ISSUED" then
        return false,"EXECUTION_LINEAGE_UNPROVEN" end
    return true,"OK"
end
-- Explicit offline *simulation* of the existing T1.6 protocol, with a caller-supplied
-- mock Core implementation. No use in production until a separate audited stage.
function C.simulate_observed(A,B,Core,st,cache,q)
    local ok,why=revalidate(cache,st,q)
    if not ok then return deny(why,why=="NATIVE_FUTURE_NOT_IMMEDIATE") end
    if type(Core)~="table" or type(Core.begin_transition_txn)~="function"
       or type(Core.commit_transition_edge)~="function"
       or type(Core.abort_transition_txn)~="function" then
       return deny("T16_PROTOCOL_NOT_CONNECTED",true)
    end
    local preview=B.preview(A,cache.a,q,cache.evidence,cache.timing)
    if not preview.preview_open or preview.authoritative~=false then
        return deny(preview.reason or "MOVE_ADOPT_NOT_AUTHORIZED",preview.zone=="HARD_BLOCK")
    end
    -- A or B has proved permission from the exact-current observation; no
    -- post-Native-promotion route geometry is consulted.
    local g=copy_scalars(cache.geometry)
    local mode=preview.credit
    if mode=="STEERING_CORNER_HANDOFF" then g.route_mode="STEERING_CORNER"
    elseif mode=="REGISTER_ROUTE_OBLIGATION" then g.route_mode="PATH_SAFE"
    elseif mode=="ALREADY_SEMANTIC_DONE" then g.route_mode="COMPLETE"
    else return deny("UNKNOWN_MOVE_COMPLETION_CREDIT",true) end
    -- Crucially: T1.6 does NOT have a synthetic 'MOVE_ADOPT' credit. Instead
    -- it uses g.route_mode in Core.commit_transition_edge to match ACK semantics.
    local tx=Core.begin_transition_txn(st,cache.current,cache.successor,preview.reason,q.now_ms,g,"NATIVE_RECONCILE")
    if not tx or tx.state~="AUTHORIZED" or tx.current~=cache.current
        or tx.successor~=cache.successor or tx.current_idx~=st.idx
        or tx.successor_idx~=st.idx+1 then
        if tx then Core.abort_transition_txn(st,tx,"TXN_AUTHORIZATION_IDENTITY_MISMATCH",q.now_ms) end
        return deny("TXN_AUTHORIZATION_IDENTITY_MISMATCH",true)
    end
    tx.state="OBSERVED";tx.execution_lineage=q.execution_lineage
    local committed=Core.commit_transition_edge(st,tx,q.now_ms,{
        owned=false,execution_lane=q.execution_lineage,
        observed_execution_lineage=q.execution_lineage,
        use_current_origin=true,enter_reason="NATIVE_SUCCESSOR_ADOPTED"
    })
    if committed~=true then
        Core.abort_transition_txn(st,tx,"TXN_COMMIT_REJECTED",q.now_ms)
        return deny("TXN_COMMIT_REJECTED",true)
    end
    if tx.state~="COMMITTED" or st.idx~=cache.a.successor_index
        or st.plan[st.idx]~=cache.successor then
        return deny("COMMIT_CONTRACT_FAILED",true)
    end
    return {allow=true,authoritative=false,zone=preview.zone,reason="T16_OBSERVED_COMMITTED_SHADOW",
        simulated=true,credit=mode,preserve_prior_debt=preview.preserve_prior_debt==true,
        transaction_state=tx.state,committed_edge=true}
end
return C
