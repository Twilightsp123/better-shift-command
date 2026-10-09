-- H8 policy-level adversarial gates for the independent Native-MOVE stall lane.
local P=assert(loadfile(assert(arg[1])))()
local pass,fail=0,0
local function T(name,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print("PASS "..name)
 else fail=fail+1;print("FAIL "..name.." :: "..tostring(e)) end
end
local default={immediate_successor=true,target_exact=true,target_terminal_abort=false,
 prior_route_clear=true,semantic_done=false,exit_route=false,
 arrival_issue_coherent=false,arrival_adopt_coherent=false,
 path_error=30,waypoint_tolerance=5,remaining=16,sync_margin=0,
 terminal_stall_ready=true,native_current_exact=true,
 terminal_stall_limit=20,route_progress=0.84,route_min_progress=0.60}
local function C(ch)
 local t={} for k,v in pairs(default) do t[k]=v end
 for k,v in pairs(ch or {}) do t[k]=v end
 return P.evaluate(t)
end
T("H8P01 explicit stationary exact MOVE grants ISSUE independent of G11",function()
 local d=C();assert(d.issue_window.open and d.adopt_window.open)
 assert(d.current_credit=="ATTACK_TERMINAL_HANDOFF")
 assert(d.reason=="ATTACK_NATIVE_MOVE_STALL_TERMINAL")
end)
T("H8P02 stale or missing Native MOVE proof fails closed",function()
 assert(not C{native_current_exact=false}.issue_window.open)
 assert(not C{terminal_stall_ready=false}.adopt_window.open)
end)
T("H8P03 outside existing bounded terminal cannot issue",function()
 assert(not C{remaining=20.01}.issue_window.open)
end)
T("H8P04 route progress remains mandatory",function()
 assert(not C{route_progress=0.59}.issue_window.open)
end)
T("H8P05 unpaid prior MOVE debt fails closed",function()
 assert(not C{prior_route_clear=false}.issue_window.open)
end)
T("H8P06 EXIT_ROUTE still strictly requires completion",function()
 assert(not C{exit_route=true}.issue_window.open)
end)
T("H8P07 bad target and canonical gap fail closed",function()
 assert(C{target_exact=false}.hard_violation)
 assert(C{immediate_successor=false}.hard_violation)
end)
T("H8P08 terminal target is not live",function()
 assert(not C{target_terminal_abort=true}.issue_window.open)
end)
T("H8P09 G11 existing braking path still works",function()
 local d=C{terminal_stall_ready=false,arrival_issue_coherent=true,arrival_adopt_coherent=true,path_error=2}
 assert(d.issue_window.open and d.current_credit=="ATTACK_TERMINAL_HANDOFF")
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; POLICY ONLY")
os.exit(fail==0 and 0 or 1)
