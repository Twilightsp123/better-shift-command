-- H2-A failing-first real-controller proof. LEGACY baseline SHOULD fail route-credit cases.
-- The entire test executes shipped controller with fake CA/native ACK semantics.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(label,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print("PASS "..label)
 else fail=fail+1;print("FAIL "..label.." :: "..tostring(e)) end
end
local function n(f,what)
 local count=0
 for _,s in ipairs(f.logs) do
  if s:find("] "..what.." uid=1001 ",1,true) then count=count+1 end
 end
 return count
end
local function report(f,term)
 local a={}
 for _,s in ipairs(f.logs) do
  if s:find(term,1,true) then a[#a+1]=s end
 end
 return table.concat(a," | ")
end
local function make(destx,destz,width)
 local f=F({debug_source=true,width=width or 20})
 f:start()
 f:emit("MOVE",false,100,0)
 f:emit("MOVE",true,destx,destz)
 f:tick(100,0,0)
 f:tick(200,60,0)
 return f
end
local function safe(f)
 for _,s in ipairs(f.logs) do assert(not s:find("CONTROLLER_FAIL",1,true),s) end
end
T("H2-A01 ACK at x60 for 180 U-turn must NOT mark P100 as visited",function()
 local f=make(0,0)
 assert(f.issued==1,"legacy early U-turn must be exercised")
 assert(f:has("H1_SHADOW_ISSUE") and f:has("verdict=BLOCKED"),"H1 witness missing")
 f:deliver();f:tick(300,60,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1,"ACK transition not committed")
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"),
   "ACK manufactured arrival at 100: "..report(f,"ACTION_COMPLETE"))
 assert(not f:has("ROUTE_OBLIGATION_SATISFIED"),"invented route satisfaction")
 safe(f)
end)
T("H2-A02 ACK at x60 for 90-degree corner cannot silently credit P100",function()
 local f=make(100,100,40)
 assert(f.issued==1,"legacy early 90 issue absent")
 assert(f:has("H1_SHADOW_ISSUE") and f:has("verdict=BLOCKED"),"90 H1 witness absent")
 f:deliver();f:tick(300,60,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1,"90 ACK missing")
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"),
   "ACK claimed waypoint without observed motion: "..report(f,"ACTION_COMPLETE"))
 safe(f)
end)
T("H2-A03 nearby 90 corner allows completion only from waypoint reach",function()
 local f=F({debug_source=true,width=40})
 f:start();f:emit("MOVE",false,100,0);f:emit("MOVE",true,100,100)
 f:tick(100,0,0);f:tick(200,98,0)
 assert(f.issued==1,"near corner not issued")
 f:deliver();f:tick(300,98,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(f:has("ACTION_COMPLETE"),"actual reached waypoint not credited")
 safe(f)
end)
T("H2-A04 collinear early ACK registers unpaid route debt without credit",function()
 local f=make(200,0)
 assert(f.issued==1,"legacy forward issue absent")
 f:deliver();f:tick(300,60,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED"),"forward unpaid P missing")
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"),"forward path prematurely credited")
 safe(f)
end)
T("H2-A05 pending issue cannot credit even if route shadow says BLOCKED",function()
 local f=make(0,0)
 assert(f.issued==1)
 f:tick(300,60,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"))
 safe(f)
end)
T("H2-A06 rejected Native ACK cannot mark waypoint complete",function()
 local f=F({debug_source=true,width=20,reject_native=true})
 f:start();f:emit("MOVE",false,100,0);f:emit("MOVE",true,0,0)
 f:tick(100,0,0);f:tick(200,60,0);assert(f.issued==1)
 f:deliver();f:tick(300,60,0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(not f:has("reason=STEERING_CORNER_HANDOFF"))
 safe(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H2-A real-controller ACK source baseline NOT WH3")
os.exit(fail==0 and 0 or 1)
