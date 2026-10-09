local P=assert(loadfile(arg[1]))()
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local base={immediate_successor=true,target_exact=true,target_terminal_abort=false,prior_route_clear=true,semantic_done=false,exit_route=false,arrival_issue_coherent=true,arrival_adopt_coherent=true,path_error=8,waypoint_tolerance=3,remaining=10,sync_margin=1}
local function C(x)local f={};for k,v in pairs(base)do f[k]=v end;for k,v in pairs(x or {})do f[k]=v end;return P.evaluate(f)end
T('skip hard',function()assert(C{immediate_successor=false}.hard_violation)end)
T('target hard',function()assert(C{target_exact=false}.hard_violation)end)
T('debt blocks',function()
 local d=C{prior_route_clear=false,path_error=2,remaining=1}
 assert(not d.issue_window.open and not d.adopt_window.open)
end)
T('complete preserves',function()local d=C{semantic_done=true,exit_route=true,arrival_issue_coherent=false,arrival_adopt_coherent=false};assert(d.issue_window.open and d.adopt_window.open)end)
T('exit strict',function()
 local d=C{exit_route=true,path_error=2,remaining=1}
 assert(not d.issue_window.open and not d.adopt_window.open)
end)
T('path safe',function()local d=C{path_error=2,remaining=30};assert(d.issue_window.open and d.adopt_window.open and d.current_credit=='ATTACK_TERMINAL_HANDOFF')end)
T('path adopt-only',function()local d=C{path_error=2,arrival_issue_coherent=false,arrival_adopt_coherent=true};assert(not d.issue_window.open and d.adopt_window.open)end)
T('terminal issue',function()local d=C{remaining=3,sync_margin=50};assert(d.issue_window.open)end)
T('terminal adopt-only',function()local d=C{remaining=3.5,sync_margin=0.5};assert(not d.issue_window.open and d.adopt_window.open)end)
T('beyond poll blocks',function()local d=C{remaining=3.5001,sync_margin=0.5};assert(not d.issue_window.open and not d.adopt_window.open)end)
T('sync never widens issue',function()for _,r in ipairs({3.1,3.5,4,6,20})do local seen=nil;for _,s in ipairs({0,.1,.5,1,5,50})do local d=C{remaining=r,sync_margin=s};if seen==nil then seen=d.issue_window.open else assert(d.issue_window.open==seen)end end end end)
T('issue subset adopt',function()for _,p in ipairs({0,2,3,3.1,8,100})do for _,r in ipairs({0,2,3,3.2,4,20})do for _,s in ipairs({0,.5,2,20})do local d=C{path_error=p,remaining=r,sync_margin=s};assert(not d.issue_window.open or d.adopt_window.open)end end end end)
T('terminated closes',function()local d=C{path_error=2,target_terminal_abort=true};assert(not d.issue_window.open and not d.adopt_window.open)end)
T('H7 real terminal stall permits attack without monotone G1.1 braking',function()
 local d=C{arrival_issue_coherent=false,arrival_adopt_coherent=false,path_error=8,
     waypoint_tolerance=3,remaining=13.4,terminal_stall_proven=true,terminal_stall_limit=17}
 assert(d.issue_window.open and d.adopt_window.open)
 assert(d.issue_window.reason=='ATTACK_TERMINAL_STALL_VERIFIED')
 assert(d.current_credit=='ATTACK_TERMINAL_HANDOFF')
end)
T('H7 does not short circuit distant or unproved stops',function()
 for _,f in ipairs({
  {remaining=17.0001,terminal_stall_proven=true,terminal_stall_limit=17},
  {remaining=13.4,terminal_stall_proven=false,terminal_stall_limit=17},
  {remaining=13.4,terminal_stall_proven=true,terminal_stall_limit=nil}
 })do
  f.arrival_issue_coherent=false;f.arrival_adopt_coherent=false;f.path_error=8
  local d=C(f);assert(not d.issue_window.open and not d.adopt_window.open)
 end
end)
T('H7 preserves Exit, prior route debt, target and canonical hard guards',function()
 for _,f in ipairs({
  {exit_route=true},
  {prior_route_clear=false},
  {target_exact=false},
  {immediate_successor=false},
  {target_terminal_abort=true}
 })do
  f.terminal_stall_proven=true;f.terminal_stall_limit=17;f.remaining=13
  f.arrival_issue_coherent=false;f.arrival_adopt_coherent=false
  local d=C(f);assert(not d.issue_window.open and not d.adopt_window.open)
 end
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
