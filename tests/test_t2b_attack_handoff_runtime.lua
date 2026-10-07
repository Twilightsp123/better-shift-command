local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function order_v3(f,u)local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end;return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z} end
local function seed(f)
 f.unit.idle=false;f.unit.moving=true;f.enemy.x=200;f.enemy.z=0
 local m=f:emit('MOVE',false,100,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 return m,a
end
local function four(f)f:tick(100,75,0);f:tick(200,84,0);f:tick(300,90,0);f:tick(400,94,0)end
T('T2B2-RT00 proactive waits for ACK',function()local f=F({cold_idle=true,debug_source=true,width=20});f:start();seed(f);four(f);assert(f.issued==1);assert(not f:has('reason=ATTACK_TERMINAL_HANDOFF'));f:deliver();f:tick(500,95,0);assert(f:has('reason=ATTACK_TERMINAL_HANDOFF'));assert(f:has('TRANSITION_EDGE_COMMITTED'));healthy(f)end)
T('T2B2-RT01 reject no credit',function()local f=F({cold_idle=true,debug_source=true,width=20,reject_native=true});f:start();seed(f);four(f);assert(f.issued==1);f:deliver();f:tick(500,95,0);assert(f:has('TRANSITION_EDGE_ABORTED'));assert(not f:has('reason=ATTACK_TERMINAL_HANDOFF'));healthy(f)end)
T('T2B2-RT02 Native exact Attack uses cache',function()
 local f=F({cold_idle=true,debug_source=true,width=20,no_calibration=true,native_order_evidence_v3=order_v3});f:start()
 local m,a=seed(f);f.evidence_record=m;four(f)
 f.evidence_record=a;f.unit.target=f.enemy;f:tick(500,94.5,0)
 assert(f.issued==0);assert(f:has('NATIVE_SUCCESSOR_ADOPTED'));assert(f:has('reason=ATTACK_TERMINAL_HANDOFF'));assert(f:has('TRANSITION_EDGE_COMMITTED'));healthy(f)
end)
T('T2B2-RT03 early Native Attack fails closed',function()
 local f=F({cold_idle=true,debug_source=true,width=20,no_calibration=true,native_order_evidence_v3=order_v3});f:start()
 local m,a=seed(f);f.evidence_record=m
 f:tick(100,75,0);f:tick(200,84,0);f:tick(300,90,0)
 f.evidence_record=a;f.unit.target=f.enemy;f:tick(400,94,0)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'))
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION') or f:has('NATIVE_ADVANCED_WITHOUT_FRESH_T2B_DECISION'))
 healthy(f)
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
