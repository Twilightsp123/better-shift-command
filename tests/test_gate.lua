-- FEG2: continuous close target-matched melee may qualify despite body movement.
local G=assert(loadfile(assert(arg[1])))()
local pass,fail=0,0
local function T(name,fn)
 local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..name)else fail=fail+1;print('FAIL '..name..' '..tostring(e))end
end
local function sample(now,d,melee,match,az,tz)
 return {now=now,ax=-d,az=az or 0,tx=0,tz=tz or 0,melee=melee~=false,target_match=match~=false}
end
local function constant(g,start,finish,d,step,melee,match)
 local r;for t=start,finish,step or 100 do r=G.update(g,sample(t,d,melee,match))end;return r
end
T('residual melee far never opens over 90 seconds',function()
 local g=G.new(0,40,40);for t=0,90000,100 do assert(not G.update(g,sample(t,80)).allow)end
end)
T('brief passage through the near band cannot open contact',function()
 local g=G.new(0,40,40)
 for t=0,6100,100 do assert(not G.update(g,sample(t,90-t/100)).allow)end
 -- Only 500ms of near-band contact, then the reported melee disappears.
 for t=6200,9000,100 do assert(not G.update(g,sample(t,20,false)).allow)end
end)
T('far slowdown obstacle is not an impact',function()
 local g=G.new(0,40,40);for t=0,3000,100 do G.update(g,sample(t,120-t/100))end
 for t=3100,15000,100 do local r=G.update(g,sample(t,90));assert(not r.open and not r.allow,'far obstacle transiently opened gate')end
end)
T('sustained close melee opens without requiring a false edge or static body',function()
 local g=G.new(0,40,40);local first
 for t=0,7000,100 do local z=G.update(g,sample(t,90-t/100));if z.just_opened then first=t end end
 local z=constant(g,7100,9000,20)
 assert(z.allow and first and first>=6800 and g.open_mode=='SUSTAINED_NEAR_CONTACT')
end)
T('close start requires warmup plus stable confirmation',function()
 local g=G.new(0,40,40)
 for t=0,1500,100 do assert(not G.update(g,sample(t,8)).allow)end
 local r=G.update(g,sample(1600,8));assert(r.allow and r.just_opened and r.reason=='CLOSE_START_SETTLED')
end)
T('no charge field/API is required',function()
 local g=G.new(0);assert(constant(g,0,2000,9).allow)
end)
T('false-to-true while body far does not bypass geometry',function()
 local g=G.new(0);constant(g,0,1000,90,100,false)
 assert(g.fresh_seen);assert(not constant(g,1100,12000,90).allow)
end)
T('fresh melee near and settled opens',function()
 local g=G.new(0);constant(g,0,1000,10,100,false)
 local r=constant(g,1100,2000,10);assert(r.allow and g.open_mode=='FRESH_MELEE_NEAR_SETTLED')
end)
T('wrong target never opens even at zero distance',function()
 local g=G.new(0);assert(not constant(g,0,10000,0,100,true,false).allow)
end)
T('correct target without melee never opens',function()
 local g=G.new(0);assert(not constant(g,0,10000,0,100,false,true).allow)
end)
T('missing position and NaN never open',function()
 local g=G.new(0);local s=sample(0,8);s.tx=nil;assert(not G.update(g,s).allow)
 s=sample(100,8);s.ax=0/0;assert(not G.update(g,s).allow)
end)
T('long sample gap resets confirmation rather than crediting absence',function()
 local g=G.new(0);constant(g,0,1200,8);local r=G.update(g,sample(10000,8));assert(not r.allow)
 assert(not constant(g,10100,11400,8).allow);assert(constant(g,11500,11700,8).allow)
end)
T('journal input gap resets rate window',function()
 local g=G.new(0);constant(g,0,1200,8);local s=sample(1300,8);s.input_gap=true
 local r=G.update(g,s);assert(not r.allow and r.reason=='OBSERVATION_GAP')
end)
T('pause duplicate timestamp advances nothing',function()
 local g=G.new(0);constant(g,0,1200,8);local before=g.candidate_ms
 for i=1,100 do assert(not G.update(g,sample(1200,8)).allow)end
 assert(g.candidate_ms==before and not g.opened)
end)
T('500ms model cadence supported',function()
 local g=G.new(0);assert(constant(g,0,2000,8,500).allow)
end)
T('1000ms model cadence supported',function()
 local g=G.new(0);assert(constant(g,0,3000,8,1000).allow)
end)
T('confirmed contact is not denied just because the body keeps moving',function()
 local g=G.new(0);constant(g,0,2000,20)
 for t=2100,2700,100 do assert(G.update(g,sample(t,20-(t-2000)/100)).allow)end
end)
T('close moving melee needs sustained confirmation then may accumulate hold',function()
 local g=G.new(0);local first
 for t=0,9000,100 do local z=sample(t,8);z.ax=t/100;z.tx=z.ax+8
  local out=G.update(g,z);if out.just_opened then first=t end
  if t<1700 then assert(not out.allow)end
 end
 assert(g.opened and first and first>=1700 and first<=2000)
end)
T('transient melee false suspends but does not erase open episode',function()
 local g=G.new(0);constant(g,0,2000,8);local r=G.update(g,sample(2100,8,false))
 assert(not r.allow and g.opened and not r.reset_hold);assert(G.update(g,sample(2200,8)).allow)
end)
T('far separation sustained relocks and requests credit reset',function()
 local g=G.new(0);constant(g,0,2000,20)
 for t=2100,6500,100 do G.update(g,sample(t,20+(t-2000)/100))end
 assert(not g.opened and g.episode==2)
end)
T('new Attack resets gate independent of previous engagement',function()
 local g=G.new(0);constant(g,0,2000,10);assert(g.opened)
 local h=G.new(2100);assert(not G.update(h,sample(2100,60)).allow and not h.opened)
end)
T('changing widths later cannot inflate the frozen gate',function()
 local g=G.new(0,40,40);local s=sample(0,80);s.own_width=500;s.target_width=500
 G.update(g,s);assert(g.near==28)
end)
T('missing widths use explicit fallback; extreme widths are capped',function()
 assert(G.new(0).near==28);assert(G.new(0,500,500).near==34);assert(G.new(0,0,0).near==16)
end)
T('teleport/discontinuity resets sampling and cannot prove contact',function()
 local g=G.new(0);constant(g,0,2000,180)
 local r=G.update(g,sample(2100,8));assert(not r.allow and r.discontinuity)
end)
T('position read failure after open suspends immediately',function()
 local g=G.new(0);constant(g,0,2000,8);local s=sample(2100,8);s.tz=nil
 assert(not G.update(g,s).allow and g.opened)
end)
T('clock reversal is refused',function()
 local g=G.new(0);G.update(g,sample(1000,8));assert(not pcall(G.update,g,sample(900,8)))
end)
print('ACTUAL_INTERPRETER='.._VERSION)
print('TOTAL '..pass..' PASS '..fail..' FAIL')
os.exit(fail==0 and 0 or 1)
