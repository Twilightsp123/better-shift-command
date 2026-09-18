-- v1.0.7 command-block semantics. Manual positions are observations, not WH3 physics proof.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function healthy(f)for _,s in ipairs(f.logs)do assert(not s:find('CONTROLLER_FAIL',1,true),s)end end
local function ticks(f,a,b,step,x,z)for t=a,b,step or 100 do f:tick(t,x,z)end end
local function hascmd(f,n,kind,x)
 local c=f.commands[n];assert(c and c.draft.kind==kind,'missing '..kind..' command #'..n)
 if x then assert(math.abs(c.draft.x-x)<0.01,'wrong destination')end
 return c
end
local function attack_root(tail)
 local f=F({width=40,debug_source=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');if tail then f:emit('MOVE',true,-28,0)end;f:tick(100)
 return f
end
local function run_attack_hold(f,from,to)
 for t=from or 200,to or 5200,100 do f:tick(t)end
end

T('single Move completion is latched with no successor and later Attack does not re-wait',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,70,0);f:tick(300,84,0)
 f.unit.idle=true;f.unit.moving=false;for t=400,1200,100 do f:tick(t,85,0)end
 assert(f.issued==0 and f:has('reason=NATIVE_IDLE_ROUTE_FINISH'))
 f:emit('ATTACK',true,nil,nil,'2001');f:tick(1300,85,0)
 assert(f.issued==1);hascmd(f,1,'ATTACK');assert(f:has('reason=ATTACK_AFTER_ROUTE_COMPLETE'));healthy(f)
end)

T('brief idle or distant idle does not latch Move completion',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,50,0)
 f.unit.idle=true;f.unit.moving=false;for t=300,800,100 do f:tick(t,50,0)end
 assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'))
 f.unit.idle=false;f.unit.moving=true;f:tick(900,50,0)
 f.unit.idle=true;f.unit.moving=false;for t=1000,1500,100 do f:tick(t,85,0)end
 assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'),'less than confirmation window must not latch')
 healthy(f)
end)


T('paused model time cannot accrue Move idle completion',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,70,0);f.unit.idle=true;f.unit.moving=false;f:tick(500,85,0)
 for i=1,30 do f:tick(500,85,0) end
 assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'));f:tick(600,85,0);assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'));healthy(f)
end)
T('Move idle completion cannot bridge a long observation gap',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,70,0);f.unit.idle=true;f.unit.moving=false
 for t=300,800,100 do f:tick(t,85,0) end;assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'))
 f:tick(2500,85,0);assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'),'gap must restart confirmation')
 for t=2600,3100,100 do f:tick(t,85,0) end;assert(not f:has('NATIVE_IDLE_ROUTE_FINISH'))
 f:tick(3200,85,0);assert(f:has('NATIVE_IDLE_ROUTE_FINISH'));healthy(f)
end)
T('normal replacement cancels an in-progress Move idle candidate',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,70,0);f.unit.idle=true;f.unit.moving=false
 for t=300,800,100 do f:tick(t,85,0) end
 f:emit('MOVE',false,-100,0);f:tick(900,85,0);for t=1000,2500,100 do f:tick(t,85,0) end
 assert(f:has('GEN_CANCEL') and not f:has('NATIVE_IDLE_ROUTE_FINISH'));healthy(f)
end)
T('Move to Move uses a bounded steering corridor for a right-angle waypoint while collinear prediction stays unchanged',function()
 local a=F({debug_source=true,width=40});a:start();a:emit('MOVE',false,100,0);a:emit('MOVE',true,100,100)
 a:tick(100,0,0);a:tick(200,60,0)
 assert(a.issued==1,'90 degree waypoint should hand off before arrival once the turn corridor is entered')
 hascmd(a,1,'MOVE',100);assert(a:has('route_mode=STEERING_CORNER'));assert(a:has('reason=PREDICTIVE'));healthy(a)
 local b=F({debug_source=true});b:start();b:emit('MOVE',false,100,0);b:emit('MOVE',true,200,0)
 b:tick(100,0,0);b:tick(200,80,0);assert(b.issued==1);hascmd(b,1,'MOVE',200)
 assert(b:has('route_mode=PATH_SAFE') and b:has('ACTION_HANDOFF_COMMITTED') and b:has('semantic_done=false'));healthy(b)
end)

T('strict PATH_SAFE still requires the safety margin before SC4 stall logic can matter',function()
 local f=F({debug_source=true,width=10});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,8)
 f:tick(100,0,0);f:tick(200,50,0);f:tick(1200,50,0)
 assert(f.issued==0,'cut error inside raw tolerance but outside the 0.75 safety margin must not become PATH_SAFE')
 assert(f:count('MOVE_ROUTE_PROTECT')>=2,'strict safety-margin rejection must remain externally visible after progress')
 healthy(f)
end)

T('20m Move to Move cannot hand off at only 20 percent progress',function()
 local f=F({width=40,debug_source=true});f:start();f:emit('MOVE',false,20,0);f:emit('MOVE',true,40,0)
 f:tick(100,0,0);f:tick(200,4,0);assert(f.issued==0,'20 percent progress must not erase a short current leg')
 f:tick(300,6,0);assert(f.issued<=1);healthy(f)
end)

T('predictive Move handoff transfers the old waypoint obligation until the actual path satisfies it',function()
 local f=F({debug_source=true});f:start()
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('MOVE',true,300,0)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);hascmd(f,1,'MOVE',200)
 f:deliver();f:tick(300,80,0)
 assert(f:has('ROUTE_OBLIGATION_TRANSFERRED'))
 assert(f.issued==1,'a second predictive handoff cannot outrun an unverified earlier waypoint')
 f:tick(400,105,0);assert(f:has('ROUTE_OBLIGATION_SATISFIED'))
 -- Once the observed segment actually crossed the transferred waypoint, normal prediction may resume later.
 f:tick(500,165,0);assert(f.issued==2);hascmd(f,2,'MOVE',300);healthy(f)
end)


T('SC3 soft debt allows a dense collinear Move handoff while keeping the old waypoint debt unresolved',function()
 local f=F({debug_source=true,width=4});f:start()
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,120,0);f:emit('MOVE',true,140,0)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);hascmd(f,1,'MOVE',120)
 f:deliver();f:tick(300,80,0);assert(f:has('ROUTE_OBLIGATION_TRANSFERRED'))
 f:tick(400,92,0)
 assert(not f:has('ROUTE_OBLIGATION_SATISFIED'),'P1 debt must still be unresolved when SC3 continues')
 assert(f.issued==2,'a successor chord that still preserves the old debt corridor should not hard-block Move->Move')
 hascmd(f,2,'MOVE',140)
 assert(f:has('ROUTE_DEBT_SOFT_CONTINUE'),'live diagnostics must prove conditional soft continuation')
 assert(f:has('debt_mode=SOFT_PRESERVED'),'handoff must carry soft-debt evidence')
 f:deliver();f:tick(500,92,0)
 assert(f:has('ROUTE_OBLIGATION_TRANSFERRED uid=1001 gen=1 block=M1 action=2'),'SC3 must keep the newly rounded PATH_SAFE node as background debt too')
 assert(not f:has('ROUTE_OBLIGATION_SATISFIED uid=1001 gen=1 block=M1 action=1'),'soft continuation must not silently erase P1 debt')
 f:tick(600,101,0)
 assert(f:has('ROUTE_OBLIGATION_SATISFIED uid=1001 gen=1 block=M1 action=1'),'old P1 debt must still settle from real trajectory evidence')
 healthy(f)
end)

T('SC3 soft debt becomes a hard block when the proposed successor chord cuts away from the owed waypoint',function()
 local f=F({debug_source=true,width=4});f:start()
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,120,0);f:emit('MOVE',true,120,40)
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);hascmd(f,1,'MOVE',120)
 f:deliver();f:tick(300,80,0);assert(f:has('ROUTE_OBLIGATION_TRANSFERRED'))
 f:tick(400,92,0);f:tick(1400,92,0)
 assert(f.issued==1,'deviating successor must remain blocked until the old debt is actually satisfied')
 assert(f:has('route_reason=PRIOR_ROUTE_OBLIGATION_DEVIATION'),'hard-block reason must identify debt-corridor deviation')
 assert(f:has('debt_mode=HARD'),'diagnostic must distinguish hard debt from SC3 soft continuation')
 healthy(f)
end)

T('an unresolved transferred waypoint still blocks the next action after the successor Move itself completes',function()
 local f=F({debug_source=true});f:start();f.enemy.x=300;f.enemy.z=0
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);f:deliver()
 -- Simulate a native/nav path that deviates around the transferred waypoint instead of crossing it.
 f:tick(300,120,50);f:tick(400,200,0)
 assert(f:has('ACTION_COMPLETE') and f:has('action=2'))
 assert(not f:has('ROUTE_OBLIGATION_SATISFIED'))
 assert(f.issued==1,'finishing the successor Move cannot erase an unresolved earlier waypoint obligation')
 assert(f:has('route_reason=PRIOR_ROUTE_OBLIGATION_PENDING') or f:has('MOVE_ROUTE_PROTECT') or f:has('ATTACK_ROUTE_PROTECT'))
 healthy(f)
end)

T('SC4 stalled turn corridor escapes inside a bounded margin instead of parking at the waypoint',function()
 local f=F({debug_source=true,width=10});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,20)
 f:tick(100,0,0);f:tick(200,70,0);assert(f.issued==0)
 f:tick(300,82,0);assert(f.issued==0,'18m remains outside the normal 15m short-leg-capped steering corridor')
 f:tick(400,82,0);assert(f.issued==0,'stall escape must not fire on the first frozen sample')
 f:tick(500,82,0);if f.issued==0 then f:tick(600,82,0) end
 assert(f.issued==1,'SC4 must escape once CA has parked just outside the turn corridor')
 hascmd(f,1,'MOVE',100,20)
 assert(f:has('TURN_CORRIDOR_STALL_ESCAPE'),'diagnostic must identify SC4 stall escape')
 assert(f:has('stall_escape=true'),'handoff log must prove the escape path, not ordinary steering')
 healthy(f)
end)

T('SC4 stall escape keeps the very-short-successor adjacent-leg cap',function()
 local f=F({debug_source=true,width=4});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,5)
 f:tick(100,0,0);f:tick(200,92,0);f:tick(300,92,0);f:tick(400,92,0);f:tick(1200,92,0)
 assert(f.issued==0,'a 5m successor must not be swallowed from 8m away even after a sustained stall')
 assert(f:has('TURN_CORRIDOR_REQUIRED'),'short-leg safety must remain the visible block reason')
 f:tick(1300,98,0);assert(f.issued==1,'handoff resumes only after entering the original short-leg corridor');healthy(f)
end)

T('SC1 steering corridor cannot swallow a very short successor leg',function()
 local f=F({debug_source=true,width=4});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,5)
 f:tick(100,0,0);f:tick(200,85,0);assert(f.issued==0,'5m successor leg must not be swallowed from 15m away')
 f:tick(1200,85,0);assert(f:has('TURN_CORRIDOR_REQUIRED'),'bounded-corner reason must be visible')
 f:tick(1300,98,0);assert(f.issued==1,'handoff is allowed only after entering the capped corridor');healthy(f)
end)

T('SC1 accepted steering-corner handoff completes the intermediate waypoint without creating return debt',function()
 local f=F({debug_source=true,width=40});f:start()
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,100);f:emit('MOVE',true,0,100)
 f:tick(100,0,0);f:tick(200,60,0);assert(f.issued==1);assert(f:has('route_mode=STEERING_CORNER'))
 f:deliver();f:tick(300,65,5)
 assert(f:has('STEERING_CORNER_COMMITTED'),'ACK must commit the rounded waypoint')
 assert(f:has('reason=STEERING_CORNER_HANDOFF'),'intermediate waypoint must be semantically complete')
 assert(not f:has('ROUTE_OBLIGATION_TRANSFERRED'),'rounded waypoint must not create a return-to-P debt')
 -- Continue around the corner; the next steering handoff must not be blocked by the old P1.
 f:tick(400,95,55);assert(not f:has('route_reason=PRIOR_ROUTE_OBLIGATION_PENDING'));healthy(f)
end)

T('SC1 U-turn starts before the waypoint instead of requiring a node-complete stop',function()
 local f=F({debug_source=true,width=20});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,0,0)
 f:tick(100,0,0);f:tick(200,60,0)
 assert(f.issued==1,'U-turn should enter steering corridor with substantial distance remaining')
 hascmd(f,1,'MOVE',0);assert(f:has('route_mode=STEERING_CORNER'));assert(not f:has('reason=MOVE_AFTER_NODE_COMPLETE'));healthy(f)
end)


T('SC2 early A/B opens near the existing predictive threshold before the SC1 dynamic window',function()
 local f=F({debug_source=true,width=10});f:start();f:emit('MOVE',false,100,0);f:emit('MOVE',true,100,100)
 for i=0,74 do f:tick(100+i*100,i*0.8,0) end
 assert(f.issued==1,'SC2 should hand off around 40m remaining instead of waiting for the ~20m SC1 dynamic corridor')
 assert(f:has('route_mode=STEERING_CORNER'))
 assert(f:has('corner_base=19.500000') and f:has('corner_early=41.500000'),'diagnostic must prove early threshold, not SC1 base, opened the gate')
 assert(f:has('remaining=40.000') or f:has('remaining=40.800'))
 healthy(f)
end)

T('R4 route debt does not fault while the old waypoint is still making measurable progress',function()
 local f=F({debug_source=true});f:start();f.enemy.x=300;f.enemy.z=0
 f:emit('MOVE',false,100,0);f:emit('MOVE',true,200,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,80,0);assert(f.issued==1);f:deliver()
 -- Finish the successor without crossing the transferred 100,0 waypoint.
 f:tick(300,120,50);f:tick(400,200,0)
 assert(f:has('ACTION_COMPLETE') and f:has('action=2'))
 -- Spend more than the old 2s fixed deadline continuously moving back toward the debt.
 local x=195
 for t=500,3000,100 do x=x-3;f:tick(t,x,0) end
 assert(not f:has('ROUTE_UNRECOVERABLE'),'continuous debt progress must not be killed by a wall-clock deadline')
 f:tick(3100,100,0);assert(f:has('ROUTE_OBLIGATION_SATISFIED'));healthy(f)
end)

T('Move to Attack cannot use braking until the waypoint route is safe',function()
 local f=F({debug_source=true});f:start();f.enemy.x=200;f.enemy.z=200
 f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,70,0);f:tick(300,70.2,0)
 assert(f.issued==0 and f:has('ATTACK_ROUTE_PROTECT'))
 f:tick(400,97.5,0);assert(f.issued==1);hascmd(f,1,'ATTACK');healthy(f)
end)

T('Move to Attack uses a formation-aware reached envelope before idle, while a short leg stays protected',function()
 local f=F({width=40,debug_source=true});f:start();f.enemy.x=200;f.enemy.z=0
 f.unit.idle=false;f.unit.moving=true;f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 f:tick(100,0,0);f:tick(200,89,0);assert(f.issued==0,'11m remaining is outside the 10m long-leg envelope')
 f:tick(300,90.5,0);assert(f.issued==1,'long Move should hand off before an idle stop once the route node is actually reached')
 hascmd(f,1,'ATTACK');assert((f:has('reason=ROUTE_NODE_REACHED') or f:has('reason=ROUTE_NODE_PASSED')) and f:has('reason=ATTACK_AFTER_ROUTE_COMPLETE'));healthy(f)
 local s=F({width=40,debug_source=true});s:start();s.enemy.x=100;s.enemy.z=0;s.unit.idle=false;s.unit.moving=true
 s:emit('MOVE',false,20,0);s:emit('ATTACK',true,nil,nil,'2001')
 s:tick(100,0,0);s:tick(200,15,0);assert(s.issued==0,'short 20m leg must not use the full formation-width envelope')
 s:tick(300,16.2,0);assert(s.issued==1,'short-leg fraction permits handoff only after the current node is substantially preserved')
 healthy(s)
end)

T('completed Attack with no tail stays completed and a later Move exits immediately',function()
 local f=attack_root(false);run_attack_hold(f,200,6000);assert(f.issued==0)
 assert(f:has('ATTACK_HOLD_READY_NO_TAIL') and f:has('completion_latched=true'))
 f.unit.melee=false;f.unit.target=nil;f:emit('MOVE',true,-80,20);f:tick(6100)
 assert(f.issued==1);hascmd(f,1,'MOVE',-80);assert(f:has('ATTACK_COMPLETE_LATCHED'));healthy(f)
end)

T('exit block may advance through internal Move nodes before disengagement, but not into next Attack',function()
 local f=attack_root(true);f:emit('MOVE',true,-80,0);f:emit('ATTACK',true,nil,nil,'2001')
 -- Keep unit_distance at zero to model continued physical contact regardless center movement.
 function f.unit:unit_distance()return self.box_gap or 0 end;f.unit.box_gap=0
 run_attack_hold(f,200,6000);assert(f.issued==1);hascmd(f,1,'MOVE',-28)
 f:deliver();f:tick(6100,-8,0)
 f:tick(6200,-26,0);assert(f.issued==2,'internal exit Move must continue even before disengagement');hascmd(f,2,'MOVE',-80)
 f:deliver();f:tick(6300,-26,0);f:tick(6400,-79,0);f:tick(6500,-80,0)
 assert(f.issued==2,'next Attack must remain behind exit obligation')
 -- Stable clear evidence commits the block; then the already-complete route can cross to Attack.
 f.unit.melee=false;f.unit.target=nil;f.unit.box_gap=10
 for t=6600,7800,100 do f:tick(t,-80,0)end
 assert(f:has('EXIT_BLOCK_COMMITTED'));assert(f.issued==3);hascmd(f,3,'ATTACK');healthy(f)
end)

T('stalled post-Attack exit reasserts the same Move only after a stall and is bounded',function()
 local f=attack_root(true);function f.unit:unit_distance()return self.box_gap or 0 end;f.unit.box_gap=0
 run_attack_hold(f,200,6000);assert(f.issued==1);hascmd(f,1,'MOVE',-28)
 f:deliver();f:tick(6100,-8,0)
 -- No progress, still engaged with source target. No immediate spam.
 for t=6200,7100,100 do f:tick(t,-8,0)end;assert(f.issued==1)
 for t=7200,7600,100 do f:tick(t,-8,0)end;assert(f.issued==2);hascmd(f,2,'MOVE',-28);assert(f:has('EXIT_BLOCK_REASSERT'))
 f:deliver();f:tick(7700,-8,0)
 for t=7800,9300,100 do f:tick(t,-8,0)end;assert(f.issued==3);hascmd(f,3,'MOVE',-28)
 f:deliver();f:tick(9400,-8,0);for t=9500,22000,100 do f:tick(t,-8,0);if f.native_pending then f:deliver() end end
 assert(f:count('EXIT_BLOCK_REASSERT')==4 and f.issued==5,'exit recovery is bounded to four reasserts');healthy(f)
end)


T('SC5 stale V3 Exit body evidence falls back to positive contact and reasserts the accepted Move',function()
 local f=F({width=40,debug_source=true,native_evidence_v3=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 function f.unit:unit_distance()return self.box_gap or 0 end;f.unit.box_gap=0
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-28,0);f:tick(100)
 run_attack_hold(f,200,6000);assert(f.issued==1);hascmd(f,1,'MOVE',-28)
 f:deliver();f:tick(6100,-8,0)
 for t=6200,6900,100 do f:tick(t,-8,0)end
 assert(f.issued==1,'SC5 fallback must still wait for the bounded 900ms physical stall window')
 f:tick(7000,-8,0)
 assert(f.issued==2,'stale V3 EntitySnapshot plus positive contact and stalled Exit must reassert once')
 hascmd(f,2,'MOVE',-28)
 assert(f:has('evidence=V3_ENTITY_STALE_CONTACT_FALLBACK') and f:has('v3_reason=ENTITY_STALE'))
 healthy(f)
end)

T('SC5 sticky melee without positive enemy contact never triggers the stale-V3 fallback',function()
 local f=F({width=40,debug_source=true,native_evidence_v3=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0;f.unit.melee=true;f.unit.target=f.enemy
 function f.unit:unit_distance()return self.box_gap or 0 end;f.unit.box_gap=0
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-28,0);f:tick(100)
 run_attack_hold(f,200,6000);assert(f.issued==1);f:deliver();f:tick(6100,-8,0)
 f.unit.box_gap=50 -- keep the intentionally sticky melee flag, but remove real contact evidence.
 for t=6200,9000,100 do f:tick(t,-8,0)end
 assert(f.issued==1,'sticky melee alone must never cause Exit command spam')
 assert(not f:has('V3_ENTITY_STALE_CONTACT_FALLBACK'))
 healthy(f)
end)

T('native target match cannot skip an unfinished exit Move',function()
 local f=attack_root(true);f:emit('ATTACK',true,nil,nil,'2001');run_attack_hold(f,200,6000)
 assert(f.issued==1);f:deliver();f:tick(6100,-8,0)
 -- Same target can remain attached from the old engagement; this is not successor proof.
 f.unit.melee=true;f.unit.target=f.enemy;f:tick(6200,-12,0)
 assert(f.issued==1 and not f:has('NATIVE_SUCCESSOR_ADOPTED'));healthy(f)
end)

T('native target match cannot skip an unfinished ordinary Move',function()
 local f=F({debug_source=true});f:start();f.enemy.x=100;f.enemy.z=100
 f:emit('MOVE',false,100,0);f:emit('ATTACK',true,nil,nil,'2001')
 f.unit.target=f.enemy;f.unit.melee=true
 f:tick(100,0,0);f:tick(200,50,0)
 assert(not f:has('ACTION_COMPLETE'))
 assert(not f:has('NATIVE_SUCCESSOR_ADOPTED'),'target match is only a clue until the Move is independently complete')
 assert(f.issued==0,'unsafe route must not be bypassed by stale/automatic target state');healthy(f)
end)

T('completed Move plus matching target still needs independent native action identity',function()
 local f=F({cold_idle=true,debug_source=true});f:start();f.unit.idle=false;f.unit.moving=true
 f:emit('MOVE',false,100,0);f:tick(100,0,0);f:tick(200,70,0);f.unit.idle=true;f.unit.moving=false
 for t=300,1100,100 do f:tick(t,85,0)end;assert(f:has('ACTION_COMPLETE'))
 f:emit('ATTACK',true,nil,nil,'2001');f.unit.target=f.enemy;f.unit.melee=true;f:tick(1200,85,0)
 assert(f.issued==0 and not f:has('NATIVE_SUCCESSOR_ADOPTED'));assert(f:has('BLOCKED_EXECUTION_IDENTITY'));healthy(f)
end)

T('ordinary RMB replacement still overrides every block obligation',function()
 local f=attack_root(true);run_attack_hold(f,200,2500);f:emit('MOVE',false,120,0);f:tick(2600)
 assert(f:has('GEN_CANCEL') and f:has('reason=EXTERNAL_REPLACE'));for t=2700,8000,100 do f:tick(t)end
 assert(f.issued==0);healthy(f)
end)

T('FEG4 matched-melee extended formation contact can hold without center-distance relock',function()
 local f=F({width=40,debug_source=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-70;f.unit.z=0
 function f.unit:unit_distance()return 0 end
 f.unit.target=f.enemy;f.unit.melee=false;f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0);f:tick(100,-70,0)
 -- Establish non-melee/fresh + approach history, then remain in matched melee at 55m center separation.
 for t=200,800,100 do f:tick(t,-70+(t-100)*15/700,0)end
 f.unit.melee=true
 for t=900,6500,100 do f:tick(t,-55,0)end
 assert(f:has('strong_far=60.000000'));assert(f:has('evidence=MATCHED_MELEE'))
 assert(f.issued==1);hascmd(f,1,'MOVE',-100);assert(not f:has('reason=SEPARATION_RELOCK'));healthy(f)
end)

T('FEG4 extended matched-melee still rejects contact beyond the bounded formation envelope',function()
 local f=F({width=40,debug_source=true});f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-70;f.unit.z=0
 function f.unit:unit_distance()return 0 end
 f.unit.target=f.enemy;f.unit.melee=false;f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,-100,0);f:tick(100,-70,0)
 for t=200,800,100 do f:tick(t,-70+(t-100)*5/700,0)end
 f.unit.melee=true;for t=900,8000,100 do f:tick(t,-65,0)end
 assert(f.issued==0);healthy(f)
end)

print('ACTUAL_INTERPRETER='.._VERSION..'; explicit engine doubles, not WH3')
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
