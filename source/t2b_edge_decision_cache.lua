-- T2B_EDGE_DECISION_CACHE_1
local C={VERSION="T2B_EDGE_DECISION_CACHE_1"}
local HUGE=(type(math.huge)=="number" and math.huge) or 1e300
local function finite(n)return type(n)=="number" and n==n and n<HUGE and n>-HUGE end
local function sid(v)return type(v)=="number" or type(v)=="string" end
local function ce(e)e=type(e)=="table" and e or {};return {open=e.open==true,reason=e.reason or "TRANSITION_WAIT",hard_violation=e.hard_violation==true} end
local function gc(g)local o={};for k,v in pairs(g) do local t=type(v);if t=="number" or t=="string" or t=="boolean" then o[k]=v end end;return o end
function C.capture(e)
 if type(e)~="table" or not sid(e.gen) or not sid(e.current_action_id) or not sid(e.successor_action_id) or not finite(e.sample_ms) or not finite(e.poll_ms) or e.poll_ms<=0 or type(e.decision)~="table" or type(e.geometry)~="table" then return nil,"CACHE_INPUT_INVALID" end
 local d=e.decision;return {gen=e.gen,current_action_id=e.current_action_id,successor_action_id=e.successor_action_id,sample_ms=e.sample_ms,poll_ms=e.poll_ms,decision={hard_violation=d.hard_violation==true,reason=d.reason,route_ok=d.route_ok==true,route_reason=d.route_reason,route_debt_mode=d.route_debt_mode,current_credit=d.current_credit,issue_route_mode=d.issue_route_mode,adopt_route_mode=d.adopt_route_mode,issue_window=ce(d.issue_window),adopt_window=ce(d.adopt_window)},geometry=gc(e.geometry)},"OK"
end
function C.read(c,q)
 if type(c)~="table" or type(q)~="table" then return nil,"CACHE_MISSING" end
 if c.gen~=q.gen or c.current_action_id~=q.current_action_id or c.successor_action_id~=q.successor_action_id then return nil,"CACHE_EDGE_IDENTITY_MISMATCH" end
 if not finite(q.now_ms) or not finite(q.current_step_ms) or q.current_step_ms<=0 then return nil,"CACHE_CLOCK_INVALID" end
 local age=q.now_ms-c.sample_ms;if age<0 then return nil,"CACHE_TIME_REVERSED" end;if age>q.current_step_ms then return nil,"CACHE_OLDER_THAN_ONE_OBSERVED_POLL" end;return c,"OK"
end
return C
