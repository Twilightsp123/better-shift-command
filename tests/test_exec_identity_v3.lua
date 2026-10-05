-- SC6: authoritative V3 execution-identity reconciliation regressions.
-- These tests deliberately keep V2 disabled so a V2 wiring regression fails loudly.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function order_v3(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=f.bad_lifetime and '2' or r.unit_lifetime,
  complete=true,active=true,known=true,accepted_journal_serial=f.bad_receipt and '0' or r.serial,
  active_engine_seq=f.bad_sequence and '4294967295' or r.engine_seq,kind=r.order_type,
  target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
local function base()
 local f=F({cold_idle=true,debug_source=true,native_order_evidence_v3=order_v3})
 f:start();f.enemy.x=300;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 return f
end
T('SC6 V3_ONLY_SUCCESSOR_READY adopts exact immediate Attack',function()
 local f=base()
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f.unit.target=f.enemy;f:tick(300,100,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'V3 exact successor should adopt')
 assert(f:has('provider=V3'),'adoption must name V3 provider')
 assert(f.issued==0,'adoption must not duplicate command')
 healthy(f)
end)
T('SC6 V3_ONLY_SUCCESSOR_EARLY_ROLLBACK restores unfinished current Move',function()
 local f=base()
 f:emit('MOVE',false,100,0);f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001')
 f.unit.target=f.enemy;f:tick(100,20,0)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'))
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION') and f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 assert(f:has('provider=V3'))
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE' and f.commands[1].draft.x==100)
 healthy(f)
end)
T('SC6 V3_FUTURE_OVERRUN_ROLLBACK never skips canonical intermediates',function()
 local f=base()
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 f:emit('MOVE',true,200,0)
 local far=f:add_enemy_reinforcement('2002',400,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2002')
 f.unit.target=far;f:tick(100,20,0)
 assert(f:has('NATIVE_FUTURE_OVERRUN'),'overrun must be explicit')
 assert(f:has('future_index=4'),'exact future index must be reported')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'overrun must restore current Move')
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'))
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE' and f.commands[1].draft.x==100)
 healthy(f)
end)
T('SC6 V3_IDENTITY_MISMATCH_NO_FALSE_ADOPT ignores semantic current_target without exact identity',function()
 local f=base()
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f.bad_sequence=true;f.unit.target=f.enemy;f:tick(300,100,0)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'))
 assert(f:has('BLOCKED_EXECUTION_IDENTITY'))
 assert(f.issued==0)
 healthy(f)
end)
T('SC6 SC5_REASSERT_REQUIRES_CURRENT_EXECUTION does not physical-reassert over future Attack',function()
 local f=F({cold_idle=true,debug_source=true,native_order_evidence_v3=order_v3})
 local e2=f:add_enemy_reinforcement('2002',-8,0)
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 for t=100,6000,100 do f:tick(t,-8,0);if f.native_pending then f:deliver() end end
 assert(f.issued>=1,'Exit Move should be issued')
 local before_reassert=f:count('EXIT_BLOCK_REASSERT')
 -- Native now promotes a captured future Attack while Exit is physically stalled.
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2002');f.unit.target=e2;f.unit.melee=true
 for t=6100,7600,100 do f:tick(t,-8,0) end
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'identity layer owns this recovery')
 assert(f:count('EXIT_BLOCK_REASSERT')==before_reassert,'SC5 physical layer must not race the identity rollback')
 healthy(f)
end)
T('SC6 NONCANONICAL_ACTIVE_ORDER blocks SC5 physical recovery',function()
 local function stale_entity(ff,u,now)
  return {schema=3,complete=true,probe_reason='ENTITY_STALE',model_ms=0,slot_count=1,live_count=1,dead_count=0,
   movement_idle_count=1,movement_pathing_count=0,movement_halted_count=0,median_x=ff.unit.x,median_z=ff.unit.z,
   motion_complete=false,motion_matched_count=0,entities={{entity='e1',x=ff.unit.x,z=ff.unit.z,movement_state=0,motion_complete=false}}}
 end
 local f=F({width=40,debug_source=true,native_evidence_v3=true,native_order_evidence_v3=order_v3,native_entity_evidence_v3=stale_entity})
 local e2=f:add_enemy_reinforcement('2002',-8,0)
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 function f.unit:unit_distance() return 0 end
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 f:tick(100)
 for t=200,6000,100 do f:tick(t) end
 assert(f.issued==1,'Exit Move must be issued before identity mismatch test')
 f:deliver();f:tick(6100,-8,0)
 local before=f.issued
 -- Fabricate an exact native Attack identity that is not present in the Lua canonical plan.
 f.evidence_record={unit_uid='1001',unit_lifetime='1',serial='999001',engine_seq='999002',order_type='ATTACK',target_uid='2002'}
 f.unit.target=e2;f.unit.melee=true
 for t=6200,8500,100 do f:tick(t,-8,0) end
 assert(f:has('ACTIVE_EXECUTION_NOT_CANONICAL'))
 assert(f.issued==before,'SC5 must not overwrite an exact noncanonical active order')
 healthy(f)
end)
T('SC6 V2_COMPAT_FALLBACK works only when V3 is unavailable',function()
 local f=F({cold_idle=true,debug_source=true,disable_v3_evidence=true,native_evidence_v2=true,native_order_evidence=function(ff,u)
  local r=ff.evidence_record;if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
  return {schema=2,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
   accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
 end})
 f:start();f.enemy.x=300;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,100,0)
 f.evidence_record=f:emit('ATTACK',true,nil,nil,'2001');f.unit.target=f.enemy;f:tick(300,100,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED') and f:has('provider=V2'))
 healthy(f)
end)
print('ACTUAL_INTERPRETER='.._VERSION..'; SC6 execution identity regressions; V3-authoritative plus explicit V2 fallback')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
