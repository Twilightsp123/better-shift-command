-- Runs the ACTUAL client using typed DLL fixtures, NOT a native WH3 interpreter.
local ROOT = assert(arg[1], 'project root required')
print('ACTUAL_TEST_INTERPRETER=' .. _VERSION)
print('FIXTURE_VERSION_OVERRIDE=Lua 5.1; actual DLL and battle manager are NOT executed')
local passes, failures = 0, 0
local function eq(a,b) assert(a==b, tostring(a)..' != '..tostring(b)) end
local function has(logs,text)
    for _,v in ipairs(logs) do if v:find(text,1,true) then return true end end
    return false
end
local function dec(n) return string.format('%.0f',n) end
local function order(n,epoch)
    return {epoch=epoch or '1',serial=dec(n),command_id=dec(n),script_issue_id='0',
      unit_uid='1003',unit_revision='1',engine_seq='0',flags_valid_mask='15',
      engine_seq_valid=true,source='UNKNOWN',status='ACCEPTED',order_type='MOVE',
      is_queued=false,dest_x=1,dest_y=2,dest_z=3,batch_index=0,batch_total=0}
end
local function fixture(opts)
    opts=opts or {}
    local f={logs={},phases={},timers={},calls={begin=0,read=0,finish=0,start=0,remove=0,commands=0},
        records={},epoch=opts.epoch or '1',recording=false,installed=false,current=opts.phase or 'Startup'}
    local b={}
    function b:out(t) f.logs[#f.logs+1]=t end
    function b:register_phase_change_callback(p,fn)
        if opts.registration_error==p then error('INJECT_REGISTER_ERROR') end
        f.phases[p]=f.phases[p] or {};table.insert(f.phases[p],fn)
    end
    function b:repeat_real_callback(fn,ms,key)
        eq(ms,200); if opts.timer_error then error('INJECT_TIMER_ERROR') end
        f.timers[key]=fn
    end
    function b:remove_real_callback(key) f.calls.remove=f.calls.remove+1; f.timers[key]=nil end
    function b:get_current_phase_name() if opts.phase_error then error('INJECT_PHASE_ERROR') end;return f.current end
    f.b=b
    local bridge={}
    function bridge.version() if opts.version_error then error('VERSION_THROW') end;return opts.version or '0.1.1-observer-floatabi' end
    function bridge.number_abi_probe() return opts.bad_number and 0 or 16777215,1.5 end
    function bridge.exact_id_probe() if opts.numeric_ids then return 4294967295,16777217 end;return '4294967295','16777217' end
    function bridge.capabilities()
        if opts.caps_error then error('CAPS_THROW') end
        return {host_lua_number='float32',host_lua_number_bytes=4,
          exact_source=opts.exact_source or false,verified_issue=false,controller_connected=false,
          complete_command_batch=false,observer_hooks_installed=f.installed and not opts.inactive_caps,
          queued_from_native_entry=f.installed and not opts.inactive_caps}
    end
    function bridge.start_observer(ack)
        f.calls.start=f.calls.start+1;eq(ack,true)
        if opts.start_throw then error('START_THROW') end
        if opts.backend_missing then return false,'MINHOOK_BACKEND_MISSING_BUILD_BACKEND_FIRST' end
        f.installed=true;return true
    end
    function bridge.begin_battle(session)
        f.calls.begin=f.calls.begin+1
        assert(type(session)=='string' and #session<=64)
        if opts.begin_throw then error('BEGIN_THROW') end
        if opts.begin_failure then return nil,'BEGIN_DENIED' end
        f.recording=true
        if opts.old_fake_two_returns then return true,f.epoch end
        return opts.numeric_epoch and 1 or f.epoch
    end
    function bridge.end_battle(epoch)
        f.calls.finish=f.calls.finish+1;eq(epoch,f.epoch); f.recording=false
        if opts.end_failure then return nil,'END_DENIED' end
        return true
    end
    function bridge.get_status() return {epoch=f.epoch,recording=f.recording and not opts.status_inactive} end
    function bridge.issue_verified_command() f.calls.commands=f.calls.commands+1;error('UNEXPECTED_COMMAND') end
    function bridge.read_journal(epoch,after,count)
        f.calls.read=f.calls.read+1
        if opts.read_throw then error('READ_THROW') end
        if opts.read_failure then return nil,'OldEpoch' end
        eq(epoch,f.epoch)
        if not opts.old_fake_two_returns then eq(type(after),'string') end
        local cursor=tonumber(after) -- fixture implementation uses actual Lua5.3 doubles; NOT production ID logic.
        local rows={}; for _,r in ipairs(f.records) do
            if tonumber(r.serial)>cursor and #rows<count then rows[#rows+1]=r end
        end
        local newest=#f.records>0 and f.records[#f.records].serial or after
        local meta={epoch=epoch,oldest_serial=#f.records>0 and f.records[1].serial or '0',
          newest_serial=newest,next_after=#rows>0 and rows[#rows].serial or after,
          dropped='0',count=#rows,overrun=false,complete=true,error='Ok',journal_fault='Ok'}
        if opts.mutate then opts.mutate(rows,meta,f) end
        return rows,meta
    end
    if opts.missing_api then bridge[opts.missing_api]=nil end
    f.bridge=bridge
    local inherited={bm=b,out=function(t)f.logs[#f.logs+1]=t end}
    local env={_VERSION=opts.real_version and _VERSION or 'Lua 5.1',
        package={loadlib=function()
            if opts.load_failure then return nil,'INJECT_LOAD_FAILURE' end
            return function() if opts.init_throw then error('INIT_THROW') end;return bridge end
        end}}
    if not opts.globals_via_metatable then
        env.bm=inherited.bm; env.out=inherited.out
    end
    env._G=env
    setmetatable(env,{__index=function(_,k)
        if inherited[k] ~= nil then return inherited[k] end
        return _G[k]
    end})
    f.env=env
    function f.load(path)
        local fn=assert(loadfile(path or ROOT..'/lua/queue_probe.lua','t',env));return fn()
    end
    function f.phase(p) f.current=p;for _,fn in ipairs(f.phases[p] or {}) do fn() end end
    function f.tick()
        local pending={}; for _,fn in pairs(f.timers) do pending[#pending+1]=fn end
        for _,fn in ipairs(pending) do fn() end
    end
    function f.state()return env.__WH3_OBSERVER_V022_CLIENT end
    function f.active() f.load();f.phase('Deployment');return f end
    function f.put(n)for i=1,n do f.records[#f.records+1]=order(i,f.epoch) end end
    return f
end
local function test(name,fn)
    local ok,err=pcall(fn)
    if ok then passes=passes+1; print('PASS '..name)
    else failures=failures+1; print('FAIL '..name..': '..tostring(err)) end
end
local function fails(opts,text)
    local f=fixture(opts);f.active();f.records={order(1,f.epoch)};f.tick()
    assert(has(f.logs,text),table.concat(f.logs,'\n'));eq(f.calls.commands,0);return f
end

test('old production client: one-string begin success leads to nil epoch and zero reads',function()
    local f=fixture(); f.put(2);f.load(ROOT..'/original/queue_probe_v02.lua');f.phase('Deployment');f.tick()
    eq(f.calls.begin,1);eq(f.calls.read,0);assert(has(f.logs,'BATTLE_STARTED epoch=nil'))
    f.phase('Complete');eq(f.calls.finish,0)
end)
test('old client isolated second bug: force two-return begin fixture exposes string-number comparison',function()
    local f=fixture({old_fake_two_returns=true});f.put(1)
    f.load(ROOT..'/original/queue_probe_v02.lua');f.phase('Deployment')
    local ok,err=pcall(f.tick);eq(ok,false);assert(tostring(err):find('compare'))
end)
test('v0.2.1 rawget regression: inherited WH3 globals leave only ENTER and no observer start',function()
    local f=fixture({globals_via_metatable=true});
    f.load(ROOT..'/original/queue_probe_v021.lua')
    eq(f.calls.start,0);eq(f.calls.begin,0)
    assert(has(f.logs,'[BRIDGE_OBSERVER_V021] ENTER'))
    assert(not has(f.logs,'ABI_OK'))
end)
test('v0.2.2 resolves inherited WH3 globals and initializes observer',function()
    local f=fixture({globals_via_metatable=true});f.put(1);f.active()
    eq(f.calls.start,1);eq(f.calls.begin,1);eq(f.state().records,'1')
    assert(has(f.logs,'ABI_OK'));assert(has(f.logs,'HOOKS_ACTIVE'));assert(has(f.logs,'BATTLE_STARTED epoch=1'))
end)
test('single-return string epoch starts and reads real client',function()
    local f=fixture();f.put(2);f.active();eq(f.state().epoch,'1');eq(f.state().records,'2');eq(f.state().cursor,'2')
    eq(f.calls.begin,1);eq(f.calls.commands,0);assert(has(f.logs,'ORDER_OBSERVED'))
end)
test('native engine sequence zero is valid',function()
    local f=fixture();f.put(1);f.active();assert(has(f.logs,'engine_seq=0 engine_seq_valid=true'))
end)
test('maximum u32 and above-float24 native identifiers preserved',function()
    local f=fixture({epoch='4294967295'}); local r=order(16777217,f.epoch)
    r.engine_seq='4294967295';r.command_id='16777217';f.records={r};f.active()
    eq(f.state().cursor,'16777217');assert(has(f.logs,'engine_seq=4294967295'))
    f.records[#f.records+1]=order(4294967295,f.epoch);f.tick();eq(f.state().cursor,'4294967295')
end)
test('decimal ordering crosses 9 to 10 and 99 to 100',function()
    local f=fixture();f.put(120);f.active();eq(f.state().records,'120');eq(f.state().cursor,'120')
end)
test('pagination uses next_after, does not jump to newest',function()
    local f=fixture();f.put(150);f.active();eq(f.calls.read,3);eq(f.state().records,'150')
end)
test('512-record tick budget defers but next tick completes backlog',function()
    local f=fixture();f.put(600);f.active();eq(f.state().records,'512');assert(has(f.logs,'BACKLOG_DEFERRED'))
    f.tick();eq(f.state().records,'600');eq(f.state().cursor,'600')
end)
test('empty pages do not duplicate consumed records',function()
    local f=fixture();f.put(5);f.active();f.tick();f.tick();eq(f.state().records,'5')
end)
test('no records logs waiting, never acceptance PASS',function()
    local f=fixture().active();f.tick();assert(has(f.logs,'WAITING_NATIVE_RECORDS'));eq(f.state().records,'0')
    assert(not has(f.logs,'ORDER_OBSERVED'));assert(not has(f.logs,'PASS'))
end)
test('overrun surfaces gap and retains only returned records',function()
    local f=fixture({mutate=function(_,m) m.overrun=true;m.error='Overrun';m.complete=false;m.dropped='7' end})
    f.records={order(8)};f.active();eq(f.state().gaps,'1');eq(f.state().records,'1');assert(has(f.logs,'JOURNAL_GAP'))
end)
test('native failure record stays failure with invalid sequence flag',function()
    local f=fixture();local r=order(1);r.status='REJECTED_NATIVE';r.engine_seq_valid=false;r.flags_valid_mask='0';r.is_queued=nil
    f.records={r};f.active();assert(has(f.logs,'status=REJECTED_NATIVE'));assert(has(f.logs,'engine_seq_valid=false is_queued=nil'))
end)
test('queued false, true and unavailable remain distinct',function()
    local f=fixture();f.put(3);f.records[2].is_queued=true;f.records[3].is_queued=nil;f.active()
    for _,v in ipairs({'false','true','nil'})do assert(has(f.logs,'is_queued='..v))end
end)
test('unknown source is not rewritten to player',function()
    local f=fixture();f.put(1);f.active();assert(has(f.logs,'source=UNKNOWN'));assert(not has(f.logs,'EXTERNAL_PLAYER'))
end)
test('attack target, raw flags and batch status retained',function()
    local f=fixture();local r=order(1);r.order_type='ATTACK';r.target_uid='16777217';r.target_root='0x00000000ABCDEF10';r.raw70=1
    r.dest_x=nil;r.dest_y=nil;r.dest_z=nil;f.records={r};f.active()
    assert(has(f.logs,'target_uid=16777217 target_root=0x00000000ABCDEF10 raw70=1'))
end)
test('Deployed fallback starts only one session',function()
    local f=fixture();f.load();f.phase('Deployed');f.phase('Deployment');eq(f.calls.begin,1)
end)
test('late initialization in Deployment starts immediately',function()
    local f=fixture({phase='Deployment'});f.load();eq(f.calls.begin,1)
end)
test('late initialization in Deployed starts immediately',function()
    local f=fixture({phase='Deployed'});f.load();eq(f.calls.begin,1)
end)
test('late initialization in VictoryCountdown starts immediately',function()
    local f=fixture({phase='VictoryCountdown'});f.load();eq(f.calls.begin,1)
end)
test('late Complete does not start a session',function()
    local f=fixture({phase='Complete'});f.load();eq(f.calls.begin,0);eq(f.state().stopped,true)
end)
test('Complete drains, ends once, removes real callback',function()
    local f=fixture().active();f.put(5);f.phase('Complete');f.phase('Complete');f.tick()
    eq(f.state().records,'5');eq(f.calls.finish,1);eq(f.calls.remove,1);eq(next(f.timers),nil)
end)
test('duplicate script execution does not double hooks or listeners',function()
    local f=fixture().active();f.load();eq(f.calls.start,1);eq(f.calls.begin,1);assert(has(f.logs,'DUPLICATE_ENTRY_IGNORED'))
end)
test('new battle manager closes old client',function()
    local a=fixture().active();local b=fixture({epoch='2'});b.env.__WH3_OBSERVER_V022_CLIENT=a.state();b.active()
    eq(a.calls.finish,1);eq(a.state().stopped,true);eq(b.state().epoch,'2')
end)
test('missing backend fails before any session or timer',function()
    local f=fails({backend_missing=true},'MINHOOK_BACKEND_MISSING_BUILD_BACKEND_FIRST')
    eq(f.calls.begin,0);eq(next(f.timers),nil)
end)
test('start observer exception handled',function()fails({start_throw=true},'START_THROW')end)
test('claimed start success but inactive caps fails',function()fails({inactive_caps=true},'HOOK_CAPABILITY_NOT_ACTIVE')end)
test('number ABI mismatch prevents hook install',function()local f=fails({bad_number=true},'FAIL NUMBER_ABI');eq(f.calls.start,0)end)
test('numeric exact IDs rejected before hook install',function()local f=fails({numeric_ids=true},'FAIL EXACT_ID_ABI');eq(f.calls.start,0)end)
test('version call failure prevents hook install',function()local f=fails({version_error=true},'FAIL VERSION');eq(f.calls.start,0)end)
test('unexpected DLL version rejected',function()fails({version='0.3'},'FAIL VERSION')end)
test('wrong interpreter rejected without pretending ABI success',function()fails({real_version=true},'WRONG_LUA_VERSION')end)
test('load failure reports and stops',function()fails({load_failure=true},'FAIL LOADLIB')end)
test('module initialization exception handled',function()fails({init_throw=true},'FAIL INIT')end)
test('missing native API detected',function()fails({missing_api='read_journal'},'MISSING_API read_journal')end)
test('capability API exception handled',function()fails({caps_error=true},'FAIL CAPABILITIES')end)
test('unexpected provenance-capable DLL not silently accepted',function()fails({exact_source=true},'NOT_EXPECTED_OBSERVER_BASELINE')end)
test('begin nil,error handled without poller',function()local f=fails({begin_failure=true},'BEGIN_BATTLE BEGIN_DENIED');eq(next(f.timers),nil)end)
test('begin exception handled',function()fails({begin_throw=true},'BEGIN_THROW')end)
test('numeric epoch rejected',function()fails({numeric_epoch=true},'FAIL BEGIN_BATTLE')end)
test('begin status not recording closes session',function()local f=fails({status_inactive=true},'BEGIN_STATUS');eq(f.calls.finish,1)end)
test('timer registration exception closes native session',function()local f=fails({timer_error=true},'REGISTER_TIMER');eq(f.calls.finish,1)end)
test('phase registration exception caught',function()fails({registration_error='Deployment'},'REGISTER_PHASE Deployment')end)
test('Complete registration exception caught',function()fails({registration_error='Complete'},'REGISTER_COMPLETE')end)
test('current phase query exception caught',function()fails({phase_error=true},'GET_PHASE')end)
test('read nil,error exits instead of empty poll success',function()local f=fails({read_failure=true},'READ_NATIVE OldEpoch');eq(f.calls.finish,1)end)
test('read exception exits and releases session',function()local f=fails({read_throw=true},'READ_EXCEPTION');eq(f.calls.finish,1)end)
local mutations={
 {'metadata wrong epoch','READ_EPOCH_MISMATCH',function(_,m)m.epoch='2'end},
 {'metadata numeric cursor','META_ID_TYPE_next_after',function(_,m)m.next_after=0 end},
 {'metadata fault','JOURNAL_FAULT_SerialExhausted',function(_,m)m.journal_fault='SerialExhausted'end},
 {'read error','READ_ERROR_OldEpoch',function(_,m)m.error='OldEpoch'end},
 {'incomplete read','INCOMPLETE_NATIVE_READ',function(_,m)m.complete=false end},
 {'count mismatch','READ_COUNT_MISMATCH',function(_,m)m.count=1 end},
 {'cursor advance on empty page','EMPTY_PAGE_CURSOR_ADVANCE',function(_,m)m.next_after='1';m.newest_serial='1'end},
 {'noncanonical id','META_ID_TYPE_dropped',function(_,m)m.dropped='00'end},
 {'u32 overflow','META_ID_TYPE_dropped',function(_,m)m.dropped='4294967296'end},
 {'metadata status type','META_STATUS_TYPES',function(_,m)m.complete='true'end},
}
for _,t in ipairs(mutations)do test(t[1],function()fails({mutate=t[3]},t[2])end)end
local record_mutations={
 {'numeric serial','RECORD_ID_TYPE_serial',function(r)r.serial=1 end},
 {'record wrong epoch','RECORD_EPOCH_MISMATCH',function(r)r.epoch='2'end},
 {'record serial duplicate','RECORD_SERIAL_ORDER',function(r)r.serial='0'end},
 {'record bool invalid','RECORD_STATUS_TYPES',function(r)r.engine_seq_valid=1 end},
 {'queued number invalid','QUEUED_TYPE',function(r)r.is_queued=0 end},
 {'nan geometry','GEOMETRY_TYPE_dest_x',function(r)r.dest_x=0/0 end},
 {'numeric target UID','TARGET_UID_TYPE',function(r)r.target_uid=1007 end},
 {'numeric pointer','TARGET_ROOT_TYPE',function(r)r.target_root=1007 end},
}
for _,t in ipairs(record_mutations)do test(t[1],function()
    local f=fixture({mutate=function(rows)if #rows>0 then t[3](rows[1]) end end});f.put(1);f.active();assert(has(f.logs,t[2]),table.concat(f.logs,'\n'))
    eq(f.state().records,'0');eq(f.calls.finish,1)
end)end
test('bad second record does not partially commit first record',function()
    local f=fixture();f.put(2);f.records[2].source=nil;f.active();eq(f.state().records,'0');eq(f.state().cursor,'0')
end)
test('next_after cannot skip an unreturned page',function()
    local f=fixture({mutate=function(rows,m)if #rows>0 then m.next_after=m.newest_serial end end});f.put(80);f.active()
    assert(has(f.logs,'NEXT_AFTER_NOT_LAST_RETURNED'));eq(f.state().records,'0')
end)
test('native end error is reported without repeated retries',function()
    local f=fixture({end_failure=true}).active();f.phase('Complete');f.phase('Complete')
    eq(f.calls.finish,1);assert(has(f.logs,'CLEANUP_END_ERROR END_DENIED'))
end)
test('final read budget reports unconsumed backlog explicitly',function()
    local f=fixture().active();f.put(600);f.phase('Complete')
    eq(f.state().records,'512');assert(has(f.logs,'FINAL_BACKLOG_UNREAD'));eq(f.calls.finish,1)
end)
print(string.format('SCENARIOS=%d PASS=%d FAIL=%d',passes+failures,passes,failures))
if failures>0 then os.exit(1) end
