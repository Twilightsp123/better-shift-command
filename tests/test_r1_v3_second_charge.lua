-- Center-A2 authoritative second-charge regressions.
-- EntitySnapshot/FrozenHandoff/ContactPair remain telemetry only in this architecture.
local F=assert(loadfile(assert(arg[2])))().new
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local function deliver_all(f) while f.native_pending do f:deliver() end end
local function tick(f,t,x,z) f:tick(t,x or f.unit.x,z or 0);deliver_all(f) end
local function setup(p1,p2,opts)
 opts=opts or {};opts.cold_idle=true;opts.width=40;opts.debug_source=true
 local f=F(opts);f:start();f.enemy.x=0;f.enemy.z=0;f.unit.x=-8;f.unit.z=0
 f.unit.idle=false;f.unit.moving=true;f.unit.melee=true;f.unit.target=f.enemy
 f:emit('ATTACK',false,nil,nil,'2001');f:emit('MOVE',true,p1,0);f:emit('ATTACK',true,nil,nil,'2001');f:emit('MOVE',true,p2,0)
 for t=100,6000,100 do tick(f,t,-8) end
 assert(f.commands[1] and f.commands[1].draft.kind=='MOVE','A1 must release Exit P1')
 return f
end
T('route-complete Exit issues A2 without EntitySnapshot and fresh approach releases P2',function()
 local f=setup(-100,-160)
 f.unit.melee=true;f.unit.target=nil;local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK','P1 completion must issue A2 without entity evidence')
 for t=9600,13500,100 do local p=(t-9600)/3900;local ax=-100+math.min(80,80*p);f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,ax) end
 for t=13600,18500,100 do f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,-20) end
 assert(f.commands[3] and f.commands[3].draft.kind=='MOVE','fresh A2 approach + hold must release P2')
 assert(f:has('CENTER_A2_APPROACH_SEEN') and f:has('CENTER_A2_FIRST_CREDIT') and f:has('ATTACK_HOLD_DONE'))
end)
T('A2 start-near stationary sticky melee cannot borrow A1 contact',function()
 local f=setup(-20,-80);f.unit.melee=true;f.unit.target=nil;local x=-8
 for t=6100,7600,100 do x=math.max(-20,x-1);tick(f,t,x) end
 for t=7700,9000,100 do tick(f,t,-20) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK')
 local n=#f.commands
 for t=9100,17000,100 do f.unit.melee=true;f.unit.target=f.enemy;f.unit.moving=false;tick(f,t,-20) end
 assert(#f.commands==n,'stationary sticky melee after A2 ACK must not release P2')
 assert(not f:has('CENTER_A2_FIRST_CREDIT'),'old sticky melee must not create fresh credit')
end)
T('A2 explicit melee-clear creates a fresh episode and can release P2',function()
 local f=setup(-20,-80);f.unit.melee=true;f.unit.target=nil;local x=-8
 for t=6100,7600,100 do x=math.max(-20,x-1);tick(f,t,x) end
 for t=7700,9000,100 do tick(f,t,-20) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK')
 for t=9100,9700,100 do f.unit.melee=false;f.unit.target=nil;tick(f,t,-20) end
 for t=9800,15500,100 do f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,-20) end
 assert(f:has('CENTER_A2_FRESH_SEEN'));assert(f.commands[3] and f.commands[3].draft.kind=='MOVE')
end)
T('wrong target after A2 ACK cannot credit fresh-mode hold',function()
 local f=setup(-100,-160);local other=f:add_enemy_reinforcement('2002',0,10);f.unit.melee=true;f.unit.target=nil;local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK')
 for t=9600,17500,100 do local p=(t-9600)/7900;local ax=-100+math.min(80,80*p);f.unit.melee=true;f.unit.target=other;tick(f,t,ax) end
 assert(not f.commands[3],'wrong target must never release P2')
end)
T('missing V3 physical evidence is telemetry only and cannot veto A2',function()
 local f=setup(-100,-160)
 f.unit.melee=false;f.unit.target=nil;local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 assert(f.commands[2] and f.commands[2].draft.kind=='ATTACK','physical evidence failure cannot veto route-complete A2')
 assert(not f:has('code=BLOCKED_EVIDENCE'),'Entity/Contact gap may not become a behavior fault')
end)
T('same-target A2 credit always starts after ACK-side fresh or approach evidence',function()
 local f=setup(-100,-160);f.unit.melee=true;f.unit.target=nil;local x=-8
 for t=6100,9500,100 do x=math.max(-100,x-3);tick(f,t,x) end
 for t=9600,14500,100 do local p=(t-9600)/4900;local ax=-100+math.min(80,80*p);f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,ax) end
 for t=14600,18500,100 do f.unit.melee=true;f.unit.target=f.enemy;tick(f,t,-20) end
 local first_credit,proof=nil,nil
 for _,line in ipairs(f.logs) do
  local ms=tonumber(line:match('model_ms=(%d+)'))
  if line:find('CENTER_A2_FRESH_SEEN',1,true) or line:find('CENTER_A2_APPROACH_SEEN',1,true) then proof=proof or ms end
  if line:find('CENTER_A2_FIRST_CREDIT',1,true) then first_credit=first_credit or ms end
 end
 assert(proof and first_credit and proof<=first_credit,'A2 credit must never precede fresh/approach proof')
end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
