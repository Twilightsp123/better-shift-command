-- TPOL T2-B Move->Attack terminal-handoff regression gate.
-- The terminal corridor is now an offline candidate: these cases lock both the
-- smooth handoff and the fail-closed boundaries until WH3 runtime smoke closes T2-B.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)
 local ok,e=pcall(fn)
 if ok then pass=pass+1;print('PASS '..n)
 else fail=fail+1;print('FAIL '..n..' :: '..tostring(e)) end
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
local function base(native)
 local cfg={cold_idle=true,debug_source=true,width=40}
 if native then cfg.native_order_evidence_v3=order_v3 end
 local f=F(cfg)
 f:start();f.enemy.x=200;f.enemy.z=0
 f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 return f
end
local function walk_slow(f,to_x)
 -- 10 m/s synthetic approach so attack_geometry uses a non-pathological speed.
 f:tick(100,0,0)
 local t=1100
 local x=10
 while x<=to_x do f:tick(t,x,0);t=t+1000;x=x+10 end
 if (to_x%10)~=0 then f:tick(t,to_x,0);t=t+1000 end
 return t
end
local function native_at(f,record,t,x)
 f.evidence_record=record;f.unit.target=f.enemy
 f:tick(t,x,0)
end

T('T2B-00 completed Move plus newly appended exact Attack adopts without duplicate issue',function()
 local f=base(true)
 f:emit('MOVE',false,100,0)
 f:tick(100,0,0);f:tick(1100,50,0);f:tick(2100,100,0)
 local attack=f:emit('ATTACK',true,nil,nil,'2001')
 f.evidence_record=attack;f.unit.target=f.enemy;f:tick(2200,100,0)
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'completed Move must adopt exact newly appended Attack')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'),'completed Move must not rollback exact Attack')
 assert(f.issued==0,'native adoption must not duplicate the Attack')
 healthy(f)
end)

T('T2B-01 Smooth proactive terminal corridor issues Attack before full waypoint stop',function()
 local f=base(false)
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 walk_slow(f,75) -- progress=.75, remaining=25m; straight attack threshold is bounded ~29m.
 assert(f.issued==1,'terminal corridor should proactively issue the immediate Attack before semantic_done')
 assert(f.commands[1].draft.kind=='ATTACK','terminal handoff must issue Attack, not another Move')
 assert(not f:has('ATTACK_REQUIRES_ROUTE_COMPLETE'),'Smooth may not reduce T2-B to strict semantic_done')
 healthy(f)
end)

T('T2B-02 Native exact immediate Attack inside terminal corridor soft-adopts instead of rollback',function()
 local f=base(true)
 f:emit('MOVE',false,100,0)
 local attack=f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk_slow(f,70)
 native_at(f,attack,t,75) -- enter the terminal corridor on the same poll as Native evidence.
 assert(f:has('NATIVE_SUCCESSOR_ADOPTED'),'exact i+1 Attack inside terminal corridor should be adopted')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'),'terminal-corridor Attack must not be rolled back to Move')
 assert(not f:has('NATIVE_ADVANCED_BEFORE_PERMISSION'),'bounded legal successor should not fault as premature')
 assert(f.issued==0,'soft-adopt must not duplicate the native Attack')
 healthy(f)
end)

T('T2B-03 far-early Native Attack remains rollback-protected',function()
 local f=base(true)
 f:emit('MOVE',false,100,0)
 local attack=f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk_slow(f,60) -- progress=.60 but remaining=40m, outside bounded straight threshold.
 native_at(f,attack,t,60)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'far-early Attack must not adopt')
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION'),'far-early Attack must remain explicitly blocked')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'far-early Attack must restore the unfinished Move')
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE','rollback must reassert the current Move')
 healthy(f)
end)

T('T2B-04 Native Attack at i+2 never skips an intermediate canonical Move',function()
 local f=base(true)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,150,0)
 local attack=f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,20,0) -- before Move->Move policy can advance the canonical cursor.
 native_at(f,attack,200,20)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'i+2 Attack must never adopt')
 assert(f:has('NATIVE_FUTURE_OVERRUN'),'i+2 must remain a hard future-overrun invariant')
 assert(f:has('future_index=3'),'rollback telemetry must retain the exact skipped index')
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE','overrun must reassert current Move')
 healthy(f)
end)

T('T2B-05 target/receipt mismatch cannot false-adopt terminal Attack',function()
 local f=base(true)
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 local t=walk_slow(f,70)
 f.evidence_record={unit_uid='1001',unit_lifetime='1',serial='999001',engine_seq='999002',
  order_type='ATTACK',target_uid='2002',dest_x=0,dest_z=0}
 f.unit.target=f.enemy;f:tick(t,75,0) -- mismatch is present before proactive handoff can run.
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'mismatched target/receipt may not borrow terminal permission')
 assert(f:has('ACTIVE_EXECUTION_NOT_CANONICAL'),'mismatch must remain identity-fail-closed')
 assert(f.issued==0,'noncanonical Attack must not trigger a replacement Attack')
 healthy(f)
end)

T('T2B-06 short Move leg cannot be swallowed before bounded progress',function()
 local f=F({cold_idle=true,debug_source=true,width=40,native_order_evidence_v3=order_v3})
 f:start();f.enemy.x=100;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,20,0)
 local attack=f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,4,0);f:tick(2100,8,0) -- 40% progress on a 20m leg.
 native_at(f,attack,2200,8)
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'short-leg early Attack must not swallow most of the waypoint')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'short-leg early Attack stays rollback-protected')
 healthy(f)
end)

T('T2B-07 existing route-complete path remains valid when Move is already complete',function()
 local f=base(false)
 f:emit('MOVE',false,100,0)
 f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,100,0)
 assert(f.issued==1 and f.commands[1].draft.kind=='ATTACK','semantic-complete Move must still issue Attack')
 assert(f:has('ATTACK_AFTER_ROUTE_COMPLETE'),'completed Move must retain the established route-complete credit path')
 healthy(f)
end)

T('T2B-08 high-angle Attack requires extra route progress before terminal handoff',function()
 local f=F({cold_idle=true,debug_source=true,width=40})
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(1100,50,0);f:tick(2100,75,0)
 assert(f.issued==0,'U-turn terminal handoff must require more progress than a straight approach')
 f:tick(3100,86,0)
 assert(f.issued==1 and f.commands[1].draft.kind=='ATTACK','high-angle handoff should open after the bounded turn-progress requirement')
 assert(f:has('reason=ATTACK_TERMINAL_HANDOFF'),'high-angle legal handoff must use explicit terminal credit')
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; TPOL T2-B Shift Move->Attack regression gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
