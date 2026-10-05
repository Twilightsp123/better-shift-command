-- v1.0.7 invariant contracts: journal, ownership, cancellation, revisions and bounded concurrency.
local actual=_VERSION
local F=assert(loadfile(assert(arg[2])))().new
local p,fails=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then p=p+1;print('PASS '..n)else fails=fails+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(x)assert(not x:has('CONTROLLER_FAIL'))end
local function route(x,who)
 x.enemy.x=300;x.enemy.z=0
 x:emit('MOVE',false,100,0,nil,who);x:emit('MOVE',true,200,0,nil,who);x:emit('ATTACK',true,nil,nil,'2001',who)
end
local function issue_first(opts)
 local x=F(opts);x:start();route(x);x:tick(100,0,0);x:tick(200,80,0);assert(x.issued==1);return x
end
T('bootstrap and startup are visible',function()local x=F();assert(x:has('BATTLE_MANAGER_OK'));x:start();assert(x:has('INPUT_READY'));healthy(x)end)
T('missing battle manager fails closed',function()local x=F({no_bm=true});assert(x:has('BATTLE_MANAGER_UNAVAILABLE') and not x:has('INPUT_READY'))end)
T('wrong Bridge version fails closed',function()local x=F({wrong_version=true});assert(x:has('WRONG_BRIDGE_VERSION'))end)
T('observer and begin failures do not start',function()local a=F({observer_fail=true});a:start();assert(a:has('OBSERVER_TEST_FAIL'));local b=F({begin_nil=true});b:start();assert(b:has('BEGIN_BEGIN_DENIED'))end)
T('journal reads 64 and paginates before executing',function()local x=F();x:start();for i=1,130 do x:emit('MOVE',false,i,0)end;x:tick(100);assert(x.read_sizes[1]==64 and x.acks==3 and x.ack=='130')end)
T('journal gap and overrun fail before dispatch',function()for _,k in ipairs({'gap','overrun'})do local o={};o[k]=true;local x=F(o);x:start();route(x);x:tick(100,80,0);assert(x.issued==0 and x:has('CONTROLLER_FAIL'))end end)
T('bad cursor is never acknowledged',function()local x=F();x:start();x:emit('MOVE',false,100,0);x.cfg.bad_cursor=true;x:tick(100);assert(x.acks==0 and x:has('JOURNAL_CURSOR_CONTRACT'))end)
T('ack failure prevents issue',function()local x=F();x:start();route(x);x.cfg.ack_fail=true;x:tick(100);assert(x.issued==0 and x:has('ACK_ACK_DENIED'))end)
T('revision race never reauthorizes stale plan',function()local x=F({revision_race=true});x:start();route(x);x:tick(100,0,0);x:tick(200,80,0);assert(x.issued==0 and x:has('REVISION_CHANGED_BEFORE_DISPATCH'))end)
T('native stale gate skips callback',function()local x=F({gate_race=true});x:start();route(x);x:tick(100,0,0);x:tick(200,80,0);assert(x.issued==0 and x.releases==0 and x:has('REJECTED_STALE'))end)
T('normal RMB cancels old generation and late ACK cannot revive it',function()local x=issue_first();x:emit('MOVE',false,-100,0);x:tick(300);x:deliver();x:tick(400);assert(x:has('LATE_OWN_ACK_IGNORED'));for t=500,6000,100 do x:tick(t)end;assert(x.issued==1);healthy(x)end)
T('HALT cancels controlled generation',function()local x=issue_first();x:deliver();x:tick(300,120,0);x:emit('HALT',nil);x:tick(400);assert(x:has('GEN_CANCEL') and x:has('reason=EXTERNAL_HALT'));healthy(x)end)
T('ACK timeout disarms controller',function()local x=issue_first();x:tick(5300);assert(x:has('OWN_ACK_TIMEOUT') and not x.armed)end)
T('wrong own issue and revision fail closed',function()local a=issue_first({wrong_own_issue=true});a:deliver();a:tick(300);assert(a:has('UNEXPECTED_OWN_ACK'));local b=issue_first({wrong_own_revision=true});b:deliver();b:tick(300);assert(b:has('OWN_ACK_CONTRACT'))end)
T('wrong own Attack target ACK fails closed',function()
 local x=F({wrong_own_target=true});x:start();x.enemy.x=100;x.enemy.z=0
 x:emit('MOVE',false,20,0);x:emit('ATTACK',true,nil,nil,'2001');x:tick(100,0,0);x:tick(200,18.5,0)
 assert(x.issued==1 and x.commands[1].draft.kind=='ATTACK');x:deliver();x:tick(300,18.5,0)
 assert(x:has('OWN_TARGET_MISMATCH') and x:has('CONTROLLER_FAIL'))
end)
T('command callback exception releases and fails visibly',function()local x=F({command_throw=true});x:start();route(x);x:tick(100,0,0);x:tick(200,80,0);assert(x:has('LUA_CALLBACK_FAILED') and x.releases==1)end)
T('missing vector helper fails before publish',function()local x=F({no_vector=true});x:start();route(x);x:tick(100,0,0);x:tick(200,80,0);assert(x.issued==0 and x:has('LUA_CALLBACK_FAILED'))end)
T('five recipients share widened bounded pipeline without four-unit batching',function()
 local x=F({two_units=true});local u3=x:add_late_local('1003',0,0);local u4=x:add_late_local('1004',0,0);local u5=x:add_late_local('1005',0,0);x:start()
 for _,u in ipairs({'1001','1002','1003','1004','1005'})do route(x,u)end;x:tick(100,0,0);x.unit2.x=80;u3.x=80;u4.x=80;u5.x=80;x:tick(200,80,0)
 assert(x.issued==5 and x.pending_count==5);x:tick(300,90,0);assert(x.issued==5);healthy(x)
end)
T('queued append during pending affects only that recipient and redecides',function()
 local x=issue_first();x:emit('MOVE',true,260,0);x:tick(300,90,0);x:deliver();x:tick(400,95,0)
 assert(x:has('OWN_STALE_AFTER_APPEND') and x.issued==2);healthy(x)
end)
T('paused callbacks drain ACK but do not create model-time handoff',function()local x=issue_first();x:deliver();for i=1,20 do x:tick(200,80,0)end;assert(x.pending_count==0 and x.issued==1);healthy(x)end)

T('poll reentry fails closed before a second issue',function()
 local x=F({poll_reentry=true});x:start();route(x);x:tick(100,0,0);x:tick(200,80,0)
 assert(x:has('POLL_REENTRY') and x.issued==0);assert(x:has('CONTROLLER_FAIL'))
end)
T('cancelling one of four pending recipients does not cancel siblings',function()
 local x=F({two_units=true});local u3=x:add_late_local('1003',0,0);local u4=x:add_late_local('1004',0,0);x:start()
 for _,u in ipairs({'1001','1002','1003','1004'})do route(x,u)end
 x:tick(100,0,0);x.unit2.x=80;u3.x=80;u4.x=80;x:tick(200,80,0);assert(x.issued==4 and x.pending_count==4)
 x:emit('MOVE',false,-200,0,nil,'1002');x:tick(300,80,0)
 for _,u in ipairs({'1002','1001','1003','1004'})do x:deliver(u)end;x:tick(400,80,0)
 assert(x:has('LATE_OWN_ACK_IGNORED uid=1002'))
 assert(x:has('OWN_MOVE_ACK uid=1001') and x:has('OWN_MOVE_ACK uid=1003') and x:has('OWN_MOVE_ACK uid=1004'))
 assert(not x:has('GEN_CANCEL uid=1001') and not x:has('GEN_CANCEL uid=1003') and not x:has('GEN_CANCEL uid=1004'));healthy(x)
end)
T('recoverable capture yields ambiguous generation before a fresh replace can recover',function()
 local x=issue_first();x:deliver();x:tick(300,100,0)
 x.revision['1001']=tostring(tonumber(x.revision['1001'])+1)
 x.cfg.capture_errors='1';x.cfg.last_recoverable_uid='1001';x.cfg.last_recoverable_error='EXTERNAL_OUTCOME_PARTIAL'
 x:emit('MOVE',false,180,0);x:tick(400,110,0)
 assert(x:has('BRIDGE_RECOVERABLE_CAPTURE') and not x:has('EXTERNAL_REVISION_DISCONTINUITY'));healthy(x)
 x.cfg.capture_errors='1';x:emit('MOVE',false,200,0);x:emit('MOVE',true,260,0);x:tick(500,120,0);x:tick(600,180,0)
 assert(not x:has('CONTROLLER_FAIL'));healthy(x)
end)
T('dynamic reinforcement is registered before first fresh replacement plan',function()
 local x=F();x:start();local u=x:add_reinforcement('1005',0,0);route(x,'1005');x:tick(100);assert(x:has('REGISTER_LOCAL_DYNAMIC uid=1005'));u.x=80;x:tick(200);assert(x.issued==1 and x.commands[1].draft.uid=='1005');healthy(x)
end)
print('ACTUAL_INTERPRETER='..actual..'; explicit engine doubles, not WH3')
print('TOTAL '..p..' PASS '..fails..' FAIL');os.exit(fails==0 and 0 or 1)
