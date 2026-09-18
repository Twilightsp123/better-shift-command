-- v1.0.7 regressions: queued restart certificates and global post-attack disengagement.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function ticks(f,a,b,step,x,z)for t=a,b,step or 100 do f:tick(t,x,z)end end
local function attack_exit_chain(extra_enemy)
 local f=F({width=40,debug_source=true})
 local e2=extra_enemy and f:add_enemy_reinforcement('2002',-28,0) or nil
 f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-28,0);f:emit('ATTACK',true,nil,nil,'2001');f:tick(100)
 for t=200,6000,100 do f:tick(t) end
 assert(f.issued==1 and f.commands[1].draft.kind=='MOVE','first post-attack command must be exit Move')
 f:deliver();f:tick(6100,-8,0)
 return f,e2
end

T('accepted HALT creates a trusted queue-reset predecessor for an immediate Shift Attack',function()
 local f=F({debug_source=true});f:start()
 f:emit('MOVE',false,100,0);f:tick(100,0,0)
 f:emit('HALT',nil);f:tick(200,0,0)
 f:emit('ATTACK',true,nil,nil,'2001');f:tick(300,0,0)
 assert(f:has('QUEUE_RESET_CERT_READY') and f:has('QUEUE_RESET_SEED'))
 assert(f:has('PLAN_ACTIVATED') and not f:has('QUEUED_WITHOUT_REPLACE_IGNORED'))
 healthy(f)
end)

T('HALT reset certificate is single-use and the following Shift tail appends normally',function()
 local f=F({debug_source=true});f:start()
 f:emit('HALT',nil);f:tick(100,0,0)
 f:emit('MOVE',true,100,0);f:emit('MOVE',true,200,0);f:tick(200,0,0)
 assert(f:count('QUEUE_RESET_SEED')==1 and f:count('ACTION_CAPTURE')==2 and f:has('PLAN_ACTIVATED'))
 assert(not f:has('QUEUED_IGNORED_BLOCKED'));healthy(f)
end)

T('queued-only start without cold idle, HALT reset, or stable idle still fails closed',function()
 local f=F({debug_source=true});f:start();f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',true,nil,nil,'2001');f:tick(100,0,0)
 assert(f:has('QUEUED_WITHOUT_REPLACE_IGNORED') and f:has('NO_TRUSTED_QUEUE_EMPTY_PREDECESSOR'))
 healthy(f)
end)

T('stable clean idle can rebuild a fresh queued-start certificate after cancellation',function()
 local f=F({cold_idle=true,debug_source=true});f:start()
 f:emit('MOVE',false,100,0);f:tick(100,0,0)
 f:emit('HALT',nil);f:tick(200,0,0)
 -- Consume the HALT reset with a replacement lifecycle, then cancel again with an unsupported control order.
 f:emit('MOVE',false,10,0);f:tick(300,0,0)
 f:emit('WITHDRAW',nil);f:tick(400,0,0)
 f.unit.idle=true;f.unit.moving=false;f.unit.melee=false;f.unit.target=nil
 for t=500,1300,100 do f:tick(t,0,0) end
 assert(f:has('QUEUE_IDLE_CERT_READY'))
 f:emit('ATTACK',true,nil,nil,'2001');f:tick(1400,0,0)
 assert(f:has('QUEUE_IDLE_SEED') and not f:has('QUEUED_WITHOUT_REPLACE_IGNORED'));healthy(f)
end)

T('Center A2 route completion is not vetoed by unrelated melee contact',function()
 local f,e2=attack_exit_chain(true)
 f.unit.x=-28;f.unit.z=0;f.unit.melee=true;f.unit.target=e2;e2.x=-28;e2.z=0
 for t=6200,8200,100 do f:tick(t,-28,0) end
 assert(f:has('EXIT_GLOBAL_CONTACTS') and f:has('contact_uids=2002'))
 local attacks=0;for _,c in ipairs(f.commands)do if c.draft.kind=='ATTACK' then attacks=attacks+1 end end
 assert(attacks>=1,'route-complete P1 must be allowed to issue A2; fresh-mode FEG decides whether A2 earns hold time')
 assert(not f:has('code=BLOCKED_EVIDENCE'),'unrelated contact may remain telemetry but cannot hard-fault the route')
 healthy(f)
end)

T('source target death does not complete exit while another enemy still holds the unit in melee',function()
 local f,e2=attack_exit_chain(true)
 f.enemy.dead=true;f.unit.x=-28;f.unit.z=0;f.unit.melee=true;f.unit.target=e2;e2.x=-28;e2.z=0
 for t=6200,8200,100 do f:tick(t,-28,0) end
 assert(f:has('EXIT_SOURCE_TARGET_ENDED_WAIT_GLOBAL_CLEAR'))
 assert(not f:has('EXIT_BLOCK_COMMITTED'));for _,c in ipairs(f.commands)do assert(c.draft.kind~='ATTACK')end;healthy(f)
end)

T('global melee clear commits exit after real exit motion and then permits the next Attack',function()
 local f,e2=attack_exit_chain(true)
 f.unit.x=-28;f.unit.z=0;f.unit.melee=true;f.unit.target=e2;e2.x=-28;e2.z=0
 for t=6200,7000,100 do f:tick(t,-28,0) end
 assert(not f:has('EXIT_BLOCK_COMMITTED'))
 e2.x=100;e2.z=100;f.unit.melee=false;f.unit.target=nil
 for t=7100,8300,100 do f:tick(t,-28,0) end
 assert(f:has('reason=LEGACY_GLOBAL_MELEE_CLEARED_AFTER_EXIT_MOTION'))
 assert(f.issued==2 and f.commands[2].draft.kind=='ATTACK');healthy(f)
end)

T('sticky melee flag may clear only after all registered enemy contacts are absent for the longer fallback dwell',function()
 local f,e2=attack_exit_chain(true)
 f.unit.x=-28;f.unit.z=0;f.unit.melee=true;f.unit.target=nil;e2.x=100;e2.z=100
 for t=6200,7400,100 do f:tick(t,-28,0) end
 assert(not f:has('EXIT_BLOCK_COMMITTED'),'sticky fallback must not use the normal short confirm')
 for t=7500,8000,100 do f:tick(t,-28,0) end
 assert(f:has('reason=LEGACY_GLOBAL_CONTACT_CLEAR_STICKY_MELEE'))
 local attacks=0;for _,c in ipairs(f.commands)do if c.draft.kind=='ATTACK'then attacks=attacks+1 end end
 assert(attacks==1,'next Attack should start after sticky-melee global-clear fallback');healthy(f)
end)

print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
