-- T2MOVE_B_HYSTERESIS_SHADOW_1
-- Non-authoritative: one-poll travel widens temporal issue frontier ONLY.
local B={VERSION="T2MOVE_B_HYSTERESIS_SHADOW_1"}
local huge=math.huge or 1e300
local function finite(n) return type(n)=="number" and n==n and n<huge and n>-huge end
local function valid_nonnegative(v) return finite(v) and v>=0 end
local function copy_scalars(t)
    local out={}
    for k,v in pairs(t) do
        if type(k)=="string" and (type(v)=="string" or type(v)=="boolean" or finite(v)) then
            out[k]=v
        end
    end
    return out
end
local function deny(reason,hard)
    return {preview_open=false,zone=hard and "HARD_BLOCK" or "WAIT",reason=reason,
        authoritative=false,credit=nil,one_poll_travel=nil}
end
function B.preview(A,c,q,evidence,timing)
    if type(A)~="table" or type(A.preview)~="function" then
        return deny("STAGE_A_REQUIRED",true)
    end
    local stage_a=A.preview(c,q)
    if stage_a.preview_open then return stage_a end
    if stage_a.reason~="PREPROMOTION_MOVE_ISSUE_NOT_PROVEN" then return stage_a end
    if type(c)~="table" or c.issue_open or c.route_ok~=true then
        return deny("PRIOR_ROUTE_OR_ISSUE_PROOF_NOT_READY",false)
    end
    if c.semantic_done then return deny("CURRENT_ALREADY_SEMANTIC_DONE",false) end
    local g=c.geometry
    if type(g)~="table" or (c.route_mode~="PATH_SAFE" and c.route_mode~="STEERING_CORNER") then
        return deny("MOVE_ROUTE_MODE_NOT_PROVEN",false)
    end
    if c.prior_debt_mode~="CLEAR" and c.prior_debt_mode~="SOFT_PRESERVED" then
        return deny("PRIOR_ROUTE_DEBT_NOT_PROVEN",true)
    end
    if c.prior_debt_mode=="SOFT_PRESERVED" then
        if not valid_nonnegative(g.route_debt_error) or not valid_nonnegative(g.route_debt_limit)
            or not finite(g.route_debt_count) or g.route_debt_count<=0
            or g.route_debt_error>g.route_debt_limit then
            return deny("SC3_DEBT_CORRIDOR_UNPROVEN",true)
        end
    end
    if not valid_nonnegative(g.remaining) or not finite(g.leg) or g.leg<=0
        or not finite(g.next_leg) or g.next_leg<=0
        or not finite(g.progress) or not valid_nonnegative(g.route_min_progress)
        or g.progress<g.route_min_progress then
        return deny("ADJACENT_LEG_OR_PROGRESS_UNPROVEN",false)
    end
    if c.route_mode=="PATH_SAFE" then
        if c.route_reason~="PATH_DEVIATION_SAFE_WITH_MARGIN"
            or not valid_nonnegative(g.cut_error) or not valid_nonnegative(g.cut_safe_limit)
            or not valid_nonnegative(g.cut_tolerance)
            or g.cut_error>g.cut_safe_limit or g.cut_safe_limit>g.cut_tolerance
            or g.cut_safe_limit>math.max(1,g.next_leg) then
            return deny("PATH_SAFE_SPATIAL_PROOF_UNCHANGED",false)
        end
    else
        if c.route_reason~="TURN_CORRIDOR_ENTERED" and c.route_reason~="TURN_CORRIDOR_STALL_ESCAPE" then
            return deny("STEERING_CORNER_REASON_UNPROVEN",false)
        end
        if not valid_nonnegative(g.corner_window)
            or not valid_nonnegative(g.corner_window_base)
            or not valid_nonnegative(g.corner_window_early)
            or g.corner_window~=math.max(g.corner_window_base,g.corner_window_early)
            or g.remaining>g.corner_window
            or g.corner_window>math.min(g.leg,g.next_leg) then
            return deny("STEERING_CORNER_ADJACENT_CAP_UNPROVEN",false)
        end
        if c.route_reason=="TURN_CORRIDOR_STALL_ESCAPE" and g.corner_stall_escape~=true then
            return deny("SC4_STALL_ESCAPE_UNPROVEN",false)
        end
    end
    if type(timing)~="table" or not valid_nonnegative(timing.proximity)
        or not valid_nonnegative(timing.stall_distance)
        or not valid_nonnegative(timing.lead_cap)
        or not valid_nonnegative(timing.brake_extra)
        or not valid_nonnegative(g.threshold) then
        return deny("ISSUE_TIMING_BOUNDARY_UNAVAILABLE",false)
    end
    local temporal_frontier=math.max(timing.proximity,g.threshold)
    if g.stall==true then
        temporal_frontier=math.max(temporal_frontier,timing.stall_distance,
            math.min(timing.lead_cap,g.threshold+timing.brake_extra))
    end
    if g.remaining<=temporal_frontier then
        return deny("SHARED_ISSUE_WINDOW_CONTRADICTION",true)
    end
    if type(evidence)~="table" or not finite(evidence.previous_sample_ms)
        or not finite(evidence.current_sample_ms)
        or not finite(evidence.previous_remaining) or not finite(evidence.current_remaining)
        or not finite(evidence.ground_distance) then
        return deny("PREPROMOTION_MOTION_EVIDENCE_MISSING",false)
    end
    if evidence.current_sample_ms~=c.sample_ms
        or evidence.current_sample_ms-evidence.previous_sample_ms~=c.poll_ms
        or evidence.current_remaining~=g.remaining then
        return deny("MOTION_SAMPLE_NOT_ALIGNED_WITH_CACHE",false)
    end
    local radial_travel=evidence.previous_remaining-evidence.current_remaining
    if radial_travel<=0 or evidence.ground_distance<radial_travel then
        return deny("ONE_POLL_APPROACH_NOT_PROVEN",false)
    end
    if g.arrival_brake_ready~=true or not valid_nonnegative(g.arrival_sync_margin)
        or math.abs(g.arrival_sync_margin-radial_travel)>
           (8*2^-52)*math.max(1,radial_travel,g.arrival_sync_margin) then
        return deny("G1_ONE_POLL_MEASUREMENT_MISMATCH",false)
    end
    local one_poll_travel=math.min(radial_travel,g.arrival_sync_margin)
    if g.remaining>temporal_frontier+one_poll_travel then
        return deny("OUTSIDE_ONE_POLL_TIMING_BAND",false)
    end
    local credit=c.route_mode=="STEERING_CORNER" and "STEERING_CORNER_HANDOFF" or "REGISTER_ROUTE_OBLIGATION"
    return {preview_open=true,zone="ADOPT_ONLY",reason="MOVE_ONE_POLL_TIMING_HYSTERESIS",
        authoritative=false,credit=credit,preserve_prior_debt=c.prior_debt_mode=="SOFT_PRESERVED",
        one_poll_travel=one_poll_travel,temporal_frontier=temporal_frontier,
        route_mode=c.route_mode,geometry=copy_scalars(g)}
end
return B
