-- H4-S Native exact i+1 MOVE parity with proactive soft rounded turn.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print("PASS "..n)else fail=fail+1;print("FAIL "..n.." :: "..tostring(e))end end
local function v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=3,epoch="1",unit_uid=u,unit_lifetime=r.unit_lifetime,
    complete=true,active=true,known=true,accepted_journal_serial=r.serial,
    active_engine_seq=r.engine_seq,kind=r.order_type,
    dest_x=r.dest_x,dest_z=r.dest_z,target_uid=r.target_uid}
end
local function base(x,z)
 local f=F({cold_idle=true,debug_source=true,no_calibration=true,width=20,native_order_evidence_v3=v3})
 f:start();f.unit.idle=false;f.unit.moving=true
 local a=f:emit("MOVE",false,100,0)
 local b=f:emit("MOVE",true,x,z)
 f.evidence_record=a
 for _,r in ipairs({{100,0},{200,30},{300,50},{400,70}})do f:tick(r[1],r[2],0)end
 return f,b
end
local function n(f,x)
 local num=0;for _,s in ipairs(f.logs)do if s:find("] "..x.." uid=1001 ",1,true) then num=num+1 end end;return num
end
local function safe(f)for _,s in ipairs(f.logs)do assert(not s:find("CONTROLLER_FAIL",1,true),s)end end
T("H4SN-01 Native queued 90-degree i+1 adopts soft corner without returning to old waypoint",function()
 local f,b=base(100,100)
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"),"frozen Native proof missing")
 f.evidence_record=b;f:tick(500,72,0)
 assert(n(f,"NATIVE_SUCCESSOR_ADOPTED")==1,"Native 90 soft corner was rolled back")
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(f:has("reason=H4_SOFT_WAYPOINT_ACCEPTED"))
 assert(not f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 safe(f)
end)
T("H4SN-02 Native queued U-turn may use soft bounded timing if explicit frozen proof exists",function()
 local f,b=base(0,0)
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"))
 f.evidence_record=b;f:tick(500,72,0)
 assert(n(f,"NATIVE_SUCCESSOR_ADOPTED")==1,"Native 180 soft corner rolled back")
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==1)
 assert(f:has("reason=H4_SOFT_WAYPOINT_ACCEPTED"))
 safe(f)
end)
T("H4SN-03 native collinear still carries physically payable debt",function()
 local f,b=base(200,0)
 assert(f:has("T2MOVE_D_SHADOW_CAPTURE"))
 f.evidence_record=b;f:tick(500,72,0)
 assert(n(f,"NATIVE_SUCCESSOR_ADOPTED")==1)
 assert(f:has("ROUTE_OBLIGATION_TRANSFERRED"))
 assert(not f:has("reason=H4_SOFT_WAYPOINT_ACCEPTED"))
 safe(f)
end)
T("H4SN-04 stale Native revision remains fail closed",function()
 local f,b=base(100,100)
 f.revision["1001"]="999";f.evidence_record=b;f:tick(500,72,0)
 assert(n(f,"NATIVE_SUCCESSOR_ADOPTED")==0)
 assert(n(f,"TRANSITION_EDGE_COMMITTED")==0)
 safe(f)
end)
print("TOTAL "..pass.." PASS "..fail.." FAIL; H4 Native only NOT WH3")
os.exit(fail==0 and 0 or 1)
