local H=(function()
    local H={VERSION="T2B_ATTACK_HANDOFF_1"}
    local HUGE=(type(math.huge)=="number" and math.huge) or 1e300
    local function finite(n) return type(n)=="number" and n==n and n<HUGE and n>-HUGE end
    function H.evaluate(f)
        local d={ready=false,reason="ATTACK_TRANSITION_WAIT",route_mode="BLOCKED",current_credit=nil}
        if type(f)~="table" then d.reason="ATTACK_HANDOFF_INPUT_INVALID";return d end
        if f.prior_clear~=true then d.reason="PRIOR_ROUTE_OBLIGATION_PENDING";return d end
        if f.semantic_done==true then
            d.ready=true;d.reason="ACTION_COMPLETE";d.route_mode="COMPLETE";return d
        end
        if f.exit_route==true then d.reason="ATTACK_REQUIRES_ROUTE_COMPLETE";return d end
        if f.arrival_braking~=true then d.reason="ATTACK_ARRIVAL_BRAKE_NOT_OBSERVED";return d end
        if f.brake_boundary~=true then d.reason="ATTACK_BEFORE_ARRIVAL_BRAKE_BOUNDARY";return d end
        if not finite(f.path_error) or not finite(f.waypoint_tolerance) or f.waypoint_tolerance<0 then
            d.reason="ATTACK_ROUTE_GEOMETRY_UNAVAILABLE";return d
        end
        d.path_error=f.path_error;d.waypoint_tolerance=f.waypoint_tolerance
        if f.path_error<=f.waypoint_tolerance then
            d.ready=true;d.reason="ATTACK_PATH_SAFE";d.route_mode="ATTACK_PATH_SAFE"
            d.current_credit="ATTACK_TERMINAL_HANDOFF";return d
        end
        if not finite(f.remaining) or f.remaining<0 then d.reason="ATTACK_REMAINING_UNAVAILABLE";return d end
        local sync=finite(f.sync_margin) and math.max(0,f.sync_margin) or 0
        d.sync_margin=sync;d.terminal_limit=f.waypoint_tolerance+sync
        if f.remaining<=d.terminal_limit then
            d.ready=true;d.reason="ATTACK_TERMINAL_CORRIDOR";d.route_mode="ATTACK_TERMINAL_CORRIDOR"
            d.current_credit="ATTACK_TERMINAL_HANDOFF";return d
        end
        d.reason="ATTACK_TERMINAL_ROUTE_PROTECT";return d
    end
    return H
end)()
return H
