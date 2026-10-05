-- T1.6 Transition Transaction runtime gate. Permission remains T1.5; only commit timing/protocol changes.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f) for _,s in ipairs(f.logs) do assert(not s:find('CONTROLLER_FAIL',1,true),s) end end
local function order_v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
  accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end

T('T16-00 BSC successor submit does not commit edge before ACK',function()
 local f=F({cold_idle=true,debug_source=true,width=20});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,100)
 f:tick(100,0,0);f:tick(200,70,0)
 assert(f.issued==1,'expected successor submission')
 assert(not f:has('ACTION_HANDOFF_COMMITTED'),'submission is not commitment')
 f:deliver();f:tick(300,72,0)
 assert(f:has('ACTION_HANDOFF_COMMITTED'),'ACK must commit edge')
 assert(f:has('TRANSITION_EDGE_COMMITTED'),'transaction commit telemetry missing')
 healthy(f)
end)

T('T16-01 rejected successor never commits previous waypoint handoff',function()
 local f=F({cold_idle=true,debug_source=true,width=20,reject_native=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,100)
 f:tick(100,0,0);f:tick(200,70,0)
 assert(f.issued==1 and not f:has('ACTION_HANDOFF_COMMITTED'))
 f:deliver();f:tick(300,72,0)
 assert(f:has('ISSUE_REJECTED'),'expected rejected Native issue')
 assert(not f:has('ACTION_HANDOFF_COMMITTED'),'rejected issue cannot commit edge')
 assert(f:has('TRANSITION_EDGE_ABORTED'),'rejected transition must abort transaction')
 healthy(f)
end)

T('T16-02 exact Native successor adoption uses same edge commit path',function()
 local f=F({cold_idle=true,debug_source=true,width=20,no_calibration=true,native_order_evidence_v3=order_v3});f:start();f.unit.idle=false;f.unit.moving=true
 f.enemy.x=200;f.enemy.z=0
 f:emit('MOVE',false,100,0);local a=f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,100,0)
 f.evidence_record=a;f.unit.target=f.enemy;f:tick(200,100,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'exact immediate Attack should still adopt under T1.5 permission')
 assert(f:has('ACTION_HANDOFF_COMMITTED'),'Native adopt must commit same canonical edge')
 assert(f:has('TRANSITION_EDGE_COMMITTED'),'Native adopt must use transaction commit')
 assert(f.issued==0,'Native adopt should not submit a new command')
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; T1.6 transition transaction permission-neutral gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
