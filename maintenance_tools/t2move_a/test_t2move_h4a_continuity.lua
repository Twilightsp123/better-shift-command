-- H4-A real-controller failure-first corner-runthrough capability specification.
-- PRE-FIX candidate expected to fail H4-A01/A02, other cases remain green.
-- No WH3 physics claim: synthetic positions are controlled observations.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print("PASS "..n)
 else fail=fail+1;print("FAIL "..n.." :: "..tostring(e)) end
end
local function no_crash(f)
 for _,s in ipairs(f.logs) do assert(not s:find("CONTROLLER_FAIL",1,true),s) end
end
local function make(destx,destz,width)
 local f=F({debug_source=true,width=width});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,destx,destz)
 f:tick(100,0,0);f:tick(200,60,0)
 return f
end
T("H4-A01 90-degree corner must maintain movement without issuing unsafe direct successor",function()
 local f=make(100,100,40)
 assert(f:has("H2_ROUTE_ISSUE_BLOCKED"),"historical failure witness must remain visible")
 assert(f.issued>=1,"no early continuity command; CA will reach waypoint before successor can be sent")
 local d=f.commands[1] and f.commands[1].draft
 assert(d and d.kind=="MOVE","continuous route needs a properly tracked Native MOVE")
 assert(not (math.abs(d.x-100)<0.01 and math.abs(d.z-100)<0.01),
   "direct early P2=100,100 shortcut loses P1=100,0")
 assert(math.abs(d.z)<0.01 and d.x>100,
   "pre-turn extension must retain the original approach line beyond P1")
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"),"no synthetic waypoint credit")
 f:deliver();f:tick(300,60,0)
 assert(not f:has("TRANSITION_EDGE_COMMITTED"),"auxiliary continuation ACK must not advance canonical cursor")
 no_crash(f)
end)
T("H4-A02 180-degree reversal must maintain inbound motion without dropping P1",function()
 local f=make(0,0,20)
 assert(f:has("H2_ROUTE_ISSUE_BLOCKED"),"unsafe U-turn must be identified")
 assert(f.issued>=1,"no inbound run-through preparation for 180-degree turn")
 local d=f.commands[1] and f.commands[1].draft
 assert(d and d.kind=="MOVE" and math.abs(d.z)<0.01 and d.x>100,
   "must keep travelling toward/through waypoint before reversing")
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"))
 f:deliver();f:tick(300,60,0)
 assert(not f:has("TRANSITION_EDGE_COMMITTED"),"continuation ACK is NOT successor ACK")
 no_crash(f)
end)
T("H4-A03 legal forward PATH_SAFE remains predictive and debt remains payable",function()
 local f=F({debug_source=true});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:tick(100,0,0);f:tick(200,80,0)
 assert(f.issued==1 and f.commands[1].draft.x==200)
 f:deliver();f:tick(300,80,0)
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED") and f:has("TRANSITION_EDGE_COMMITTED"))
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"))
 no_crash(f)
end)
T("H4-A04 no ACK cannot create route completion or transaction commit",function()
 local f=F({debug_source=true});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1)
 f:tick(300,80,0)
 assert(not f:has("TRANSITION_EDGE_COMMITTED"))
 assert(not f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 no_crash(f)
end)
T("H4-A05 rejected Native successor cannot erase current P",function()
 local f=F({debug_source=true,reject_native=true});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1)
 f:deliver();f:tick(300,80,0)
 assert(not f:has("TRANSITION_EDGE_COMMITTED"))
 assert(not f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 no_crash(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H4-A EXPECTED RED, NO WH3 GAMEPLAY")
os.exit(fail==0 and 0 or 1)
