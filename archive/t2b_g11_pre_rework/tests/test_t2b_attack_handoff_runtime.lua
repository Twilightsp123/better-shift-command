-- T2-B transaction/runtime gate: early Attack permission may change; commit protocol may not.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f) for _,s in ipairs(f.logs) do assert(not s:find('CONTROLLER_FAIL',1,true),s) end end
local function order_v3(f,u)
 local r=f.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
  accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function seed(f)
 f.unit.idle=false;f.unit.moving=true;f.enemy.x=200;f.enemy.z=0
 f:emit('MOVE',false,100,0);return f:emit('ATTACK',true,nil,nil,'2001')
end
local function brake_to_six(f)
 f:tick(100,75,0);f:tick(200,84,0);f:tick(300,90,0);f:tick(400,94,0)
end

T('T2B-00 early straight Attack submits at observed brake boundary but does not pre-ACK commit',function()
 local f=F({cold_idle=true,debug_source=true,width=20});f:start();seed(f);brake_to_six(f)
 assert(f.issued==1,'expected early Attack submission at remaining 6m')
 assert(not f:has('ACTION_COMPLETE') or not f:has('reason=ATTACK_TERMINAL_HANDOFF'),'terminal credit before ACK')
 assert(not f:has('ACTION_HANDOFF_COMMITTED'),'handoff committed before ACK')
 f:deliver();f:tick(500,95,0)
 assert(f:has('reason=ATTACK_TERMINAL_HANDOFF'),'ACK must grant terminal handoff credit')
 assert(f:has('TRANSITION_EDGE_COMMITTED'),'ACK must commit through transaction')
 healthy(f)
end)

T('T2B-01 rejected early Attack never grants terminal credit',function()
 local f=F({cold_idle=true,debug_source=true,width=20,reject_native=true});f:start();seed(f);brake_to_six(f)
 assert(f.issued==1,'expected early Attack submission')
 assert(not f:has('reason=ATTACK_TERMINAL_HANDOFF'),'credit before rejected ACK')
 f:deliver();f:tick(500,95,0)
 assert(f:has('TRANSITION_EDGE_ABORTED'),'reject must abort transaction')
 assert(not f:has('reason=ATTACK_TERMINAL_HANDOFF'),'rejected Attack cannot complete Move')
 healthy(f)
end)

T('T2B-02 exact Native immediate Attack at same brake boundary adopts through shared commit',function()
 local f=F({cold_idle=true,debug_source=true,width=20,no_calibration=true,native_order_evidence_v3=order_v3});f:start()
 local a=seed(f)
 f:tick(100,75,0);f:tick(200,84,0);f:tick(300,90,0)
 f.evidence_record=a;f.unit.target=f.enemy;f:tick(400,94,0)
 assert(f.issued==0,'Native adopt must not submit')
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'expected exact immediate Attack adoption')
 assert(f:has('reason=ATTACK_TERMINAL_HANDOFF'),'Native adoption must grant same terminal credit')
 assert(f:has('TRANSITION_EDGE_COMMITTED'),'Native adoption must share commit path')
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; T2-B arrival-brake transaction gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
