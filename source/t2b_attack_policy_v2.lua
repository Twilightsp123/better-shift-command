-- T2B_ATTACK_POLICY_2
local P={VERSION="T2B_ATTACK_POLICY_2"}
local HUGE=(type(math.huge)=="number" and math.huge) or 1e300
local function finite(n)return type(n)=="number" and n==n and n<HUGE and n>-HUGE end
local function env(o,r,h)return {open=o==true,reason=r or "TRANSITION_WAIT",hard_violation=h==true} end
function P.evaluate(f)
 local d={reason="ATTACK_TRANSITION_WAIT",hard_violation=false,current_credit=nil,issue_window=env(false,"ATTACK_TRANSITION_WAIT",false),adopt_window=env(false,"ATTACK_TRANSITION_WAIT",false),issue_route_mode="BLOCKED",adopt_route_mode="BLOCKED"}
 if type(f)~="table" then d.hard_violation=true;d.reason="ATTACK_POLICY_INPUT_INVALID";d.issue_window=env(false,d.reason,true);d.adopt_window=env(false,d.reason,true);return d end
 if f.immediate_successor~=true then d.hard_violation=true;d.reason="CANONICAL_INTERMEDIATE_ACTIONS_OWED";d.issue_window=env(false,d.reason,true);d.adopt_window=env(false,d.reason,true);return d end
 if f.target_exact~=true then d.hard_violation=true;d.reason="ATTACK_TARGET_IDENTITY_MISMATCH";d.issue_window=env(false,d.reason,true);d.adopt_window=env(false,d.reason,true);return d end
 if f.target_terminal_abort==true then d.reason="ATTACK_TARGET_TERMINATED";d.issue_window=env(false,d.reason,false);d.adopt_window=env(false,d.reason,false);return d end
 if f.prior_route_clear~=true then d.reason="PRIOR_ROUTE_OBLIGATION_PENDING";d.issue_window=env(false,d.reason,false);d.adopt_window=env(false,d.reason,false);return d end
 if f.semantic_done==true then d.reason="ATTACK_AFTER_ROUTE_COMPLETE";d.issue_route_mode="COMPLETE";d.adopt_route_mode="COMPLETE";d.issue_window=env(true,d.reason,false);d.adopt_window=env(true,d.reason,false);return d end
 if f.exit_route==true then d.reason="ATTACK_REQUIRES_ROUTE_COMPLETE";d.issue_window=env(false,d.reason,false);d.adopt_window=env(false,d.reason,false);return d end
 if not finite(f.path_error) or not finite(f.waypoint_tolerance) or f.waypoint_tolerance<0 or not finite(f.remaining) or f.remaining<0 then d.reason="ATTACK_ROUTE_GEOMETRY_UNAVAILABLE";d.issue_window=env(false,d.reason,false);d.adopt_window=env(false,d.reason,false);return d end
 -- H8: two distinct proofs are accepted: G11 predictive braking below, or
 -- current Native MOVE physically stable near its canonical terminal.  The
 -- latter is computed from fresh observed positions, not elapsed time alone.
 if f.terminal_stall_ready==true and f.native_current_exact==true
   and finite(f.terminal_stall_limit) and f.terminal_stall_limit>0
   and finite(f.route_min_progress) and finite(f.route_progress)
   and f.route_progress>=f.route_min_progress
   and f.remaining<=f.terminal_stall_limit then
   d.reason="ATTACK_NATIVE_MOVE_STALL_TERMINAL"
   d.issue_route_mode=d.reason;d.adopt_route_mode=d.reason
   d.issue_window=env(true,d.reason,false);d.adopt_window=env(true,d.reason,false)
   d.current_credit="ATTACK_TERMINAL_HANDOFF";return d
 end
 local sync=finite(f.sync_margin) and math.max(0,f.sync_margin) or 0;local safe=f.path_error<=f.waypoint_tolerance
 local io,ao=false,false;local ir,ar="ATTACK_ARRIVAL_BRAKE_UNPROVEN","ATTACK_ARRIVAL_BRAKE_UNPROVEN";local im,am="BLOCKED","BLOCKED"
 if safe then
  if f.arrival_issue_coherent==true then io=true;ir="ATTACK_PATH_SAFE";im="ATTACK_PATH_SAFE" end
  if f.arrival_adopt_coherent==true then ao=true;if io then ar="ATTACK_PATH_SAFE";am="ATTACK_PATH_SAFE" else ar="ATTACK_PATH_SAFE_HYSTERESIS";am="ATTACK_PATH_SAFE_HYSTERESIS" end end
 else
  if f.arrival_issue_coherent==true and f.remaining<=f.waypoint_tolerance then io=true;ir="ATTACK_TERMINAL_CORRIDOR";im="ATTACK_TERMINAL_CORRIDOR" elseif f.arrival_issue_coherent==true then ir="ATTACK_TERMINAL_WAIT_REACH" end
  if f.arrival_adopt_coherent==true and f.remaining<=f.waypoint_tolerance+sync then ao=true;if io then ar="ATTACK_TERMINAL_CORRIDOR";am="ATTACK_TERMINAL_CORRIDOR" else ar="ATTACK_TERMINAL_HYSTERESIS";am="ATTACK_TERMINAL_HYSTERESIS" end elseif f.arrival_adopt_coherent==true then ar="ATTACK_TERMINAL_ROUTE_PROTECT" end
 end
 d.issue_window=env(io,ir,false);d.adopt_window=env(ao,ar,false);d.issue_route_mode=im;d.adopt_route_mode=am;d.reason=io and ir or (ao and ar or ir);if io or ao then d.current_credit="ATTACK_TERMINAL_HANDOFF" end;return d
end
return P
