-- H6 negative and positive real-controller synthetic fixture, not WH3 physics.
-- Source failure: 2026-10-09 12:10 uid1006 action5 debt best 5.112033,
-- strict tolerance 3.889415, unresolved 8400ms and no action6->7 ACK.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(name,fn)
 local ok,why=pcall(fn)
 if ok then pass=pass+1;print("PASS "..name)
 else fail=fail+1;print("FAIL "..name.." :: "..tostring(why)) end
end
local function count(f,tag)
 local n=0
 for _,s in ipairs(f.logs) do
  if s:find("] "..tag.." uid=1001 ",1,true) then n=n+1 end
 end
 return n
end
local function base(with_attack,reject)
 local f=F({debug_source=true,width=10,reject_native=reject==true})
 f:start()
 f:emit("MOVE",false,100,0)
 f:emit("MOVE",true,135,0)
 if with_attack then f:emit("ATTACK",true,nil,nil,"2001") end
 f:tick(100,0,0)
 f:tick(200,80,0)
 assert(f.issued==1,"expected predictive MOVE handoff")
 f:deliver();f:tick(300,80,0)
 return f
end
T("H6NP01 post-ACK forward close crossing retires guide debt",function()
 local f=base()
 assert(count(f,"ROUTE_OBLIGATION_TRANSFERRED")==1)
 f:tick(400,96,3.4)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==0)
 f:tick(500,101,3.4)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==1,"close missed guide debt not retired")
 assert(f:has("semantics=GUIDE_ONLY_NOT_PHYSICAL_ARRIVAL"))
 assert(f:has("reason=ROUTE_GUIDE_NEAR_PASS_ACCEPTED"))
 assert(count(f,"ROUTE_OBLIGATION_SATISFIED")==0,"counterfeit physical arrival")
end)
T("H6NP02 wide lateral miss remains unpaid",function()
 local f=base()
 f:tick(400,96,6.3);f:tick(500,101,6.3)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==0)
 assert(count(f,"ROUTE_OBLIGATION_SATISFIED")==0)
end)
T("H6NP03 reverse crossing is not forward passage",function()
 local f=base()
 f:tick(400,105,8);f:tick(500,101,3.4);f:tick(600,96,3.4)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==0)
 assert(count(f,"ROUTE_OBLIGATION_SATISFIED")==0)
end)
T("H6NP04 old guide debt retirement cannot prematurely ATTACK",function()
 local f=base(true)
 f:tick(400,96,3.4);f:tick(500,101,3.4)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==1)
 assert(f.issued==1,"MOVE->ATTACK gated by current MOVE completion")
 assert(count(f,"TRANSITION_EDGE_COMMITTED")==1)
end)
T("H6NP05 rejected Native ACK leaves debt uncredited",function()
 local f=base(false,true)
 f:tick(400,96,3.4);f:tick(500,101,3.4)
 assert(count(f,"TRANSITION_EDGE_COMMITTED")==0)
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==0)
end)
T("H6NP06 unacknowledged U-turn cannot counterfeit near-pass or commit",function()
 local f=F({debug_source=true,width=10});f:start()
 f:emit("MOVE",false,100,0);f:emit("MOVE",true,0,0)
 f:tick(100,0,0);f:tick(200,60,0)
 assert(count(f,"TRANSITION_EDGE_COMMITTED")==0,"U-turn without ACK committed")
 assert(count(f,"ROUTE_GUIDE_NEAR_PASS_ACCEPTED")==0,"U-turn invented physical near-pass")
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H6 SYNTHETIC ONLY; WH3 UNVERIFIED")
os.exit(fail==0 and 0 or 1)
