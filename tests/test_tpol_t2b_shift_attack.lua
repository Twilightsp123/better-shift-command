-- TPOL T2-B Move->Attack terminal-handoff regression gate under native Move passthrough ownership.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f) for _,s in ipairs(f.logs) do assert(not s:find('CONTROLLER_FAIL',1,true),s) end end
local function order_v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
  accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function base(native)
 local cfg={cold_idle=true,debug_source=true,width=40};if native then cfg.native_order_evidence_v3=order_v3 end
 local f=F(cfg);f:start();f.enemy.x=200;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true;return f
end
local function walk(f,to_x)
 f:tick(100,0,0);local t=1100;local x=10
 while x<=to_x do f:tick(t,x,0);t=t+1000;x=x+10 end
 if (to_x%10)~=0 then f:tick(t,to_x,0);t=t+1000 end
 return t
end
local function native_at(f,r,t,x) f.evidence_record=r;f.unit.target=f.enemy;f:tick(t,x,0) end

T('T2B-00 proactive terminal corridor still issues Attack',function()
 local f=base(false);f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001');walk(f,75)
 assert(f.issued==1 and f.commands[1].draft.kind=='ATTACK');assert(f:has('ATTACK_TERMINAL_HANDOFF'));healthy(f)
end)

T('T2B-01 exact immediate native Attack inside terminal corridor adopts',function()
 local f=base(true);f:emit('MOVE',false,100,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk(f,70);native_at(f,a,t,75)
 assert(f:has('ATTACK_TERMINAL_HANDOFF'));assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'));assert(f.issued==0);healthy(f)
end)

T('T2B-02 far-early immediate native Attack remains rollback protected',function()
 local f=base(true);f:emit('MOVE',false,100,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk(f,50);native_at(f,a,t,55)
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION'));assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE');healthy(f)
end)

T('T2B-03 sampled Attack beyond an intermediate Move yields instead of replacing native queue',function()
 local f=base(true);f:emit('MOVE',false,100,0);f:emit('MOVE',true,150,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,20,0);native_at(f,a,200,20)
 assert(f:has('NATIVE_MOVE_PASSTHROUGH_YIELD'));assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'));assert(f.issued==0);healthy(f)
end)

T('T2B-04 target/receipt mismatch cannot false-adopt terminal Attack',function()
 local f=base(true);f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk(f,70)
 f.evidence_record={unit_uid='1001',unit_lifetime='1',serial='999001',engine_seq='999002',order_type='ATTACK',target_uid='2002',dest_x=0,dest_z=0}
 f:tick(t,75,0)
 assert(not f:has('ATTACK_TERMINAL_HANDOFF'));assert(f:has('ACTIVE_EXECUTION_NOT_CANONICAL'));assert(f.issued==0);healthy(f)
end)

T('T2B-05 short Move leg cannot be swallowed before bounded progress',function()
 local f=F({cold_idle=true,debug_source=true,width=40,native_order_evidence_v3=order_v3})
 f:start();f.enemy.x=100;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,20,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,4,0);native_at(f,a,2100,8)
 assert(not f:has('ATTACK_TERMINAL_HANDOFF'));assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'));healthy(f)
end)

T('T2B-06 high-angle Attack requires extra progress',function()
 local f=F({cold_idle=true,debug_source=true,width=40});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,50,0);f:tick(2100,75,0);assert(f.issued==0)
 f:tick(3100,86,0);assert(f.issued==1 and f.commands[1].draft.kind=='ATTACK');assert(f:has('ATTACK_TERMINAL_HANDOFF'));healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; TPOL T2-B under native Move passthrough')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
