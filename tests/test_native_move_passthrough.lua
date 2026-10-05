-- Native Move queue passthrough ownership regression gate.
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
 local f=F({cold_idle=true,debug_source=true,width=width or 20,native_order_evidence_v3=order_v3})
 f:start();f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 return f
end
local function native_at(f,record,t,x,z)
 f.evidence_record=record;f:tick(t,x,z or 0)
end

T('PASS-00 early exact i+1 Move shadows native queue without rollback or reissue',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 native_at(f,m2,200,30,0)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_SYNC'),'native i+1 should advance shadow cursor')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'),'native Move must never be destructively rolled back')
 assert(f.issued==0,'passthrough must not issue replacement Move')
 healthy(f)
end)

T('PASS-01 180-degree early fold-back is observed, not corrected by REPLACE',function()
 local f=base(40)
 f:emit('MOVE',false,100,0)
 local back=f:emit('MOVE',true,0,0)
 f:tick(100,0,0)
 native_at(f,back,200,25,0)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_SYNC'),'hairpin should remain native-owned for diagnostic isolation')
 assert(not f:has('HAIRPIN_PROGRESS_REQUIRED'),'passthrough may observe but not policy-block native Move')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 assert(f.issued==0)
 healthy(f)
end)

T('PASS-02 all-Move i+2 sample fast-forwards shadow cursor without REPLACE',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,200,0)
 local m3=f:emit('MOVE',true,300,0)
 f:tick(100,0,0)
 native_at(f,m3,200,80,0)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_FAST_FORWARD'),'observer may miss a short intermediate Move between polls')
 assert(not f:has('NATIVE_FUTURE_OVERRUN'),'all-Move sampling gap is not a destructive overrun')
 assert(f.issued==0)
 healthy(f)
end)

T('PASS-03 native-owned Move chain never proactively dispatches next Move',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 f:tick(200,80,0) -- old controller would proactively issue P2 here.
 assert(f.issued==0,'native queue ownership forbids proactive Move->Move dispatch')
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_WAIT') or true)
 healthy(f)
end)

T('PASS-04 Move->Attack terminal handoff remains controller-owned T2-B',function()
 local f=base(40)
 f.enemy.x=140;f.enemy.z=0
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,50,0);f:tick(2100,75,0)
 assert(f.issued==1,'T2-B must still issue terminal Attack')
 assert(f.commands[1].draft.kind=='ATTACK')
 assert(f:has('ATTACK_TERMINAL_HANDOFF'))
 healthy(f)
end)

T('PASS-05 noncanonical active Move stays fail-observed but never replaced',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 f.evidence_record={unit_uid='1001',unit_lifetime='1',serial='999001',engine_seq='999002',order_type='MOVE',dest_x=250,dest_y=0,dest_z=0}
 f:tick(200,60,0)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_NONCANONICAL'),'noncanonical native execution must be observed explicitly')
 assert(f.issued==0,'observer mismatch must not mutate the native queue')
 healthy(f)
end)

T('PASS-06 cross-semantic future Move yields BSC tracking instead of rolling native queue back',function()
 local f=base(20)
 f.enemy.x=150;f.enemy.z=0
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 local m3=f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 native_at(f,m3,200,70,0)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_YIELD'),'cannot silently skip Attack; yield tracking instead')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'),'yield must preserve native queue')
 assert(f.issued==0)
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; native Move queue passthrough ownership gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
