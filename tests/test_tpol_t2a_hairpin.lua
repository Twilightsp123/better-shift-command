-- T2-A hairpin/U-turn safety regression gate.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print('PASS '..n) else fail=fail+1;print('FAIL '..n..' :: '..tostring(e)) end
end
local function healthy(f)
 for _,s in ipairs(f.logs) do assert(not s:find('CONTROLLER_FAIL',1,true),s) end
end
local function order_v3(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=r.serial,
  active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,
  dest_x=r.dest_x,dest_z=r.dest_z}
end
local function base(width)
 local f=F({cold_idle=true,debug_source=true,width=width or 40,native_order_evidence_v3=order_v3})
 f:start();f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 return f
end
local function native_at(f,record,t,x,z)
 f.evidence_record=record;f:tick(t,x,z or 0)
end

T('HAIRPIN-00 exact 180deg successor at 25 percent must not soft-adopt',function()
 local f=base(40)
 f:emit('MOVE',false,100,0)
 local back=f:emit('MOVE',true,0,0)
 f:tick(100,0,0)
 native_at(f,back,200,25,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'quarter-leg U-turn must not adopt')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'quarter-leg U-turn must restore current Move')
 healthy(f)
end)

T('HAIRPIN-01 exact 180deg successor at 60 percent must still not soft-adopt',function()
 local f=base(40)
 f:emit('MOVE',false,100,0)
 local back=f:emit('MOVE',true,0,0)
 f:tick(100,0,0)
 native_at(f,back,200,60,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'mid-leg U-turn must not fold formation early')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'mid-leg U-turn must remain protected')
 healthy(f)
end)

T('HAIRPIN-02 exact 180deg successor may adopt only very near waypoint',function()
 local f=base(40)
 f:emit('MOVE',false,100,0)
 local back=f:emit('MOVE',true,0,0)
 f:tick(100,0,0)
 native_at(f,back,200,96,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'near-waypoint U-turn should be allowed to adopt')
 assert(f:has('MOVE_STEERING_HANDOFF'),'near U-turn needs explicit completion credit')
 healthy(f)
end)

T('HAIRPIN-03 90deg bounded corner remains smooth',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local turn=f:emit('MOVE',true,100,100)
 f:tick(100,0,0)
 native_at(f,turn,200,70,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'ordinary 90deg corner must keep T2-A smoothing')
 healthy(f)
end)

T('HAIRPIN-04 i+2 remains hard overrun even near U-turn waypoint',function()
 local f=base(40)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,0,0)
 local third=f:emit('MOVE',true,100,0)
 f:tick(100,0,0)
 native_at(f,third,200,96,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'i+2 cannot borrow hairpin permission')
 assert(f:has('NATIVE_FUTURE_OVERRUN'),'i+2 must remain hard overrun')
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; TPOL T2-A hairpin/U-turn safety gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
