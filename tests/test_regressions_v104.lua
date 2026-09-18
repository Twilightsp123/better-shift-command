-- v1.0.7 retained safety regressions not specific to command-block geometry.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function ticks(f,a,b,step)for t=a,b,step or 100 do f:tick(t)end end
local function attack(tail)
 local f=F({width=40,debug_source=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');if tail then f:emit('MOVE',true,-80,0)end;f:tick(100);return f
end
T('temporary hidden target preserves Attack and never queries hidden position',function()
 local f=attack(true);ticks(f,200,1000);f.enemy.hidden=true;f.enemy.position_error=true;ticks(f,1100,3000)
 assert(f.issued==0 and f:has('TARGET_TEMPORARILY_UNAVAILABLE') and not f:has('ATTACK_TARGET_ABORT_CONTINUE'));healthy(f)
end)
T('routing is still an Attack, not death or zero-hold completion',function()
 local f=attack(true);f.enemy.routing=true;ticks(f,200,2500);assert(f.issued==0 and not f:has('ATTACK_TARGET_ABORT_CONTINUE'))
 f.enemy.routing=false;ticks(f,2600,6000);assert(f.issued==1);healthy(f)
end)
T('one-tick death signal cannot skip Attack',function()
 local f=attack(true);f.enemy.dead=true;f:tick(200);f.enemy.dead=false;f:tick(300);ticks(f,400,1200)
 assert(f.issued==0 and not f:has('ATTACK_TARGET_ABORT_CONTINUE'));healthy(f)
end)
T('confirmed death releases a known tail only after confirmation',function()
 local f=attack(true);f.enemy.dead=true;for t=200,800,100 do f:tick(t);assert(f.issued==0)end
 f:tick(900);assert(f.issued==1 and f.commands[1].draft.kind=='MOVE');assert(f:has('reason=TARGET_DEAD'));healthy(f)
end)
T('future unavailable Attack preserves earlier Move prefix and suffix',function()
 local f=F({debug_source=true});f:start();f.enemy.hidden=true;f.enemy.position_error=true
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('ATTACK',true,nil,nil,'2001');f:emit('MOVE',true,300,0)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1 and not f:has('GEN_CANCEL'));f:deliver();f:tick(300,120,0);healthy(f)
end)
T('out-of-order ACKs remain recipient-local',function()
 local f=F({two_units=true,debug_source=true});f:start();f.enemy.x=300;f.enemy.z=0
 for _,u in ipairs({'1001','1002'})do f:emit('MOVE',false,100,0,nil,u);f:emit('MOVE',true,200,0,nil,u)end
 f:tick(100,0,0);f.unit2.x=80;f:tick(200,80,0);assert(f.issued==2)
 f:deliver('1002');f:deliver('1001');f:tick(300,90,0);assert(f.pending_count==0 and f:count('OWN_MOVE_ACK')==2);healthy(f)
end)
T('first pure Shift during startup delay uses pre-input cold-idle certificate',function()
 local f=F({cold_idle=true,debug_source=true});f.phase='Deployed';f.callbacks.Deployed();assert(f.recording and #f.delay==1)
 f:emit('MOVE',true,100,0);local d=f.delay;f.delay={};for _,cb in ipairs(d)do cb()end;f:tick(100,0,0)
 assert(f:has('COLD_IDLE_SEED') and f:has('PLAN_ACTIVATED'));healthy(f)
end)
T('startup never fabricates cold-idle predecessor for a moving unit',function()
 local f=F({cold_idle=true,debug_source=true});f.unit.idle=false;f.unit.moving=true;f.phase='Deployed';f.callbacks.Deployed()
 f:emit('MOVE',true,100,0);local d=f.delay;f.delay={};for _,cb in ipairs(d)do cb()end;f:tick(100,0,0)
 assert(f:has('QUEUED_WITHOUT_REPLACE_IGNORED') and not f:has('COLD_IDLE_SEED'));healthy(f)
end)
T('late accepted old-generation ACK updates ledger but never revives old plan',function()
 local f=F({debug_source=true});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1)
 f:emit('MOVE',false,-100,0);f:tick(300,80,0);f:deliver();f:tick(400,80,0)
 assert(f:has('LATE_OWN_ACK_IGNORED') and not f:has('OWN_MOVE_ACK uid=1001 gen=1'));healthy(f)
end)
T('more than 256 historical nodes compact without cancelling live generation',function()
 local f=F({debug_source=true});f:start();f:emit('MOVE',false,10,0);for i=2,256 do f:emit('MOVE',true,i*10,0)end
 f:tick(100,0,0)
 -- Use collinear observations and ACK each handoff to create completed history.
 local t=200
 for i=1,3 do f:tick(t,i*10-1,0);if f.native_pending then f:deliver()end;t=t+100;f:tick(t,i*10,0);t=t+100 end
 f:emit('MOVE',true,3000,0);f:tick(t,30,0)
 assert(f:has('ACTION_HISTORY_COMPACTED') and not f:has('GEN_CANCEL'));healthy(f)
end)
T('paused callbacks do not credit Attack hold time',function()
 local f=attack(true);f:tick(200);for i=1,50 do f:tick(200)end;assert(f.issued==0);ticks(f,300,2500);assert(f.issued==0);healthy(f)
end)
T('observation gaps do not backfill Attack credit',function()
 local f=attack(true);ticks(f,200,1600);f:tick(5000);assert(f.issued==0);ticks(f,5100,7000);assert(f.issued==0);healthy(f)
end)
print('ACTUAL_INTERPRETER='.._VERSION..'; explicit engine doubles, not WH3')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
