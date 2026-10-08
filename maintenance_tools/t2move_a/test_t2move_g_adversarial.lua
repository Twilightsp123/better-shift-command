-- T2-MOVE-G: exact-controller route semantics under adversarial waypoint layouts.
-- No WH3 process. Expected policy behavior is specified before any controller repair.
local Fixture=assert(loadfile(assert(arg[2])))().new
local passed,failed=0,0
local function T(name,fn)
 local ok,why=pcall(fn)
 if ok then passed=passed+1;print("PASS "..name)
 else failed=failed+1;print("FAIL "..name.." :: "..tostring(why)) end
end
local function native(f,u)
 local map=f.orders_by_uid or {}
 local r=map[u]
 if not r then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=r.serial,
  active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,
  dest_x=r.dest_x,dest_z=r.dest_z}
end
local function start(opts)
 opts=opts or {}
 opts.cold_idle=true;opts.debug_source=true;opts.no_calibration=true
 opts.width=20;opts.native_order_evidence_v3=native
 local f=Fixture(opts);f:start()
 f.unit.idle=false;f.unit.moving=true
 f.orders_by_uid={}
 return f
end
local function plan(f,points,u)
 u=u or "1001"
 local cmds={}
 for i,p in ipairs(points) do
  cmds[i]=f:emit("MOVE",i~=1,p[1],p[2],nil,u)
 end
 f.orders_by_uid[u]=cmds[1]
 return cmds
end
local function step(f,t,x,z,x2,z2)
 if x2~=nil then f.unit2.x=x2;f.unit2.z=z2 or 0 end
 f:tick(t,x,z)
end
local function warm(f)
 for _,row in ipairs({{100,0},{200,30},{300,50},{400,70}}) do
  step(f,row[1],row[2],0,row[2],0)
 end
end
local function entries(f,tag,uid)
 local n=0
 for _,line in ipairs(f.logs) do
  if line:find("] "..tag.." uid="..uid,1,true) then n=n+1 end
 end
 return n
end
local function trace(f,tag)
 local out={}
 for _,line in ipairs(f.logs) do
  if line:find(tag,1,true) then out[#out+1]=line end
 end
 return table.concat(out," | ")
end
local function safe(f)
 for _,line in ipairs(f.logs) do assert(not line:find("CONTROLLER_FAIL",1,true),line) end
end
T("G-RT00 three collinear MOVE nodes commit exactly one edge each",function()
 local f=start();local a=plan(f,{{100,0},{200,0},{300,0}})
 warm(f)
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"),"missing first proof")
 f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"first MOVE missing")
 for _,v in ipairs({{600,120},{700,140},{800,160},{900,170}}) do step(f,v[1],v[2],0) end
 assert(entries(f,"ROUTE_OBLIGATION_SATISFIED","1001")>=1,"P1 route debt not paid")
 f.orders_by_uid["1001"]=a[3];step(f,1000,172,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==2,"second MOVE missing: "..trace(f,"NATIVE_SUCCESSOR"))
 assert(entries(f,"TRANSITION_EDGE_COMMITTED","1001")==2,"double/missing commit")
 assert(f.issued==0,"native exact edges were reissued")
 safe(f)
end)
T("G-RT01 180-degree reversal cannot drop distant waypoint via steering credit",function()
 local f=start();local a=plan(f,{{100,0},{0,0}})
 warm(f)
 f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==0,
  "180-degree fold-back adopted 28m before waypoint; hidden route loss: "..trace(f,"ACTION_HANDOFF_COMMITTED"))
 assert(entries(f,"STEERING_CORNER_COMMITTED","1001")==0,"early 180-degree waypoint completed")
 safe(f)
end)
T("G-RT02 135-degree backtracking cannot earn distant steering completion",function()
 local f=start();local a=plan(f,{{100,0},{30,70}})
 warm(f)
 f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==0,"backward successor skipped inbound waypoint")
 assert(entries(f,"STEERING_CORNER_COMMITTED","1001")==0,"135-degree premature completion")
 safe(f)
end)
T("G-RT03 90-degree corner keeps bounded SC1 early steering",function()
 local f=start();local a=plan(f,{{100,0},{100,100}})
 warm(f);f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"safe lateral corner blocked")
 assert(entries(f,"STEERING_CORNER_COMMITTED","1001")==1,"SC1 credit lost")
 assert(entries(f,"ROUTE_OBLIGATION_TRANSFERRED","1001")==0,"STEERING must not create PATH debt")
 safe(f)
end)
T("G-RT04 dense short leg with reversal cannot discard unresolved P1 debt",function()
 local f=start();local a=plan(f,{{100,0},{105,0},{80,0}})
 warm(f);f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"first legal PATH_SAFE edge missing")
 assert(entries(f,"ROUTE_OBLIGATION_TRANSFERRED","1001")==1,"P1 obligation missing")
 for _,v in ipairs({{600,85},{700,89},{800,93},{900,94}}) do step(f,v[1],v[2],0) end
 f.orders_by_uid["1001"]=a[3];step(f,1000,94.5,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"dense reversal skipped owed P1/P2")
 assert(entries(f,"TRANSITION_EDGE_COMMITTED","1001")==1,"unsafe second edge committed")
 safe(f)
end)
T("G-RT05 two outstanding SC3 route debts are retained across legal exact MOVE edges",function()
 local f=start();local a=plan(f,{{100,0},{105,0},{110,0},{200,0}})
 warm(f);f.orders_by_uid["1001"]=a[2];step(f,500,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"missing P1-P2 adoption")
 for _,v in ipairs({{600,85},{700,89},{800,93},{900,94}}) do step(f,v[1],v[2],0) end
 f.orders_by_uid["1001"]=a[3];step(f,1000,94.5,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==2,
  "P2-P3 legal soft-SC3 edge should adopt: "..trace(f,"NATIVE_SUCCESSOR"))
 assert(entries(f,"ROUTE_OBLIGATION_TRANSFERRED","1001")==2,
  "two canonical waypoint debts must be recorded separately")
 assert(entries(f,"ROUTE_OBLIGATION_SATISFIED","1001")==0,
  "two unvisited nodes may not be silently credited")
 safe(f)
end)
T("G-RT06 two units isolate V3 evidence and independently reject revision drift",function()
 local f=start({two_units=true})
 f.unit2.idle=false;f.unit2.moving=true
 local a=plan(f,{{100,0},{200,0}},"1001")
 local b=plan(f,{{100,0},{200,0}},"1002")
 warm(f)
 assert(entries(f,"T2MOVE_D_SHADOW_CAPTURE","1001")>0,"unit 1 proof absent")
 assert(entries(f,"T2MOVE_D_SHADOW_CAPTURE","1002")>0,"unit 2 proof absent")
 f.revision["1002"]="999" -- unseen Native revision change for unit 2 only
 f.orders_by_uid["1001"]=a[2];f.orders_by_uid["1002"]=b[2]
 step(f,500,72,0,72,0)
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1001")==1,"unit 1 was affected by unit 2 state")
 assert(entries(f,"NATIVE_SUCCESSOR_ADOPTED","1002")==0,"unit 2 stale revision adopted")
 assert(entries(f,"TRANSITION_EDGE_COMMITTED","1001")==1,"unit 1 commit missing")
 assert(entries(f,"TRANSITION_EDGE_COMMITTED","1002")==0,"unit 2 false credit")
 safe(f)
end)
print("TOTAL "..passed.." PASS "..failed.." FAIL; G ISOLATED REAL-CONTROLLER FIXTURES, NOT WH3")
os.exit(failed==0 and 0 or 1)
