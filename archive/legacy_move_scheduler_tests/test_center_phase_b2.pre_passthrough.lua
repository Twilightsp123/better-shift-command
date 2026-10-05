local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function deliver_all(f) while f.native_pending do f:deliver() end end
local function tick(f,t,x,z) f:tick(t,x or f.unit.x,z or 0);deliver_all(f) end
local function setup(p1,p2)
 local f=F({cold_idle=true,width=40,debug_source=true})
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0
 f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,p1,0);f:emit('ATTACK',true,nil,nil,'2001');f:emit('MOVE',true,p2,0)
 for t=100,6000,100 do tick(f,t,-8) end
 assert(f.commands[1] and f.commands[1].draft.kind=='MOVE','A1 should release P1')
 return f
end
T('B2 entity evidence can never hard-fault Center exit',function()
 local f=F({cold_idle=true,width=40,debug_source=true})
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0)
 for t=100,6000,100 do tick(f,t,-8) end
 assert(f.commands[1] and f.commands[1].draft.kind=='MOVE')
 f.unit.target=nil;f.unit.melee=true;f.unit.moving=false
 -- Hold the Exit command without route progress for longer than evidence_wait_ms so
 -- the legacy evidence-fault call site is definitely exercised.
 for t=6100,12500,100 do tick(f,t,-8) end
 assert(f:has('CENTER_ENTITY_EVIDENCE_TELEMETRY'),'legacy evidence fault call must be visible as telemetry')
 assert(not f:has('code=BLOCKED_EVIDENCE'),'Entity/Frozen evidence must remain telemetry-only even before A2 append')
end)
T('B2 accepted A2 that goes idle reasserts same action/target and preserves credit',function()
 local f=setup(-100,-160)
 f.unit.melee=true;f.unit.target=nil
 local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK','P1 completion should issue A2')
 -- Create a fresh A2 approach and about one second of legitimate credit.
 for t=9600,12500,100 do
   local p=(t-9600)/2900;local ax=-100+math.min(80,80*p)
   f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,ax)
 end
 for t=12600,14000,100 do f.unit.idle=false;f.unit.moving=false;f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,-20) end
 local before=#f.commands
 assert(not f.commands[before+1] or f.commands[before+1].draft.kind~='MOVE','hold should not already have released P2')
 -- CA loses the accepted attack execution: no target, no motion, no melee.
 for t=14100,17600,100 do f.unit.idle=true;f.unit.moving=false;f.unit.melee=false;f.unit.target=nil;tick(f,t,-20) end
 local reassert=nil
 for i=before+1,#f.commands do if f.commands[i].draft.kind=='ATTACK' then reassert=f.commands[i];break end end
 assert(reassert,'stalled accepted Attack must get a bounded same-target reassert')
 assert(reassert.draft.target=='2001','reassert must preserve intended target')
 assert(f:has('ATTACK_REASSERT_ISSUED') and f:has('ATTACK_REASSERT_ACK'),'reassert issue and ACK must be explicit')
 local preserved=nil
 for _,line in ipairs(f.logs) do if line:find('ATTACK_REASSERT_ISSUED',1,true) then preserved=tonumber(line:match('preserved_eligible_ms=(%d+)')) or preserved end end
 assert(preserved and preserved>0,'legitimate pre-stall A2 credit must survive reassert')
 assert(not f:has('code=BLOCKED_EXECUTION reason=ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE'),'first recovery attempt must happen before terminal execution fault')
 -- After reassert ACK, stale state cannot credit; a new approach/contact is required.
 for t=17700,19500,100 do f.unit.idle=false;f.unit.moving=true;f.unit.melee=false;f.unit.target=nil;tick(f,t,-60+(t-17700)*0.02) end
 for t=19600,24000,100 do f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,-20) end
 assert(f:has('CENTER_A2_APPROACH_SEEN') or f:has('CENTER_A2_FRESH_SEEN'))
 assert(f:has('ATTACK_HOLD_DONE'),'preserved legitimate credit plus post-reassert fresh engagement should finish the same action')
end)
T('B2 attack recovery is bounded to two same-action reasserts',function()
 local f=setup(-100,-160)
 f.unit.melee=true;f.unit.target=nil
 local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK')
 -- Never let the accepted A2 execute. Each recovery ACK is delivered, then it stalls again.
 for t=9600,32000,100 do f.unit.idle=true;f.unit.moving=false;f.unit.melee=false;f.unit.target=nil;tick(f,t,-100) end
 assert(f:count('ATTACK_REASSERT_ISSUED')==2,'recovery budget must submit exactly two reasserts')
 assert(f:count('ATTACK_REASSERT_ACK')==2,'both bounded reasserts should ACK in fixture')
 assert(f:has('code=BLOCKED_EXECUTION reason=ATTACK_ACCEPTED_BUT_NO_EXECUTION_EVIDENCE'),'after budget exhaustion the fault must be explicit')
 local attack_cmds=0
 for _,c in ipairs(f.commands) do if c.draft.kind=='ATTACK' then attack_cmds=attack_cmds+1 end end
 assert(attack_cmds==3,'original A2 plus exactly two recovery attacks expected')
end)
T('B2 near debt is not killed by an arbitrary stall timer',function()
 local f=F({debug_source=true});f:start();f.enemy.x=300;f.enemy.z=0
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);f:deliver()
 f:tick(300,120,50);f:tick(400,200,0)
 assert(f:has('ROUTE_OBLIGATION_TRANSFERRED'))
 -- Bring the old debt close to its tolerance, then let formation drift/settle for >8s.
 for t=500,1600,100 do f:tick(t,106,0) end
 for t=1700,11000,100 do f:tick(t,105.8,0) end
 assert(not f:has('ROUTE_UNRECOVERABLE'),'near-tolerance debt must not be declared unreachable solely by time')
 f:tick(11100,100,0);assert(f:has('ROUTE_OBLIGATION_SATISFIED'))
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
