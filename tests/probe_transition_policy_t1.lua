-- Deterministic behavior probe for T1 old/new equivalence.
local F=assert(loadfile(assert(arg[2])))().new
local function out(name,f)
 local issued={}
 for i,c in ipairs(f.commands) do issued[#issued+1]=(c.draft.kind or '?')..':'..tostring(c.draft.x or '')..':'..tostring(c.draft.z or '') end
 local tags={}
 for _,s in ipairs(f.logs) do
  for _,k in ipairs({'NATIVE_FUTURE_OVERRUN','NATIVE_SUCCESSOR_ROLLBACK','NATIVE_SUCCESSOR_ADOPTED','STEERING_CORNER_COMMITTED','ATTACK_AFTER_ROUTE_COMPLETE','MOVE_AFTER_NODE_COMPLETE'}) do
   if s:find(k,1,true) then tags[#tags+1]=k end
  end
 end
 print('RESULT '..name..' issued='..f.issued..' commands='..table.concat(issued,',')..' tags='..table.concat(tags,','))
end
local function order_v3(f,u)
 local r=f.evidence_record
 if not r or r.unit_uid~=u then return nil,'NO_ORDER' end
 return {schema=3,epoch='1',unit_uid=u,unit_lifetime=r.unit_lifetime,complete=true,active=true,known=true,
  accepted_journal_serial=r.serial,active_engine_seq=r.engine_seq,kind=r.order_type,target_uid=r.target_uid,dest_x=r.dest_x,dest_z=r.dest_z}
end
-- SC1/SC2 Move->Move early steering.
do
 local f=F({cold_idle=true,debug_source=true,width=20});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,100)
 f:tick(100,0,0);f:tick(200,70,0);out('move_turn',f)
end
-- Strict pre-T2 Move->Attack: not at 75m, then after node completion.
do
 local f=F({cold_idle=true,debug_source=true,width=40});f:start();f.enemy.x=200;f.enemy.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001');f:tick(100,0,0);f:tick(200,75,0);out('attack_early',f);f:tick(300,100,0);out('attack_complete',f)
end
-- Legacy T1 SC6 immediate future MOVE remains rollback (T2-A not active).
do
 local f=F({cold_idle=true,debug_source=true,width=20,native_order_evidence_v3=order_v3});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);local m2=f:emit('MOVE',true,200,0);f:tick(100,20,0);f.evidence_record=m2;f:tick(200,30,0);out('native_move_legacy',f)
end
-- Immediate Attack after current Move completion is still adoptable.
do
 local f=F({cold_idle=true,debug_source=true,width=20,native_order_evidence_v3=order_v3});f:start();f.enemy.x=200;f.enemy.z=0;f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);local a=f:emit('ATTACK',true,nil,nil,'2001');f:tick(100,100,0);f.evidence_record=a;f.unit.target=f.enemy;f:tick(200,100,0);out('native_attack_complete',f)
end