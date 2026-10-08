-- BSC-TPOL-T2MOVE-A-SHADOW-1
-- Pure offline pre-promotion decision cache + reconciliation preview.
-- No gameplay permission, dispatch, cursor advancement or Native APIs.
local A={VERSION="T2MOVE_A_SHADOW_1"}
local function scalar(v) return type(v)=="string" or type(v)=="number" end
local function finite(v) return type(v)=="number" and v==v and v<math.huge and v>-math.huge end
local modes={PATH_SAFE=true,STEERING_CORNER=true,COMPLETE=true}
local function copy_scalars(t)
    local out={}
    if type(t)=="table" then
        for k,v in pairs(t) do
            if type(k)=="string" and (type(v)=="string" or type(v)=="boolean" or finite(v)) then
                out[k]=v
            end
        end
    end
    return out
end
local function deny(reason,hard)
    return {preview_open=false,zone=hard and "HARD_BLOCK" or "WAIT",reason=reason,
        authoritative=false,credit=nil,geometry=nil}
end
function A.capture(e)
    if type(e)~="table" or e.exact_current_execution~=true then return nil,"CURRENT_EXECUTION_NOT_EXACT" end
    if not scalar(e.gen) or not scalar(e.current_action_id) or not scalar(e.successor_action_id)
        or not scalar(e.unit_lifetime) or not finite(e.sample_ms) or not finite(e.poll_ms)
        or e.poll_ms<=0 or not finite(e.current_index) or not finite(e.successor_index)
        or e.successor_index~=e.current_index+1 then return nil,"EDGE_IDENTITY_INVALID" end
    if type(e.decision)~="table" or type(e.geometry)~="table"
        or e.current_kind~="MOVE" or e.successor_kind~="MOVE" then return nil,"MOVE_EDGE_INPUT_INVALID" end
    local d=e.decision
    if d.transition_kind~="MOVE->MOVE" or d.hard_violation==true then
        return nil,"CANONICAL_POLICY_PROOF_INVALID"
    end
    local g=copy_scalars(e.geometry)
    return {
        gen=e.gen,unit_lifetime=e.unit_lifetime,
        current_action_id=e.current_action_id,successor_action_id=e.successor_action_id,
        current_index=e.current_index,successor_index=e.successor_index,
        sample_ms=e.sample_ms,poll_ms=e.poll_ms,
        issue_open=type(d.issue_window)=="table" and d.issue_window.open==true,
        route_ok=d.route_ok==true,route_reason=d.route_reason,
        route_mode=g.route_mode,prior_debt_mode=g.route_debt_mode,
        semantic_done=e.semantic_done==true,geometry=g,
    },"OK"
end
function A.preview(c,q)
    if type(q)~="table" or q.exact_native_successor~=true then
        return deny("EXACT_NATIVE_SUCCESSOR_NOT_PROVEN",true)
    end
    if not finite(q.current_index) or not finite(q.future_index) or q.future_index~=q.current_index+1 then
        return deny("CANONICAL_INTERMEDIATE_ACTIONS_OWED",true)
    end
    if type(c)~="table" then return deny("PREPROMOTION_CACHE_MISSING",false) end
    if q.gen~=c.gen or q.unit_lifetime~=c.unit_lifetime
       or q.current_action_id~=c.current_action_id or q.successor_action_id~=c.successor_action_id
       or q.current_index~=c.current_index or q.future_index~=c.successor_index then
        return deny("PREPROMOTION_EDGE_IDENTITY_MISMATCH",true)
    end
    if not finite(q.now_ms) or not finite(q.observed_step_ms) or q.observed_step_ms<=0 then
        return deny("OBSERVATION_CLOCK_INVALID",false)
    end
    local age=q.now_ms-c.sample_ms
    if age<0 or age>q.observed_step_ms then return deny("CACHE_OUTSIDE_ONE_ACTUAL_POLL",false) end
    -- Stage A shadow only: no adopt-only hysteresis and no route relaxation.
    if not c.issue_open or not c.route_ok or not modes[c.route_mode] then
        return deny("PREPROMOTION_MOVE_ISSUE_NOT_PROVEN",false)
    end
    local credit
    if c.semantic_done or c.route_mode=="COMPLETE" then
        credit="ALREADY_SEMANTIC_DONE"
    elseif c.route_mode=="STEERING_CORNER" then
        credit="STEERING_CORNER_HANDOFF"
    else
        credit="REGISTER_ROUTE_OBLIGATION"
    end
    return {preview_open=true,zone="ISSUE_READY",reason="SHADOW_MOVE_EXACT_ISSUE_READY",
        authoritative=false,credit=credit,geometry=copy_scalars(c.geometry),
        preserve_prior_debt=c.prior_debt_mode=="SOFT_PRESERVED"}
end
return A
