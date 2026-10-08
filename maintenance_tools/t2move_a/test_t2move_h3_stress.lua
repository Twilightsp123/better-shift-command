-- H3 deterministic offline stress: real shipped controller, simulated CA positions.
-- Not WH3 physics, and no mileage/timing parameters are tuned here.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(name,fn)
 local ok,why=pcall(fn);if ok then pass=pass+1;print("PASS "..name)
 else fail=fail+1;print("FAIL "..name.." :: "..tostring(why)) end
end
local function events(f,name,u)
 local n=0
 for _,line in ipairs(f.logs) do
  if line:find("] "..name.." uid="..(u or "1001").." ",1,true) then n=n+1 end
 end
 return n
end
local function no_crash(f)
 for _,line in ipairs(f.logs) do assert(not line:find("CONTROLLER_FAIL",1,true),line) end
end
local function queued(points,width)
 local f=F({debug_source=true,width=width or 20})
 f:start()
 for i,p in ipairs(points) do f:emit("MOVE",i>1,p[1],p[2]) end
 f:tick(100,0,0)
 return f
end
T("H3-01 10-node collinear stress keeps cursor <= committed ACK count",function()
 local points={};for i=1,10 do points[i]={70+i*30,0} end
 local f=queued(points,10)
 local t=200
 for x=80,362,10 do
  f:tick(t,x,0);t=t+100
  if f.native_pending then f:deliver();f:tick(t,x,0);t=t+100 end
  assert(events(f,"TRANSITION_EDGE_COMMITTED")<=f.issued,"commit without Native issue")
  assert(events(f,"ROUTE_OBLIGATION_SATISFIED")<=events(f,"ROUTE_OBLIGATION_TRANSFERRED"),
    "route debt satisfaction inflated")
  assert(f.issued<=9,"more issued transitions than canonical edges")
  no_crash(f)
 end
 assert(f.issued>=3,"stress did not exercise enough transitions")
end)
T("H3-02 alternating 10-node zigzag never silently credits away from every node",function()
 local points={};for i=1,10 do points[i]={100+5*(i-1),(i%2==0) and 15 or 0} end
 local f=queued(points,4)
 for i,x in ipairs({20,40,60,70,80,85,90}) do
  f:tick(100+i*100,x,0)
  assert(events(f,"TRANSITION_EDGE_COMMITTED")==0,"unsafe zigzag accepted before reach")
  no_crash(f)
 end
 assert(f:has("H2_ROUTE_ISSUE_BLOCKED"),"route conflict not observed")
end)
T("H3-03 cardinal directions 90/135/180 need proof before issuing",function()
 for _,p in ipairs({{100,100},{30,70},{0,0},{80,0},{100,-100}}) do
  local f=queued({{100,0},p},20)
  f:tick(200,60,0)
  assert(f.issued==0,"turn cut without completing P100 "..p[1]..","..p[2])
  assert(events(f,"TRANSITION_EDGE_COMMITTED")==0)
  no_crash(f)
 end
end)
T("H3-04 route debts survive stacked forward ACKs until observed traversal",function()
 local f=queued({{100,0},{120,0},{140,0},{160,0},{180,0}},4)
 f:tick(200,80,0);assert(f.issued==1)
 f:deliver();f:tick(300,80,0)
 assert(events(f,"ROUTE_OBLIGATION_TRANSFERRED")==1)
 f:tick(400,92,0);assert(f.issued==2)
 f:deliver();f:tick(500,92,0)
 assert(events(f,"ROUTE_OBLIGATION_TRANSFERRED")==2)
 assert(events(f,"ROUTE_OBLIGATION_SATISFIED")==0)
 f:tick(600,101,0)
 assert(events(f,"ROUTE_OBLIGATION_SATISFIED")==1)
 no_crash(f)
end)
T("H3-05 pending/native rejection never credits or queues duplicate completion",function()
 local f=queued({{100,0},{200,0}})
 f:tick(200,75,0);assert(f.issued==1)
 for t=300,600,100 do f:tick(t,75,0) end
 assert(events(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(events(f,"ROUTE_OBLIGATION_TRANSFERRED")==0)
 assert(f.issued==1)
 no_crash(f)
 local bad=F({debug_source=true,reject_native=true});bad:start()
 bad:emit("MOVE",false,100,0);bad:emit("MOVE",true,200,0)
 bad:tick(100,0,0);bad:tick(200,75,0);assert(bad.issued==1)
 bad:deliver();bad:tick(300,75,0)
 assert(events(bad,"TRANSITION_EDGE_COMMITTED")==0)
 assert(events(bad,"ROUTE_OBLIGATION_TRANSFERRED")==0)
 no_crash(bad)
end)
T("H3-06 two units simultaneously maintain isolated route obligations",function()
 local f=F({debug_source=true,two_units=true})
 f:start();f.unit2.x=0;f.unit2.z=0
 for _,uid in ipairs({"1001","1002"}) do
  f:emit("MOVE",false,100,0,nil,uid)
  f:emit("MOVE",true,200,0,nil,uid)
 end
 f:tick(100,0,0);f.unit2.x=80
 f:tick(200,80,0)
 assert(f.issued==2,"two independent MOVE issues expected")
 assert(f.pending_count==2,"two-unit queue isolation failed")
 f:deliver("1002");f:tick(300,80,0)
 assert(events(f,"TRANSITION_EDGE_COMMITTED","1002")==1)
 assert(events(f,"TRANSITION_EDGE_COMMITTED","1001")==0)
 f:deliver("1001");f:tick(400,80,0)
 assert(events(f,"TRANSITION_EDGE_COMMITTED","1001")==1)
 no_crash(f)
end)
T("H3-07 Native revision drift cannot turn stale ISSUE into credit",function()
 local f=F({debug_source=true,revision_race=true});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:tick(100,0,0);f:tick(200,80,0)
 assert(events(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(events(f,"ROUTE_OBLIGATION_TRANSFERRED")==0)
 no_crash(f)
end)
T("H3-08 REPLACE cancels pending old generation rather than crediting old edge",function()
 local f=queued({{100,0},{200,0}})
 f:tick(200,80,0);assert(f.issued==1)
 f:emit("MOVE",false,-100,0)
 f:tick(300,80,0)
 assert(events(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(events(f,"ROUTE_OBLIGATION_TRANSFERRED")==0)
 no_crash(f)
end)
T("H3-09 final unresolved SC3 debt blocks premature Move-to-Attack",function()
 local f=F({debug_source=true})
 f:start();f.enemy.x=300;f.enemy.z=0
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:emit("ATTACK",true,nil,nil,"2001")
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1)
 f:deliver();f:tick(300,80,0);f:tick(400,120,50);f:tick(500,200,0)
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 assert(not f:has("ROUTE_OBLIGATION_SATISFIED"))
 assert(f.issued==1,"unpaid P100 leaked into ATTACK")
 no_crash(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H3 STRESS SYNTHETIC ONLY / NO WH3")
os.exit(fail==0 and 0 or 1)
