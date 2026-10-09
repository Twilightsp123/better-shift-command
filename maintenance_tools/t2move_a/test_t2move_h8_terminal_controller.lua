-- H8 real shipped Lua controller + synthetic V3 CA adapter; not a WH3 physics replay.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(name,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print("PASS "..name)
 else fail=fail+1;print("FAIL "..name.." :: "..tostring(e)) end
end
local function n(f,tag)
 local cnt=0
 for _,line in ipairs(f.logs) do
  if line:find("] "..tag.." uid=1001 ",1,true) then cnt=cnt+1 end
 end
 return cnt
end
local function v3(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=r.serial,
  active_engine_seq=r.engine_seq,kind=r.order_type,dest_x=r.dest_x,dest_z=r.dest_z,
  target_uid=r.target_uid}
end
local function fixture(p,with_i2)
 local f=F({cold_idle=true,debug_source=true,width=40,no_calibration=false,native_order_evidence_v3=v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local m=f:emit("MOVE",false,100,0)
 if with_i2 then f:emit("MOVE",true,130,0) end
 f:emit("ATTACK",true,nil,nil,"2001")
 f.evidence_record=m
 f:tick(100,0,0)
 f:tick(200,40,0)
 f:tick(300,p,0)
 for i=4,13 do f:tick(i*100,p,0) end
 return f
end
local function healthy(f)
 for _,line in ipairs(f.logs) do assert(not line:find("CONTROLLER_FAIL",1,true),line) end
end
T("H8C01 stalled current Native MOVE at 16m triggers proactive ATTACK",function()
 local f=fixture(84,false)
 assert(n(f,"DISPATCH_ATTACK")==1,"native current MOVE liveness unsolved; logs="..table.concat(f.logs," | "))
 assert(f:has("reason=ATTACK_NATIVE_MOVE_STALL_TERMINAL"))
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0,"no credit before Native ACK")
 f:deliver();f:tick(1400,84,0)
 assert(n(f,"OWN_ATTACK_ACK")==1,"proactive ATTACK Native ACK missing")
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 healthy(f)
end)
T("H8C02 stationary too far from MOVE terminal remains blocked",function()
 local f=fixture(65,false)
 assert(n(f,"DISPATCH_ATTACK")==0)
 healthy(f)
end)
T("H8C03 no Native current MOVE identity is never a terminal proof",function()
 local f=fixture(84,false)
 -- Positive control already issued before override; testing requires identity
 -- missing throughout, so use a second fixture with its adapter disabled.
 local g=F({cold_idle=true,debug_source=true,width=40,no_calibration=false,native_order_evidence_v3=v3})
 g:start();g.unit.idle=false;g.unit.moving=true
 g:emit("MOVE",false,100,0)
 g:emit("ATTACK",true,nil,nil,"2001")
 for _,r in ipairs({{100,0},{200,40},{300,84},{400,84},{500,84},{600,84},{700,84},{800,84},{900,84},{1000,84},{1100,84},{1200,84},{1300,84}}) do g:tick(r[1],r[2],0) end
 assert(n(g,"DISPATCH_ATTACK")==0,"without current Native V3 witness issued ATTACK")
 healthy(g)
end)
T("H8C04 queued i+2 ATTACK cannot skip intermediate MOVE",function()
 local f=fixture(84,true)
 assert(n(f,"DISPATCH_ATTACK")==0)
 healthy(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; SYNTHETIC V3 CONTROLLER NOT WH3")
os.exit(fail==0 and 0 or 1)
