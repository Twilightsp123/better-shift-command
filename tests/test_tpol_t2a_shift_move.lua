-- TPOL T2-A exact immediate Move native-adoption regression gate.
-- First implementation stage is adopt-only: Lua does not gain any new proactive
-- Move->Move dispatch permission here; it only stops fighting a legal Native i+1.
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
local function base(width)
 local f=F({cold_idle=true,debug_source=true,width=width or 20,native_order_evidence_v3=order_v3})
 f:start();f.unit.x=0;f.unit.z=0;f.unit.idle=false;f.unit.moving=true
 return f
end
local function native_at(f,record,t,x,z)
 f.evidence_record=record
 f:tick(t,x,z or 0)
end

T('T2A-00 exact i+1 straight Move inside steering corridor adopts without rollback',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 native_at(f,m2,200,70,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'legal exact i+1 Move should be adopted')
 assert(f:has('MOVE_STEERING_HANDOFF'),'adoption must grant explicit steering completion credit')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'),'legal i+1 Move must not be pulled back')
 assert(f.issued==0,'native adoption must not duplicate Move')
 healthy(f)
end)

T('T2A-00B exact i+1 straight Move before existing predictive window still rolls back',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 native_at(f,m2,200,30,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'adopt-only may not widen the existing straight Move dispatch window')
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION'))
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 healthy(f)
end)

T('T2A-01 exact i+1 90-degree Move too early remains rollback-protected',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,100,100)
 f:tick(100,0,0)
 native_at(f,m2,200,20,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'early turn may not be adopted')
 assert(f:has('NATIVE_ADVANCED_BEFORE_PERMISSION'),'early exact successor must be explicitly blocked')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'early turn must restore current Move')
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE' and f.commands[1].draft.x==100)
 healthy(f)
end)

T('T2A-02 exact i+1 90-degree Move near bounded turn corridor adopts',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,100,100)
 f:tick(100,0,0)
 native_at(f,m2,200,70,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'near-corner exact i+1 Move should adopt')
 assert(f:has('MOVE_STEERING_HANDOFF'),'corner adopt needs explicit completion credit')
 assert(not f:has('NATIVE_SUCCESSOR_ROLLBACK'))
 assert(f.issued==0)
 healthy(f)
end)

T('T2A-03 i+2 Move remains hard future overrun',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,200,0)
 local m3=f:emit('MOVE',true,300,0)
 f:tick(100,0,0)
 native_at(f,m3,200,70,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'i+2 may never soft-adopt')
 assert(f:has('NATIVE_FUTURE_OVERRUN'),'i+2 must remain a hard invariant')
 assert(f:has('future_index=3'))
 assert(f.issued==1 and f.commands[1].draft.x==100)
 healthy(f)
end)

T('T2A-04 destination/receipt mismatch cannot false-adopt a Move',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,200,0)
 f:tick(100,0,0)
 f.evidence_record={unit_uid='1001',unit_lifetime='1',serial='999001',engine_seq='999002',
  order_type='MOVE',dest_x=200,dest_y=0,dest_z=0}
 f:tick(200,70,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'))
 assert(f:has('ACTIVE_EXECUTION_NOT_CANONICAL'),'identity mismatch must fail closed')
 assert(f.issued==0,'noncanonical native Move is not ours to replace')
 healthy(f)
end)

T('T2A-05 short current leg cannot be swallowed at low progress',function()
 local f=base(40)
 f:emit('MOVE',false,20,0)
 local m2=f:emit('MOVE',true,40,0)
 f:tick(100,0,0)
 native_at(f,m2,200,4,0) -- 20% of a 20m leg.
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'short leg needs substantial progress')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'short-leg early native advance must rollback')
 healthy(f)
end)

T('T2A-06 short current leg near completion may adopt exact i+1',function()
 local f=base(40)
 f:emit('MOVE',false,20,0)
 local m2=f:emit('MOVE',true,40,0)
 f:tick(100,0,0)
 native_at(f,m2,200,18,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'short leg should adopt only near its bounded completion envelope')
 assert(f:has('MOVE_STEERING_HANDOFF'))
 assert(f.issued==0)
 healthy(f)
end)

T('T2A-07 unresolved prior route debt blocks native Move adoption',function()
 local f=base(4)
 f:emit('MOVE',false,100,0)
 f:emit('MOVE',true,120,0)
 local m3=f:emit('MOVE',true,140,0)
 -- First let controller hand off P1->P2 through PATH_SAFE and create real debt.
 f:tick(100,0,0);f:tick(200,80,0)
 assert(f.issued==1,'fixture must create first predictive Move handoff')
 f:deliver();f:tick(300,80,0)
 assert(f:has('ROUTE_OBLIGATION_TRANSFERRED'),'fixture must contain unresolved earlier waypoint debt')
 -- Native now jumps to exact immediate P3 while P1 debt is still unresolved.
 native_at(f,m3,400,92,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'T2-A adopt may not carry old route debt across the boundary')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK'),'old route debt must keep the current Move authoritative')
 healthy(f)
end)

T('T2A-08 Exit-route Move does not borrow ordinary steering-adopt policy',function()
 local f=F({cold_idle=true,debug_source=true,native_order_evidence_v3=order_v3})
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0);local m2=f:emit('MOVE',true,-160,0)
 -- Advance controller into the Exit Move first.
 for t=100,6000,100 do f:tick(t,-8,0);if f.native_pending then f:deliver() end end
 local before=f.issued
 native_at(f,m2,6100,-70,0)
 assert(not f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'Exit route must keep its separate transition policy')
 assert(f:has('NATIVE_SUCCESSOR_ROLLBACK') or f.issued==before,'ordinary T2-A must not adopt across Exit semantics')
 healthy(f)
end)

T('T2A-09 completed current Move still adopts exact immediate Move without duplicate issue',function()
 local f=base(20)
 f:emit('MOVE',false,100,0)
 local m2=f:emit('MOVE',true,200,0)
 -- Present the exact native successor on the same poll that reaches the node,
 -- before Lua can proactively issue a duplicate successor.
 native_at(f,m2,100,100,0)
 assert(f:has('NATIVE_MOVE_SUCCESSOR_ADOPTED'),'completed current Move should accept exact native successor')
 assert(f.issued==0,'adopt must not duplicate native Move')
 healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; TPOL T2-A exact immediate Move native-adoption gate')
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
