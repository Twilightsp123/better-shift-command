-- H1 integration probe: observe the legacy issue/adopt decisions, never alter them.
local Fixture=assert(loadfile(assert(arg[2])))().new
local passed,failed=0,0
local function T(name,fn)
 local ok,why=pcall(fn)
 if ok then passed=passed+1;print("PASS "..name)
 else failed=failed+1;print("FAIL "..name.." :: "..tostring(why)) end
end
local function native(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
   complete=true,active=true,known=true,
   accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,
   kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function setup(next_x,next_z,calibration)
 local f=Fixture({cold_idle=true,debug_source=true,width=20,
   no_calibration=calibration~=true,native_order_evidence_v3=native})
 f:start();f.unit.idle=false;f.unit.moving=true
 local first=f:emit("MOVE",false,100,0)
 local second=f:emit("MOVE",true,next_x,next_z)
 f.evidence_record=first
 return f,first,second
end
local function warm(f)
 for _,x in ipairs({{100,0},{200,30},{300,50},{400,70}}) do f:tick(x[1],x[2],0) end
end
local function logs(f,prefix)
 local found={}
 for _,line in ipairs(f.logs) do if line:find(prefix,1,true) then found[#found+1]=line end end
 return found
end
local function contains(f,prefix,needle)
 for _,line in ipairs(logs(f,prefix)) do
   if line:find(needle,1,true) then return true end
 end
 return false
end
local function healthy(f)
 for _,line in ipairs(f.logs) do
  assert(not line:find("CONTROLLER_FAIL",1,true),line)
 end
end
T("H1-RT00 proactive early U-turn continues legacy issue but H1 says BLOCKED",function()
 local f=Fixture({debug_source=true,width=20})
 f:start();f:emit("MOVE",false,100,0);f:emit("MOVE",true,0,0)
 f:tick(100,0,0);f:tick(200,60,0)
 assert(f.issued==1,"H1 must not change original proactive SC1 U-turn")
 assert(contains(f,"H1_SHADOW_ISSUE","verdict=BLOCKED"),
   "shadow must detect U-turn before its waypoint")
 assert(contains(f,"H1_SHADOW_ISSUE","legacy_issue=true"),
   "observer must record that legacy issue was authorized")
 healthy(f)
end)
T("H1-RT01 proactive safe forward chord keeps debt in shadow",function()
 local f=Fixture({debug_source=true,width=20})
 f:start();f:emit("MOVE",false,100,0);f:emit("MOVE",true,200,0)
 f:tick(100,0,0);f:tick(200,70,0)
 assert(f.issued==1,"legacy Move->Move proactive handoff changed")
 assert(contains(f,"H1_SHADOW_ISSUE","verdict=DEBT_PRESERVED"),
   "forward chord ought to keep unpaid route debt")
 healthy(f)
end)
T("H1-RT02 frozen 180-degree Native proof cannot be replaced by post-turn position",function()
 local f,_,second=setup(0,0,false);warm(f)
 assert(contains(f,"H1_SHADOW_CURRENT","verdict=BLOCKED"),"H1 pre-promotion proof missing")
 f.evidence_record=second;f:tick(500,72,0)
 assert(contains(f,"H1_SHADOW_ADOPT","frozen_verdict=BLOCKED"),"missing frozen shadow")
 assert(not f:has("NATIVE_SUCCESSOR_ADOPTED"),"G turnback guard changed")
 healthy(f)
end)
T("H1-RT03 90-degree legacy Native credit remains, while H1 flags route conflict",function()
 local f,_,second=setup(100,100,false);warm(f)
 assert(contains(f,"H1_SHADOW_CURRENT","verdict=BLOCKED"),"90-degree cut not recognized")
 f.evidence_record=second;f:tick(500,72,0)
 assert(contains(f,"H1_SHADOW_ADOPT","frozen_verdict=BLOCKED"),"shadow must be pre-promotion")
 assert(f:has("NATIVE_SUCCESSOR_ADOPTED"),"H1 must not change legacy 90-degree adopt")
 assert(f:has("STEERING_CORNER_COMMITTED"),"H1 must not change T1.6 credit")
 healthy(f)
end)
T("H1-RT04 3-node straight Native route remains continuous",function()
 local f,_,second=setup(200,0,false);warm(f)
 assert(contains(f,"H1_SHADOW_CURRENT","verdict=DEBT_PRESERVED"),
    "pre-promotion collinear path not represented")
 f.evidence_record=second;f:tick(500,72,0)
 assert(contains(f,"H1_SHADOW_ADOPT","frozen_verdict=DEBT_PRESERVED"),
    "collinear frozen verdict missing")
 assert(f:has("NATIVE_SUCCESSOR_ADOPTED"))
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 healthy(f)
end)
print("TOTAL "..passed.." PASS "..failed.." FAIL; H1 OBSERVATION ONLY NOT WH3")
os.exit(failed==0 and 0 or 1)
