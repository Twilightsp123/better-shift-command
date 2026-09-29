-- R1 requirements tests; physical classifications here are injected test facts,
-- NOT measurements from WH3. Original v108 assertions are retained in history.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function attacks(f)local n=0;for _,c in ipairs(f.commands)do if c.draft.kind=='ATTACK' then n=n+1 end end;return n end
local function tick(f,a,b,x,deliver)
 for t=a,b,100 do f:tick(t,x,0);if deliver and f.native_pending then f:deliver()end end;healthy(f)
end
local function order_snapshot(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,"NO_ORDER" end
 return {schema=2,epoch='1',unit_uid=u,unit_lifetime=f.bad_lifetime and '2' or r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=f.bad_receipt and '0' or r.serial,
  active_engine_seq=f.bad_sequence and '4294967295' or r.engine_seq,kind=r.order_type,
  target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function entity_snapshot(f,u,now)
 local locked=f.locked_entities or {}
 return {schema=2,complete=not f.entity_incomplete,probe_reason=f.entity_incomplete and 'SYNTHETIC_INCOMPLETE' or 'OK',
  model_ms=f.frozen_ms or now,slot_count=60,live_count=60,dead_count=0,
  local_state0_count=0,local_state1_count=60-#locked,local_state2_count=0,local_state3_count=f.state3_count or 0,
  melee_locked_count=#locked,movement_idle_count=0,movement_pathing_count=f.pathing_count or 57,movement_halted_count=f.halted_count or (60-(f.pathing_count or 57)),
  median_x=f.unit.x,median_z=f.unit.z,motion_complete=true,motion_matched_count=60,previous_model_ms=(f.frozen_ms or now)-100,
  median_vx=f.body_vx or 0,median_vz=f.body_vz or 0,melee_locked_entities=locked}
end
local function combat_snapshot(f,u)
 local targets=f.combat_targets or {}
 return {schema=2,complete=not f.combat_incomplete,probe_reason=f.combat_incomplete and 'SYNTHETIC_INCOMPLETE' or 'OK',
  coarse_contact_count=f.coarse_contact_count or (#targets>0 and 1 or 0),group_count=#targets,
  active_melee_group_count=#targets,active_target_uids=targets}
end
local function last_own(f)
 for i=#f.records,1,-1 do if f.records[i].source=='OUR_CONTROLLER' then return f.records[i] end end
end
local function setup(opts)
 opts=opts or {}
 local f=F({cold_idle=true,width=40,debug_source=true,disable_debug=opts.quiet,native_evidence_v2=opts.evidence==true,
  native_order_evidence=opts.evidence and order_snapshot or nil,native_entity_evidence=opts.evidence and entity_snapshot or nil,
  native_combat_evidence=opts.evidence and combat_snapshot or nil})
 local e2=opts.extra and f:add_enemy_reinforcement('2002',-8,0) or nil
 local e3=opts.future and f:add_enemy_reinforcement('2003',400,0) or nil
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0
 f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f.evidence_record=f:emit('ATTACK',false,nil,nil,'2001')
 f:emit('MOVE',true,opts.exit_x or -100,0)
 if opts.internal then f:emit('MOVE',true,-200,0)end
 if not opts.no_tail then f:emit('ATTACK',true,nil,nil,e3 and '2003' or '2001') end
 f:tick(100);tick(f,200,6000)
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE','setup first exit')
 f:deliver();f.evidence_record=last_own(f);f:tick(6100,-8,0)
 return f,e2,e3
end
T('E03/R04 clear cannot delete 70m of final exit route',function()
 local f=setup();f.unit.target=nil;f.unit.melee=false;tick(f,6200,8100,-30)
 assert(f:has('EXIT_PERMISSION_READY') and attacks(f)==0)
 assert(not f:has('reason=EXIT_DISENGAGEMENT_COMMITTED'))
 tick(f,8200,8500,-99);assert(attacks(f)==1,'route now satisfied, attack must dispatch')
end)
T('E07/E09 recontact revokes current permission without deleting history',function()
 local f,e2=setup({extra=true,no_tail=true});f.unit.target=nil;f.unit.melee=false;e2.x=400
 tick(f,6200,8000,-30);assert(f:has('EXIT_BLOCK_COMMITTED'))
 e2.x=-30;f.unit.melee=true;f.unit.target=e2;tick(f,8100,9500,-30,true)
 assert(f:has('EXIT_PERMISSION_REVOKED') and f:has('EXIT_BLOCK_REASSERT'))
 assert(f:count('EXIT_BLOCK_COMMITTED')==1,'history retained rather than recreated')
end)
for _,kind in ipairs({'NONE','MOVE','ATTACK','INVALID_ATTACK'})do
 T('E10/R10 current recovery independent of successor '..kind,function()
  local f,e2,e3=setup({extra=true,no_tail=kind=='NONE',internal=kind=='MOVE',future=kind=='INVALID_ATTACK'})
  if e3 then e3.hidden=true end
  f.unit.target=e2;f.unit.melee=true;e2.x=-12
  tick(f,6200,14500,-12,true)
  assert(f:count('EXIT_BLOCK_REASSERT')==4,'same budget with real ACK for '..kind)
  assert(f:has('EXIT_RECOVERY_BUDGET_EXHAUSTED'),'explicit failure rather than a hidden forever wait')
  assert(attacks(f)==0)
  for _,cmd in ipairs(f.commands)do assert(cmd.draft.kind=='MOVE' and cmd.draft.x==-100)end
 end)
end
T('E11/R10 progress with constant contact must not cause reassert',function()
 local f,e2=setup({extra=true,exit_x=-500});f.unit.target=e2
 for t=6200,12000,100 do local x=-8-(t-6100)*0.008;e2.x=x;f:tick(t,x,0)end
 assert(f:count('EXIT_BLOCK_REASSERT')==0 and attacks(f)==0);healthy(f)
end)
T('E14/R11 unmeasurable secondary enemy is UNKNOWN not absence',function()
 local f,e2=setup({extra=true});e2.hidden=true;e2.x=-30;f.unit.target=nil;f.unit.melee=true
 tick(f,6200,8800,-30);assert(f:has('unknown=true') and not f:has('EXIT_BLOCK_COMMITTED'))
end)
T('E12/I04 recovery budget does not reset on append or revive after replacement',function()
 local f,e2=setup({extra=true,no_tail=true});f.unit.target=e2;e2.x=-12
 tick(f,6200,14500,-12,true);assert(f:count('EXIT_BLOCK_REASSERT')==4)
 f:emit('MOVE',true,-300,0);tick(f,14600,18000,-12,true);assert(f:count('EXIT_BLOCK_REASSERT')==4)
 f:emit('MOVE',false,200,0);f:tick(18100,-12,0);tick(f,18200,21000,-12,true)
 assert(f:count('EXIT_BLOCK_REASSERT')==4 and f:has('EXTERNAL_REPLACE'))
end)
T('E15/E02 route-done Exit may append another Move without Entity evidence veto',function()
 local f,e2=setup({extra=true,no_tail=true,exit_x=-28});f.unit.target=e2;e2.x=-28
 tick(f,6200,8100,-28,true)
 assert(not f:has('code=BLOCKED_EVIDENCE'),'Center architecture must not fault on unresolved physical evidence')
 local before=f.issued;f:emit('MOVE',true,-100,0);f:tick(8200,-28,0)
 assert(f.issued==before+1 and f.commands[#f.commands].draft.x==-100)
end)
T('E08 closed complete block is not reopened by later collision',function()
 local f,e2=setup({extra=true,no_tail=true});f.unit.target=nil;f.unit.melee=false;e2.x=400
 tick(f,6200,8200,-100,true);assert(f:has('EXIT_BLOCK_CLOSED'))
 e2.x=-100;f.unit.target=e2;f.unit.melee=true;local before=f.issued
 tick(f,8300,9900,-100,true);assert(f.issued==before,'do not replay old exit')
 f:emit('MOVE',true,-200,0);f:tick(10000,-100,0)
 assert(f.issued==before+1 and f.commands[#f.commands].draft.x==-200,'new route can begin')
end)
T('M08/R12 missed prediction has explicit BLOCKED_ROUTE preserving suffix',function()
 local f=F({debug_source=true});f:start();f.enemy.x=300;f.enemy.z=0
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,80,0);f:deliver();f:tick(300,120,50);f:tick(400,200,0)
 tick(f,500,10000,200,true)
 assert(f:has('BLOCKED_ROUTE') and f:has('ROUTE_UNRECOVERABLE') and attacks(f)==0)
 assert(not f:has('ROUTE_OBLIGATION_SATISFIED'))
end)
-- RE07 formally retracted state74/coarse-contact as per-Entity runtime melee evidence.
-- R08 residual-contact coverage moved to test_r1_v3_second_charge.lua where it is
-- expressed with target-specific ContactPair events plus a frozen ExitBodyCohort.
-- The six retired V2 fresh-lock cases now live in release history; target-specific post-exit
-- coverage is owned by test_r1_v3_second_charge.lua using ContactPair + frozen Exit cohort.
T('R06 ordinary first Attack still completes when V2 entity/combat producer is unavailable',function()
 local f=F({cold_idle=true,debug_source=true,native_evidence_v2=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0
 f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 tick(f,100,5000,-8,true)
 assert(f:has('ATTACK_HOLD_DONE'),'legacy FEG must remain authoritative for ordinary first Attack')
 assert(f.issued>=1 and f.commands[1].draft.kind=='MOVE')
 assert(not f:has('POST_EXIT_FRESH_ENGAGEMENT_UNAVAILABLE'))
end)
T('R08 unfinished Exit requires majority CA pathing, not merely absence of majority melee lock',function()
 local f,e2=setup({extra=true,evidence=true});f.unit.target=e2;f.unit.melee=true;e2.x=-30
 f.locked_entities={'s1','s2','s3'};f.pathing_count=0;f.halted_count=57;f.combat_targets={'2002'}
 tick(f,6200,8100,-30,true)
 assert(not f:has('EXIT_PERMISSION_READY'),'halted majority before route completion is not an operable exiting body')
 f.pathing_count=57;f.halted_count=3;tick(f,8200,9000,-30,true)
 assert(f:has('EXIT_PERMISSION_READY'),'resumed majority pathing may establish current Exit permission')
end)
T('R10 residual stragglers alone do not reassert a stalled Exit under V2 evidence',function()
 local f,e2=setup({extra=true,evidence=true,exit_x=-100});f.unit.target=e2;f.unit.melee=true;e2.x=-12
 f.locked_entities={'s1','s2','s3'};f.pathing_count=57;f.state3_count=0;f.combat_targets={'2002'}
 tick(f,6200,11000,-12,true)
 assert(f:count('EXIT_BLOCK_REASSERT')==0,'minor residual contact must not trigger recovery of an otherwise operable body')
 assert(attacks(f)==0)
end)
T('N02 decision only exact native sequence adopts without a duplicate command',function()
 local f=F({cold_idle=true,debug_source=true,native_evidence_v2=true,native_order_evidence=order_snapshot,native_entity_evidence=entity_snapshot,native_combat_evidence=combat_snapshot});f:start()
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f.unit.target=f.enemy;f:tick(300,100,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED') and f.issued==0);healthy(f)
end)
T('N04/R11 exact premature native successor is rolled back to the same unfinished Move',function()
 local f=F({cold_idle=true,debug_source=true,native_evidence_v2=true,native_order_evidence=order_snapshot,native_entity_evidence=entity_snapshot,native_combat_evidence=combat_snapshot});f:start()
 f:emit('MOVE',false,100,0);f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001')
 f.unit.target=f.enemy;f:tick(100,20,0)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'))
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION') and f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE' and f.commands[1].draft.x==100)
 healthy(f)
end)
T('N03/R11 wrong native sequence cannot adopt even at same target',function()
 local f=F({cold_idle=true,debug_source=true,native_evidence_v2=true,native_order_evidence=order_snapshot,native_entity_evidence=entity_snapshot,native_combat_evidence=combat_snapshot});f:start()
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f.bad_sequence=true;f.unit.target=f.enemy;f:tick(300,100,0)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED') and f:has('BLOCKED_EXECUTION_IDENTITY'));healthy(f)
end)
T('R11 stale entity sample must not renew residual permission',function()
 local f,e2=setup({extra=true,evidence=true});f.unit.target=nil;f.unit.melee=true;f.locked_entities={'e1'};f.combat_targets={'2002'};f.frozen_ms=6200;e2.x=-30
 tick(f,6200,8100,-30);assert(not f:has('EXIT_PERMISSION_READY') and attacks(f)==0)
end)
T('R11 incomplete entity sample remains telemetry and cannot veto route-complete A2',function()
 local f=setup({evidence=true});f.unit.target=nil;f.unit.melee=false;f.entity_incomplete=true;f.combat_targets={'2001'}
 tick(f,6200,9000,-100)
 assert(not f:has('code=BLOCKED_EVIDENCE'),'incomplete EntitySnapshot may not create a hard behavior fault')
 assert(attacks(f)>=1,'route-complete Center A2 should issue despite incomplete entity evidence')
end)
T('O04/R03 debug off does not disable recovery or fault reporting',function()
 local f,e2=setup({extra=true,no_tail=true,quiet=true});e2.x=-12;f.unit.target=e2
 tick(f,6200,14500,-12,true);assert(f:count('EXIT_BLOCK_REASSERT')==4 and f:has('BLOCKED_EXECUTION'))
end)
T('A07 no target no movement after ACK has explicit execution fault',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 f.unit.idle=true;f.unit.moving=false;f.unit.melee=false;f.unit.target=nil;tick(f,100,13000,0)
 assert(f:has('ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE') and f.issued==0)
end)
T('R4 widened dispatch pipeline does not batch an Attack behind four OTHER issues',function()
 local f=F({cold_idle=true,debug_source=true,two_units=true,width=40});local u3=f:add_late_local('1003',0,0);local u4=f:add_late_local('1004',0,0);local u5=f:add_late_local('1005',0,0)
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 for _,u in ipairs({'1002','1003','1004','1005'})do f:emit('MOVE',false,10,0,nil,u);f:emit('MOVE',true,20,0,nil,u)end
 f:tick(100,-8,0);f.unit2.x=10;u3.x=10;u4.x=10;u5.x=10;f:tick(200,-8,0)
 assert(f.pending_count==4);tick(f,300,4900,-8)
 assert(f:has('ATTACK_HOLD_DONE uid=1001'),'attack observation must finish while other units are pending')
 assert(f.native_by_uid['1001'],'R4 must dispatch the attack tail immediately instead of waiting for a four-slot batch to drain')
 assert(f.pending_count==5,'the widened pipeline must carry the four existing issues plus the attack tail')
 healthy(f)
end)
T('R09/R11 previously valid body permit is revoked when samples stop refreshing',function()
 local f,e2=setup({extra=true,evidence=true});f.unit.target=nil;f.unit.melee=true;f.locked_entities={'e1'};f.combat_targets={'2002'};e2.x=-30
 tick(f,6200,8100,-30);assert(f:has('EXIT_PERMISSION_READY'))
 f.frozen_ms=8100;tick(f,8200,9400,-30)
 assert(f:has('EXIT_PERMISSION_REVOKED') and attacks(f)==0)
end)
T('R11 missing incomplete evidence never overrides a known active Move via stale target',function()
 local f=setup({evidence=true});f.unit.target=f.enemy;f.unit.melee=false
 tick(f,6200,8500,-30)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED') and not f:has('CURRENT_TARGET_IS_NOT_ACTION_ID'))
end)
for _,bad in ipairs({'bad_lifetime','bad_receipt'}) do
 T('N03/R11 reused native sequence cannot adopt wrong '..bad,function()
  local f=F({cold_idle=true,debug_source=true,native_evidence_v2=true,native_order_evidence=order_snapshot,native_entity_evidence=entity_snapshot,native_combat_evidence=combat_snapshot});f:start()
  f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
  f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f[bad]=true
  f.unit.target=f.enemy;f:tick(300,100,0)
  assert(not f:has('NATIVE_SUCCESSOR_ADOPTED') and f:has('BLOCKED_EXECUTION_IDENTITY'))
 end)
end
T('R11 uncertain native successor must not be overwritten by recovery of old Move',function()
 local f=setup();f.enemy.x=-8;f.unit.target=f.enemy;f.unit.melee=true
 tick(f,6200,10000,-8,true)
 assert(f:has('BLOCKED_EXECUTION_IDENTITY') and f.issued==1)
end)
print('ACTUAL_INTERPRETER='.._VERSION..'; R1 decision tests, synthetic evidence producer; WH3 mapping NOT verified')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
