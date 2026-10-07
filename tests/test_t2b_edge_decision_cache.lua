local C=assert(loadfile(arg[1]))()
local pass,fail=0,0
local function T(n,fn)local ok,e=pcall(fn);if ok then pass=pass+1;print('PASS '..n)else fail=fail+1;print('FAIL '..n..' :: '..tostring(e))end end
local d={reason='H',route_ok=true,current_credit='ATTACK_TERMINAL_HANDOFF',issue_route_mode='BLOCKED',adopt_route_mode='ATTACK_TERMINAL_HYSTERESIS',issue_window={open=false,reason='WAIT'},adopt_window={open=true,reason='H'}}
local g={remaining=3.5,arrival_sync_margin=.5}
T('one poll',function()local c=C.capture{gen=7,current_action_id='11',successor_action_id='12',sample_ms=1000,poll_ms=100,decision=d,geometry=g};local r,w=C.read(c,{gen=7,current_action_id='11',successor_action_id='12',now_ms=1100,current_step_ms=100});assert(r and w=='OK')end)
T('stale',function()local c=C.capture{gen=7,current_action_id='11',successor_action_id='12',sample_ms=1000,poll_ms=100,decision=d,geometry=g};local r=C.read(c,{gen=7,current_action_id='11',successor_action_id='12',now_ms=1101,current_step_ms=100});assert(r==nil)end)
T('identity',function()local c=C.capture{gen=7,current_action_id='11',successor_action_id='12',sample_ms=1000,poll_ms=100,decision=d,geometry=g};local r=C.read(c,{gen=7,current_action_id='11',successor_action_id='13',now_ms=1050,current_step_ms=100});assert(r==nil)end)
T('variable poll',function()local c=C.capture{gen=7,current_action_id='11',successor_action_id='12',sample_ms=1000,poll_ms=100,decision=d,geometry=g};local r=C.read(c,{gen=7,current_action_id='11',successor_action_id='12',now_ms=1300,current_step_ms=300});assert(r)end)
T('freeze geometry',function()local x={remaining=3.5,arrival_sync_margin=.5,nested={x=1}};local c=C.capture{gen=7,current_action_id='11',successor_action_id='12',sample_ms=1000,poll_ms=100,decision=d,geometry=x};x.remaining=99;assert(c.geometry.remaining==3.5 and c.geometry.nested==nil)end)
print('TOTAL '..pass..' PASS '..fail..' FAIL');os.exit(fail==0 and 0 or 1)
